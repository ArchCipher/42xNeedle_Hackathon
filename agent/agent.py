#!/usr/bin/env python3
"""Main agent loop — free local Ollama only (no paid LLM APIs)."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Any

try:
    from dotenv import load_dotenv
except ImportError:

    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config_loader import load_config  # noqa: E402
from logger import AgentLogger  # noqa: E402
from ollama_client import OllamaClient, OllamaError, parse_assistant_response  # noqa: E402
from tools import ROOT, execute_tool, run_bash, scrub_malloc_env, tools_as_ollama_json  # noqa: E402

scrub_malloc_env()  # apply to current process before any subprocess

LOG = AgentLogger()
VERBOSE = True  # print human-readable progress to the terminal


def _out(msg: str = "") -> None:
    if VERBOSE:
        print(msg, flush=True)


def _out_section(title: str) -> None:
    if VERBOSE:
        print(f"\n--- {title} ---", flush=True)


def _preview(text: str, max_lines: int = 12, max_chars: int = 800) -> str:
    lines = text.splitlines()
    chunk = "\n".join(lines[:max_lines])
    if len(lines) > max_lines:
        chunk += f"\n... ({len(lines)} lines total)"
    if len(chunk) > max_chars:
        chunk = chunk[:max_chars] + "..."
    return chunk


def _format_tool_summary(name: str, inputs: dict[str, Any], result: str) -> str:
    if name == "read_file":
        path = inputs.get("path", "?")
        if result.startswith("error:"):
            return f"read_file {path} -> {result}"
        return f"read_file {path} -> ok ({len(result)} chars)\n{_preview(result)}"
    if name == "write_file":
        path = inputs.get("path", "?")
        return f"write_file {path} -> {result}"
    if name == "bash":
        cmd = inputs.get("command", "")
        return f"bash: {cmd}\n{_preview(result)}"
    if name == "run_tests":
        return f"run_tests ->\n{_preview(result)}"
    return f"{name} -> {_preview(result)}"
MANIFEST = ROOT / "agent_manifest.json"
SPEC_PATH = ROOT / "secret_spec" / "SECRET_SPEC.md"
PENDING_PROMPT_PATH = ROOT / "agent_logs" / "pending_prompt.txt"
PLAN_PATH = ROOT / "agent_logs" / "plan.md"
SPEC_SUMMARY_PATH = ROOT / "agent_logs" / "spec_summary.md"
STRATEGY_PATH = Path(__file__).resolve().parent / "strategy.md"

SCORE_RE = re.compile(r"(\d+)\s*/\s*(\d+)")
CATEGORY_RE = re.compile(
    r"([a-z][a-z0-9_]*)\s*:\s*(\d+)\s*/\s*(\d+)",
    re.IGNORECASE,
)

DEFAULT_AGENT_TASK_HACKATHON = (
    "Implement knit.py compile and src/ per secret_spec/SECRET_SPEC.md and agent_logs/plan.md. "
    "Priority: CLI + exit codes, JSON on stdout only, row_expansion, invalid input, edge cases. "
    "Use run_tests after each meaningful change."
)

DEFAULT_AGENT_TASK_FLEXIBLE = (
    "Implement the operator's application entirely in knit.py (use src/ for helpers). "
    "knit.py is the only user-facing program. Verify with bash (python knit.py ...)."
)

SYSTEM_PROMPT = """You are an autonomous coding agent for the 42 x Needle Hackathon hidden task.

## Goal
Build the submission CLI: `knit.py compile <input_file>` implemented in `src/`, matching
secret_spec/SECRET_SPEC.md exactly. Likely a data-transformation CLI: read structured input,
expand rows, emit strict JSON on stdout, correct exit codes.

## Mandatory first steps
1. read_file secret_spec/SECRET_SPEC.md
2. read_file agent/strategy.md
3. Log mentally: CLI args, input format, output JSON schema (every key/type), row_expansion rules,
   invalid input → exit code, stdout vs stderr rules.

## Build order (do not skip)
1. CLI wiring in knit.py → src/compile.py
2. UTF-8 input reader + empty file handling
3. Output JSON schema (exact key names from spec)
4. row_expansion (highest score category)
5. invalid_schema / bad input → exit 1, stderr only
6. Edge cases (nulls, special chars, duplicates)

