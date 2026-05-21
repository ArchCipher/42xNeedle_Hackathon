#!/usr/bin/env python3
"""Main agent loop for the 42 x Needle Hackathon.

All activity should go through AgentLogger so agent_logs/ stays submission-ready.
Extend _run_iteration() with your model + tools after the 19:45 checkpoint.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import sys
from pathlib import Path

try:
    from dotenv import load_dotenv
except ImportError:
    def load_dotenv(*_args: object, **_kwargs: object) -> bool:
        return False

sys.path.insert(0, str(Path(__file__).resolve().parent))
from logger import AgentLogger  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
LOG = AgentLogger()
MANIFEST = ROOT / "agent_manifest.json"
SPEC_PATH = ROOT / "secret_spec" / "SECRET_SPEC.md"


def run_bash(command: str, cwd: Path | None = None) -> tuple[int, str]:
    proc = subprocess.run(
        command,
        shell=True,
        cwd=cwd or ROOT,
        capture_output=True,
        text=True,
        timeout=120,
    )
    out = (proc.stdout or "") + (proc.stderr or "")
    return proc.returncode, out.strip()


def run_public_tests() -> tuple[int, str]:
    """Replace with the real public test command once released."""
    for cmd in (
        "python3 knit.py compile examples/hello.knit 2>&1",
        "pytest -q 2>&1",
    ):
        code, out = run_bash(cmd)
        LOG.command(cmd, exit_code=code, output=out)
        if code != 127:
            LOG.test_run(
                cmd,
                exit_code=code,
                score="unknown",
                failures=out[:500] if code != 0 else "",
                notes="public test runner placeholder",
            )
            return code, out
    return 1, "no test command found"


def _run_iteration(task: str, iteration: int) -> bool:
    """One plan-act-test cycle. Return True when the agent should stop."""
    LOG.decision(
        f"Start iteration {iteration}",
        reason="Main agent loop tick",
        next_action="Read spec, edit src/, run tests",
    )

    if SPEC_PATH.exists():
        spec = SPEC_PATH.read_text(encoding="utf-8")
        LOG.decision(
            "Loaded hidden spec",
            evidence=f"{SPEC_PATH} ({len(spec)} bytes)",
            next_action="Implement or patch compiler in src/",
        )
    else:
        LOG.decision(
            "No hidden spec yet",
            reason="secret_spec/SECRET_SPEC.md not present",
            next_action="Prepare agent + knit.py stub until 20:00 release",
        )

    code, out = run_public_tests()
    if code == 0:
        LOG.decision("Tests passed", reason=out[:200], next_action="Stop or refine")
        return True

    LOG.error(
        "Tests failed",
        details=out[:2000],
        recovery="Patch implementation and rerun",
    )
    return False


def run_agent(task: str, max_iterations: int = 50) -> None:
    load_dotenv(ROOT / ".env")
    LOG.user_prompt(
        task,
        context="Agent run started",
        expected_action="Implement compiler per spec; iterate on test failures",
    )
    LOG.decision(
        "Agent run started",
        reason=task,
        next_action=f"Up to {max_iterations} iterations",
    )

    for i in range(1, max_iterations + 1):
        try:
            if _run_iteration(task, i):
                LOG.decision("Run finished", reason="Stop condition met")
                break
        except Exception as exc:
            LOG.error("Agent crash", details=str(exc))
            raise
    else:
        LOG.error("Max iterations reached", details=f"limit={max_iterations}")


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
    parser = argparse.ArgumentParser(description="42 x Needle agent")
    sub = parser.add_subparsers(dest="cmd", required=True)

    run_p = sub.add_parser("run", help="Run the agent loop")
    run_p.add_argument("task", nargs="?", default=os.getenv("AGENT_TASK", ""))
    run_p.add_argument("--max-iterations", type=int, default=50)

    human_p = sub.add_parser("log-human", help="Log a human intervention")
    human_p.add_argument("--type", required=True, help="e.g. PROMPT_EDIT, AGENT_RESTART")
    human_p.add_argument("--what", required=True)
    human_p.add_argument("--why", default="")
    human_p.add_argument("--files", default="")
    human_p.add_argument("--touched-code", action="store_true")
    human_p.add_argument("--notes", default="")

    prompt_p = sub.add_parser("log-prompt", help="Log a user prompt to the agent")
    prompt_p.add_argument("prompt")
    prompt_p.add_argument("--context", default="")
    prompt_p.add_argument("--expected", default="")

    args = parser.parse_args()
    if args.cmd == "run":
        task = args.task or input("Task: ").strip()
        if not task:
            print("Provide a task string or set AGENT_TASK.", file=sys.stderr)
            sys.exit(1)
        run_agent(task, args.max_iterations)
    elif args.cmd == "log-human":
        cmd_log_human(args)
    elif args.cmd == "log-prompt":
        cmd_log_prompt(args)


if __name__ == "__main__":
    main()