## Discipline (score killers)
- stdout: ONLY the final JSON document (one line or pretty per spec). NO debug prints.
- stderr: all errors and diagnostics
- exit 0 = success, non-zero = failure (unless spec defines other codes)
- Match JSON field names and types exactly

## Tools
bash, read_file, write_file, run_tests — small targeted edits; run_tests after each fix.

## Tool call format (required if native tools fail)
<tool_call>
{"name": "read_file", "input": {"path": "secret_spec/SECRET_SPEC.md"}}
</tool_call>

## Do NOT edit
agent/, compiler_v2/, agent_logs/

When tests pass and spec is satisfied, reply with a short summary and stop calling tools.
"""

BUILD_CHECKLIST = """
SPEC CHECKLIST (complete before coding):
  [ ] CLI command and arguments
  [ ] Input format (CSV/JSON/text, encoding)
  [ ] Output JSON schema — all keys and types
  [ ] row_expansion definition in this spec
  [ ] Invalid input -> exit code
  [ ] Edge cases listed in spec
  [ ] stdout vs stderr rules
IMPLEMENTATION ORDER: CLI -> reader -> JSON schema -> row_expansion -> invalid handler -> edges
"""

PHASE_SETUP_SYSTEM = """You are the setup planner for a hackathon coding agent.
Read the specification excerpt and operator task. Produce ONE markdown document with:
## Spec summary (CLI, input, output JSON schema, row_expansion, exit codes, stdout/stderr)
## Implementation plan (numbered steps, files under src/ and knit.py only)
Keep it concise (under 80 lines). No code. No tool calls."""

PHASE_DIAGNOSE_SYSTEM = """You are the failure analyst for a hackathon coding agent.
Given test failures and the current plan, diagnose ONLY. Do NOT write code. Do NOT call tools.
Output markdown with:
## Root cause (one short paragraph)
## Fix first (top 3 file-level actions with paths)
## Verify next (what should change in test output)
Focus on knit.py and src/ only."""

IMPLEMENT_SYSTEM_PROMPT = """You are the implementer for the 42 x Needle Hackathon.

Follow agent_logs/plan.md and agent_logs/spec_summary.md. Edit only knit.py and src/.
Use tools: read_file, write_file, bash, run_tests (runs the configured public test command).

Rules:
- stdout: ONLY spec-compliant JSON on success
- stderr: errors and diagnostics only
- Small targeted edits; call run_tests after meaningful changes
- Do NOT edit agent/, compiler_v2/, agent_logs/

When stuck, re-read secret_spec/SECRET_SPEC.md with read_file.
Stop calling tools when you need the outer loop to run full public tests again."""

IMPLEMENT_SYSTEM_FLEXIBLE = """You are an autonomous coding agent. The operator's task defines the product.

## Entry point (required)
`knit.py` is the ONLY program users run (e.g. `python3 knit.py ...`).
Implement the operator's app there — calculator, calendar, task manager, etc.
Put helpers in `src/`. You MAY replace the current compile/compile-v2 CLI if the task needs a different interface.

## Workflow
1. read_file agent_logs/plan.md
2. write_file / edit knit.py and src/
3. bash — run `python3 knit.py ...` with real inputs to verify behavior
4. run_tests — runs the configured verify command (must pass for the loop to stop)

## Tool calls (required)
Use native tool calls OR <tool_call> JSON. Do NOT only print ```json {"name": ...} ``` without invoking tools.

## Rules
- Small steps; re-run bash smoke tests after each change
- Do NOT edit agent/, compiler_v2/, agent_logs/
- When knit.py compiles and bash smoke tests match the task, stop calling tools"""


def _is_flexible_mode(config: dict[str, Any]) -> bool:
    return str(config.get("task_mode", "hackathon")).lower() == "flexible"


def _implement_system_prompt(config: dict[str, Any]) -> str:
    return IMPLEMENT_SYSTEM_FLEXIBLE if _is_flexible_mode(config) else IMPLEMENT_SYSTEM_PROMPT


def _default_task(config: dict[str, Any]) -> str:
    if _is_flexible_mode(config):
        return DEFAULT_AGENT_TASK_FLEXIBLE
    return DEFAULT_AGENT_TASK_HACKATHON


def _reject_paid_api_env() -> None:
    for key in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "OPENROUTER_API_KEY"):
        if os.getenv(key):
            raise OllamaError(
                f"{key} is set. This agent uses free Ollama only. Unset it or use a clean shell."
            )


def _load_spec_excerpt(max_chars: int = 12000) -> str:
    if not SPEC_PATH.exists():
        return "(secret_spec/SECRET_SPEC.md not present yet.)"
    text = SPEC_PATH.read_text(encoding="utf-8")
    return text if len(text) <= max_chars else text[:max_chars] + "\n...(truncated)..."


def _log_spec_status() -> None:
    if SPEC_PATH.is_file():
        size = SPEC_PATH.stat().st_size
        LOG.decision(
            "Spec loaded from secret_spec/SECRET_SPEC.md",
            evidence=f"{size} bytes at {SPEC_PATH.relative_to(ROOT)}",
            next_action="use read_file for full spec when implementing",
        )
    else:
        LOG.decision(
            "Spec file missing",
            evidence=str(SPEC_PATH.relative_to(ROOT)),
            next_action="copy SECRET_SPEC.md into secret_spec/ from the event repo",
        )


def _load_strategy_excerpt(max_chars: int = 6000) -> str:
    if not STRATEGY_PATH.is_file():
        return "(agent/strategy.md missing)"
    text = STRATEGY_PATH.read_text(encoding="utf-8")
    return text if len(text) <= max_chars else text[:max_chars] + "\n...(truncated)..."


def _write_artifact(path: Path, content: str, label: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content.strip() + "\n", encoding="utf-8")
    LOG.decision(f"Wrote {label}", evidence=str(path.relative_to(ROOT)))


def _read_artifact(path: Path, max_chars: int = 8000) -> str:
    if not path.is_file():
        return f"({path.name} not written yet)"
    text = path.read_text(encoding="utf-8")
    return text if len(text) <= max_chars else text[:max_chars] + "\n...(truncated)..."


def _chat_no_tools(
    client: OllamaClient,
    system: str,
    user: str,
    *,
    num_predict: int = 1024,
    retries: int = 2,
) -> str:
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": system},
        {"role": "user", "content": user},
    ]
    last_err: OllamaError | None = None
    for attempt in range(1, retries + 1):
        _out(
            f"  Waiting for Ollama (text-only, attempt {attempt}/{retries}, "
            f"timeout {client.timeout}s)..."
        )
        try:
            resp = client.chat(messages, tools=None, num_predict=num_predict)
            text, _ = parse_assistant_response(resp.get("message", {}))
            return text.strip()
        except OllamaError as exc:
            last_err = exc
            LOG.error(f"Ollama text phase attempt {attempt}", details=str(exc))
            if attempt >= retries:
                raise
    raise last_err or OllamaError("Ollama text phase failed")


def _phase_diagnose(
    client: OllamaClient,
    code: int,
    test_output: str,
    *,
    iteration: int,
) -> str:
    _out_section(f"Phase 5 — Diagnose failures (iteration {iteration})")
    LOG.decision("Phase 5 start", next_action="failure analysis (no tools)")
    user = (
        f"Test exit code: {code}\n\n"
        f"Test output:\n{test_output[:5000]}\n\n"
        f"Current plan:\n{_read_artifact(PLAN_PATH, 6000)}\n\n"
        f"Spec summary:\n{_read_artifact(SPEC_SUMMARY_PATH, 4000)}"
    )
    analysis = _chat_no_tools(client, PHASE_DIAGNOSE_SYSTEM, user)
    LOG.decision(
        f"Phase 5 complete (iter {iteration})",
        reason=analysis[:500],
        next_action="Phase 3 implement fixes",
    )
    _out(_preview(analysis, max_lines=12))
    return analysis


def _write_template_setup(task: str, *, reason: str) -> None:
    _out_section("Setup — template (no LLM)")
    LOG.decision("Template setup", reason=reason, next_action="implement loop")
    spec_note = (
        _load_spec_excerpt(8000)
        if SPEC_PATH.is_file()
        else "(secret_spec/SECRET_SPEC.md not present — copy from event repo at 20:00.)"
    )
    summary = (
        f"# Spec summary (template)\n\n"
        f"Setup mode: {reason}\n\n"
        f"Operator task:\n{task}\n\n"
        f"Specification excerpt:\n{spec_note}\n\n"
        f"{BUILD_CHECKLIST}\n"
    )
    if SPEC_PATH.is_file():
        steps = (
            "1. read_file secret_spec/SECRET_SPEC.md\n"
            "2. Implement knit.py compile in src/ per spec\n"
            "3. run_tests after each meaningful change\n"
        )
    else:
        steps = (
            "1. Design CLI or UX for knit.py matching the operator task\n"
            "2. Implement logic in knit.py and src/\n"
            "3. bash: python3 knit.py <smoke args> until behavior matches task\n"
            "4. run_tests (py_compile) after each meaningful change\n"
        )
    plan = (
        f"# Implementation plan (template)\n\n"
        f"## Operator task\n{task}\n\n"
        f"## knit.py is the app\n"
        f"All user-facing behavior lives in knit.py (helpers in src/).\n\n"
        f"## Steps\n{steps}\n"
        f"{BUILD_CHECKLIST if SPEC_PATH.is_file() else ''}\n"
    )
    _write_artifact(SPEC_SUMMARY_PATH, summary, "spec_summary.md")
    _write_artifact(PLAN_PATH, plan, "plan.md")
    _out("Wrote agent_logs/spec_summary.md and agent_logs/plan.md (instant).")


def _phase_setup_combined(client: OllamaClient, task: str) -> None:
    _out_section("Setup — LLM read + plan (one call)")
    LOG.decision("Combined LLM setup", next_action="single Ollama call")
    user = (
        f"Operator task:\n{task}\n\n"
        f"Strategy excerpt:\n{_load_strategy_excerpt(2000)}\n\n"
        f"Specification:\n{_load_spec_excerpt(10000)}\n\n"
        f"{BUILD_CHECKLIST}"
    )
    combined = _chat_no_tools(client, PHASE_SETUP_SYSTEM, user, num_predict=1200)
    _write_artifact(SPEC_SUMMARY_PATH, combined, "spec_summary.md")
    _write_artifact(PLAN_PATH, combined, "plan.md")
    _out(_preview(combined, max_lines=14))


def _run_setup_phases(
    client: OllamaClient,
    task: str,
    config: dict[str, Any],
    *,
    force: bool,
    llm_setup: bool,
) -> None:
    if not force and PLAN_PATH.is_file() and SPEC_SUMMARY_PATH.is_file():
        if PLAN_PATH.stat().st_size > 80 and SPEC_SUMMARY_PATH.stat().st_size > 80:
            LOG.decision(
                "Skipping setup",
                evidence="plan.md and spec_summary.md exist",
                next_action="implement loop (--force-setup to refresh)",
            )
            _out_section("Setup skipped (existing plan.md + spec_summary.md)")
            return

    use_llm = llm_setup and SPEC_PATH.is_file()
    if not use_llm:
        why = "no spec file" if not SPEC_PATH.is_file() else "llm_setup disabled (use --llm-setup)"
        _write_template_setup(task, reason=why)
        return
    _phase_setup_combined(client, task)


def _format_pytest_result(result: dict[str, Any]) -> str:
    total = int(result.get("total", 0))
    passed = int(result.get("passed", 0))
    failed = int(result.get("failed", 0))
    lines = [f"pytest score: {passed}/{total} passed, {failed} failed"]
    for item in result.get("failures", []):
        lines.append(f"FAILED {item.get('test', '?')}")
        detail = str(item.get("detail", "")).strip()
        if detail:
            lines.append(f"  {detail[:400]}")
    return "\n".join(lines)


def _uses_team_run_tests(command: str) -> bool:
    c = command.strip().lower()
    return "run_tests.py" in c and "--program" not in c and "--suite" not in c


def _parse_test_score(output: str) -> str:
    match = SCORE_RE.search(output)
    if match:
        return f"{match.group(1)}/{match.group(2)}"
    return "see output"


def _parse_failure_categories(output: str) -> str:
    matches = CATEGORY_RE.findall(output)
    if not matches:
        return ""
    return ", ".join(f"{name}: {got}/{total}" for name, got, total in matches)


def _priority_failures(output: str) -> list[str]:
    """Categories to fix first (zero score or known high-value names)."""
    priority_names = (
        "row_expansion",
        "invalid_schema",
        "invalid output schema",
        "basic_cli",
    )
    found: list[str] = []
    lower = output.lower()
    for name in priority_names:
        if name.replace(" ", "_") in lower or name in lower:
            found.append(name)
    for name, got, total in CATEGORY_RE.findall(output):
        if int(got) == 0 and int(total) > 0:
            label = f"{name} ({got}/{total})"
            if label not in found:
                found.append(label)
    return found[:5]


def _build_repair_message(code: int, out: str, diagnosis: str = "") -> str:
    categories = _parse_failure_categories(out)
    priorities = _priority_failures(out)
    score = _parse_test_score(out)
    lines = [
        f"Tests failed (exit={code}, score={score}).",
        "Follow agent_logs/plan.md. Fix with small edits in knit.py and src/ only.",
        "stdout must be JSON only; errors on stderr.",
    ]
    if diagnosis:
        lines.append(f"Failure analysis:\n{diagnosis[:2500]}")
    if priorities:
        lines.append(f"Fix FIRST: {', '.join(priorities)}")
    if categories:
        lines.append(f"Categories: {categories}")
    lines.append(f"Output excerpt:\n{out[:3500]}")
    return "\n".join(lines)


def _sync_manifest(config: dict[str, Any]) -> None:
    if not MANIFEST.exists():
        return
    data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    data["primary_model"] = config["primary_model"]
    data["provider"] = config["provider"]
    data["runtime_or_tool"] = "custom Python agent (agent/agent.py) + Ollama"
    data["paid_frontier_models_used_after_spec_release"] = False
    data["notes"] = "Agent uses Ollama local inference only; no paid LLM API calls."
    MANIFEST.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def run_public_tests(command: str) -> tuple[int, str]:
    if _uses_team_run_tests(command):
        try:
            sys.path.insert(0, str(ROOT))
            from run_tests import run_tests as run_pytest_suite  # noqa: WPS433

            result = run_pytest_suite()
            out = _format_pytest_result(result)
            total = int(result.get("total", 0))
            failed = int(result.get("failed", 0))
            code = 0 if total > 0 and failed == 0 else 1
            LOG.command(command, exit_code=code, output=out)
        except Exception as exc:
            code, out = 1, f"run_tests import failed: {exc}"
            LOG.error("Public tests runner failed", details=str(exc))
    else:
        code, out = run_bash(command)
    score = _parse_test_score(out)
    categories = _parse_failure_categories(out)
    priorities = _priority_failures(out)
    LOG.command(command, exit_code=code, output=out)
    LOG.test_run(
        command,
        exit_code=code,
        score=score,
        failures=categories or out[:800] if code != 0 else "",
        notes=(
            f"fix first: {', '.join(priorities)}"
            if priorities
            else ("parsed score" if score != "see output" else "check after iteration")
        ),
    )
    if priorities:
        LOG.decision(
            "Test failure priorities",
            evidence=", ".join(priorities),
            next_action="patch row_expansion / invalid_schema before other changes",
        )
    return code, out


def _tool_rounds(
    client: OllamaClient,
    messages: list[dict[str, Any]],
    config: dict[str, Any],
    iteration: int,
) -> str:
    max_rounds = int(config["max_tool_rounds_per_iteration"])
    last_text = ""
    test_cmd = str(config["public_test_command"])

    for round_i in range(1, max_rounds + 1):
        _out(f"  [round {round_i}] Waiting for Ollama (can take minutes on CPU)...")
        resp = client.chat(messages, tools=tools_as_ollama_json())
        msg = resp.get("message", {})
        text, tool_calls = parse_assistant_response(msg)
        last_text = text or last_text

        if text:
            LOG.decision(
                f"Model reply (iter {iteration}, round {round_i})",
                reason=text[:600],
            )
            _out(f"  [round {round_i}] Model says:")
            _out(_preview(text, max_lines=8))

        if not tool_calls:
            _out(f"  [round {round_i}] No more tools requested.")
            return last_text

        _out(f"  [round {round_i}] Running {len(tool_calls)} tool(s)...")
        messages.append({"role": "assistant", "content": text, "tool_calls": msg.get("tool_calls")})
        for tc in tool_calls:
            name, inputs = tc["name"], tc["input"]
            LOG.command(f"{name}({json.dumps(inputs)[:200]})", run_by="agent")
            try:
                result = execute_tool(name, inputs, public_test_command=test_cmd)
            except Exception as exc:
                result = f"error: {exc}"
                LOG.error(f"Tool {name} failed", details=str(exc))
            LOG.command(f"{name} result", exit_code=0, output=result[:1500])
            messages.append({"role": "tool", "content": result})
            _out(_format_tool_summary(name, inputs, result))

    LOG.error("Tool round cap", details=f"max={max_rounds}")
    _out(f"  Stopped: hit max tool rounds ({max_rounds}).")
    return last_text


def _consume_pending_prompt() -> str | None:
    if not PENDING_PROMPT_PATH.is_file():
        return None
    text = PENDING_PROMPT_PATH.read_text(encoding="utf-8").strip()
    if not text:
        return None
    if text.upper().startswith("STOP:"):
        LOG.decision("Operator stop requested via pending_prompt.txt", evidence=text[:200])
    else:
        LOG.user_prompt(text, context="pending_prompt.txt from monitor UI")
    PENDING_PROMPT_PATH.write_text("", encoding="utf-8")
    return text


def _run_iteration(
    client: OllamaClient,
    messages: list[dict[str, Any]],
    config: dict[str, Any],
    iteration: int,
) -> tuple[bool, list[dict[str, Any]]]:
    pending = _consume_pending_prompt()
    if pending:
        messages.append(
            {"role": "user", "content": f"Operator instruction (pending_prompt.txt):\n{pending}"}
        )
    LOG.decision(
        f"Start iteration {iteration}",
        next_action="implement (tools) -> test -> repair if fail",
    )
    _out_section(f"Iteration {iteration} — Phase 3 implement")
    _tool_rounds(client, messages, config, iteration)

    test_cmd = str(config["public_test_command"])
    _out_section(f"Iteration {iteration} — Phase 4 test")
    _out(f"Command: {test_cmd}")
    code, out = run_public_tests(test_cmd)
    score = _parse_test_score(out)
    if code == 0:
        LOG.decision("Public tests passed", reason=out[:300])
        _out(f"RESULT: PASSED (exit 0, score {score})")
        _out(_preview(out, max_lines=6))
        return True, messages

    LOG.error(
        "Public tests failed",
        details=out[:2000],
        recovery="Phase 5 diagnose then implement fixes",
    )
    _out(f"RESULT: FAILED (exit {code}, score {score})")
    _out(_preview(out, max_lines=10))
    diagnosis = ""
    if config.get("diagnose_on_failure"):
        diagnosis = _phase_diagnose(client, code, out, iteration=iteration)
    else:
        LOG.decision(
            "Repair from test output (no LLM diagnose)",
            next_action="implement fixes",
        )
    messages.append({"role": "user", "content": _build_repair_message(code, out, diagnosis)})
    return False, messages


def run_agent(
    task: str,
    max_iterations: int | None = None,
    *,
    force_setup: bool = False,
    skip_setup: bool = False,
    llm_setup: bool | None = None,
    diagnose_on_failure: bool | None = None,
    task_mode: str | None = None,
) -> None:
    load_dotenv(ROOT / ".env")
    _reject_paid_api_env()
    config = load_config()
    if task_mode:
        config["task_mode"] = task_mode
        from config_loader import apply_task_mode  # noqa: E402

        config = apply_task_mode(config)
    if os.getenv("OLLAMA_BASE_URL"):
        config["ollama_base_url"] = os.environ["OLLAMA_BASE_URL"]
    if os.getenv("AGENT_MODEL"):
        config["primary_model"] = os.environ["AGENT_MODEL"]
    if llm_setup is not None:
        config["llm_setup"] = llm_setup
    if diagnose_on_failure is not None:
        config["diagnose_on_failure"] = diagnose_on_failure

    limit = max_iterations or int(config["max_iterations"])
    client = OllamaClient(
        config["ollama_base_url"],
        config["primary_model"],
        timeout=int(config["request_timeout_seconds"]),
    )

    LOG.user_prompt(task, context=f"model={config['primary_model']} (Ollama, free)")
    LOG.decision("Agent run started", reason=task, next_action=f"max {limit} iterations")
    LOG.decision(
        "Test command configured",
        evidence=str(config["public_test_command"]),
    )
    LOG.decision(
        "Task mode",
        evidence=str(config.get("task_mode", "hackathon")),
        next_action="flexible = any app in knit.py; hackathon = compiler + pytest",
    )
    _log_spec_status()

    _out_section("SPARK agent run")
    _out(f"Mode: {config.get('task_mode', 'hackathon')}")
    _out(f"Model: {config['primary_model']} @ {config['ollama_base_url']}")
    _out(f"Iterations: {limit}")
    _out(f"Task: {task}")
    _out(f"Tests: {config['public_test_command']}")
    _out(f"Logs: {ROOT / 'agent_logs'}/")
    _out("Full detail is also appended to agent_logs/*.log")

    client.ensure_model()
    _sync_manifest(config)

    _out("Warming up model (short request)...")
    try:
        client.warmup()
        _out("Model warm-up OK.")
    except OllamaError as exc:
        LOG.error("Model warm-up failed", details=str(exc))
        _out(f"Warm-up failed (continuing anyway): {exc}")

    if not skip_setup:
        _run_setup_phases(
            client,
            task,
            config,
            force=force_setup,
            llm_setup=bool(config.get("llm_setup")),
        )
    else:
        LOG.decision("Setup skipped by flag", next_action="implement loop")

    impl_hint = (
        "Implement the operator's app in knit.py. Use bash to run python3 knit.py with real inputs."
        if _is_flexible_mode(config)
        else "Implement knit.py compile per plan. Call run_tests after meaningful edits."
    )
    messages: list[dict[str, Any]] = [
        {"role": "system", "content": _implement_system_prompt(config)},
        {
            "role": "user",
            "content": (
                f"Task:\n{task}\n\n"
                f"Spec summary (agent_logs/spec_summary.md):\n"
                f"{_read_artifact(SPEC_SUMMARY_PATH)}\n\n"
                f"Implementation plan (agent_logs/plan.md):\n"
                f"{_read_artifact(PLAN_PATH)}\n\n"
                f"Begin implement phase: {impl_hint}"
            ),
        },
    ]

    crashes = 0
    passed = False
    for i in range(1, limit + 1):
        try:
            stop, messages = _run_iteration(client, messages, config, i)
            crashes = 0
            if stop:
                passed = True
                LOG.decision("Run finished", reason="tests passed")
                break
        except OllamaError as exc:
            crashes += 1
            LOG.error("Iteration failed", details=str(exc))
            _out(f"\nERROR: Ollama failed: {exc}")
            if crashes >= 3:
                raise
        except Exception as exc:
            LOG.error("Agent crash", details=str(exc))
            _out(f"\nERROR: {exc}")
            raise
    else:
        LOG.error("Max iterations reached", details=f"limit={limit}")

    _out_section("Run complete")
    if passed:
        _out("Done: public tests passed. See agent_logs/ for full history.")
    else:
        _out("Done: finished without passing all tests. Check errors.log and test_runs.log.")
    _out(f"Tail live logs: tail -f agent_logs/decisions.log")


def cmd_plan(_args: argparse.Namespace) -> None:
    """Print spec checklist and log planning decisions (no Ollama)."""
    _reject_paid_api_env()
    config = load_config()
    _log_spec_status()
    LOG.decision("Planning mode", next_action="read spec then implement in src/")
    print(BUILD_CHECKLIST)
    print("\n--- strategy excerpt ---\n")
    print(_load_strategy_excerpt(2000))
    print("\n--- spec excerpt ---\n")
    print(_load_spec_excerpt(2000))
    print(f"\nTest command: {config['public_test_command']}")
    LOG.decision("Plan printed", evidence="agent/strategy.md + spec excerpt")


def cmd_doctor(_args: argparse.Namespace) -> None:
    _reject_paid_api_env()
    config = load_config()
    print("Setup check (Ollama only)\n")
    client = OllamaClient(config["ollama_base_url"], config["primary_model"], timeout=30)
    try:
        client.health()
        print(f"OK: Ollama at {config['ollama_base_url']}")
        client.ensure_model()
        print(f"OK: model {config['primary_model']}")
    except OllamaError as exc:
        print(f"FAIL: {exc}")
        sys.exit(1)
    LOG.decision("doctor smoke test")
    print(f"OK: test command -> {config['public_test_command']}")
    print("OK: logging works")


def cmd_log_human(args: argparse.Namespace) -> None:
    LOG.human_intervention(
        args.type,
        what=args.what,
        why=args.why or "",
        files_affected=args.files or "",
        touched_final_code=args.touched_code,
        notes=args.notes or "",
    )
    print("Logged to agent_logs/human_interventions.log")


def cmd_log_prompt(args: argparse.Namespace) -> None:
    LOG.user_prompt(args.prompt, context=args.context or "", expected_action=args.expected or "")
    print("Logged to agent_logs/prompts.log")


def main() -> None:
    parser = argparse.ArgumentParser(description="42 x Needle agent (Ollama only)")
    sub = parser.add_subparsers(dest="cmd", required=True)
    sub.add_parser("doctor", help="Check Ollama setup")
    sub.add_parser("plan", help="Print spec checklist and strategy (no model call)")
    run_p = sub.add_parser("run", help="Run agent loop")
    run_p.add_argument("task", nargs="?", default=os.getenv("AGENT_TASK", ""))
    run_p.add_argument("--max-iterations", type=int, default=None)
    once_p = sub.add_parser("run-once", help="Run a single agent iteration (smoke test)")
    once_p.add_argument("task", nargs="?", default=os.getenv("AGENT_TASK", ""))
    for p in (run_p, once_p):
        p.add_argument(
            "-q",
            "--quiet",
            action="store_true",
            help="Only write to agent_logs/, minimal terminal output",
        )
        p.add_argument(
            "--force-setup",
            action="store_true",
            help="Re-run Phase 1 (read spec) and Phase 2 (plan) even if plan.md exists",
        )
        p.add_argument(
            "--skip-setup",
            action="store_true",
            help="Skip setup; go straight to implement/test loop",
        )
        p.add_argument(
            "--llm-setup",
            action="store_true",
            help="Use one Ollama call for spec+plan when SECRET_SPEC.md exists (slow on CPU)",
        )
        p.add_argument(
            "--diagnose",
            action="store_true",
            help="After failed tests, add an LLM failure-analysis phase (extra Ollama call)",
        )
        p.add_argument(
            "--mode",
            choices=("hackathon", "flexible"),
            default=None,
            help="hackathon = Knit compiler tests; flexible = any app implemented in knit.py",
        )
    human_p = sub.add_parser("log-human")
    human_p.add_argument("--type", required=True)
    human_p.add_argument("--what", required=True)
    human_p.add_argument("--why", default="")
    human_p.add_argument("--files", default="")
    human_p.add_argument("--touched-code", action="store_true")
    human_p.add_argument("--notes", default="")
    prompt_p = sub.add_parser("log-prompt")
    prompt_p.add_argument("prompt")
    prompt_p.add_argument("--context", default="")
    prompt_p.add_argument("--expected", default="")

    args = parser.parse_args()
    if args.cmd == "doctor":
        cmd_doctor(args)
    elif args.cmd == "plan":
        cmd_plan(args)
    elif args.cmd in ("run", "run-once"):
        global VERBOSE
        VERBOSE = not getattr(args, "quiet", False)
        cfg = load_config()
        if args.mode:
            cfg["task_mode"] = args.mode
            from config_loader import apply_task_mode  # noqa: E402

            cfg = apply_task_mode(cfg)
        default_task = _default_task(cfg)
        task = args.task or os.getenv("AGENT_TASK", "").strip() or default_task
        if args.cmd == "run" and not (args.task or os.getenv("AGENT_TASK")):
            hint = "calculator in knit.py" if _is_flexible_mode(cfg) else "hidden-task compiler"
            entered = input(f"Task (Enter for default — {hint}): ").strip()
            task = entered or default_task
        max_iter = 1 if args.cmd == "run-once" else args.max_iterations
        run_agent(
            task,
            max_iter,
            force_setup=args.force_setup,
            skip_setup=args.skip_setup,
            llm_setup=args.llm_setup or bool(cfg.get("llm_setup")),
            diagnose_on_failure=args.diagnose or bool(cfg.get("diagnose_on_failure")),
            task_mode=args.mode,
        )
    elif args.cmd == "log-human":
        cmd_log_human(args)
    elif args.cmd == "log-prompt":
        cmd_log_prompt(args)


if __name__ == "__main__":
    main()
