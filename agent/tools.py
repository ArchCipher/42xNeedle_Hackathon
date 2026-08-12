"""Agent tools: bash, files, tests. All paths stay inside the project root."""

from __future__ import annotations

import ast
import os
import shlex
import subprocess
from pathlib import Path
from typing import Any

from codeshield_gate import scan_python_before_write

ROOT = Path(__file__).resolve().parent.parent

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "bash",
            "description": "Run a shell command in the project root.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a UTF-8 text file relative to the project root.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or overwrite a UTF-8 text file relative to the project root.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_tests",
            "description": "Run the configured public test command.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]


def _resolve_path(rel: str) -> Path:
    p = (ROOT / rel).resolve()
    if not str(p).startswith(str(ROOT.resolve())):
        raise ValueError(f"path escapes project root: {rel}")
    return p


def scrub_malloc_env(env: dict[str, str] | None = None) -> dict[str, str]:
    """Remove macOS malloc debug vars that spam MallocStackLogging on child Python."""
    base = dict(env if env is not None else os.environ)
    for key in list(base):
        if "malloc" in key.lower():
            base.pop(key, None)
    return base


def filter_subprocess_noise(text: str) -> str:
    lines = [ln for ln in text.splitlines() if "MallocStackLogging" not in ln]
    return "\n".join(lines).strip()


def run_bash(command: str, timeout: int = 120) -> tuple[int, str]:
    cmd = command.strip()
    if cmd.endswith("2>&1"):
        cmd = cmd[:-4].strip()
    env = scrub_malloc_env()

    try:
        parts = shlex.split(cmd)
    except ValueError:
        parts = None

    if parts:
        proc = subprocess.run(
            parts,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    else:
        proc = subprocess.run(
            cmd,
            shell=True,
            cwd=ROOT,
            capture_output=True,
            text=True,
            timeout=timeout,
            env=env,
        )
    out = filter_subprocess_noise((proc.stdout or "") + (proc.stderr or ""))
    return proc.returncode, out


_PROTECTED_PREFIXES = ("agent/", "agent\\", "compiler_v2/", "compiler_v2\\", "agent_logs/")


def _check_write_allowed(rel: str) -> str | None:
    norm = rel.replace("\\", "/")
    for prefix in _PROTECTED_PREFIXES:
        if norm.startswith(prefix) or norm == prefix.rstrip("/"):
            return f"error: cannot write to protected path {rel}; edit knit.py and src/ only"
    return None


def execute_tool(name: str, inputs: dict[str, Any], *, public_test_command: str) -> str:
    if name == "bash":
        code, out = run_bash(inputs["command"])
        return f"exit={code}\n{out}"
    if name == "read_file":
        p = _resolve_path(inputs["path"])
        if not p.exists():
            return f"error: file not found: {inputs['path']}"
        return p.read_text(encoding="utf-8")
    if name == "write_file":
        rel = inputs["path"]
        blocked = _check_write_allowed(rel)
        if blocked:
            return blocked
        content = inputs["content"]
        norm = rel.replace("\\", "/")
        if norm.endswith(".py"):
            try:
                ast.parse(content, filename=rel)
            except SyntaxError as exc:
                return (
                    f"error: SYNTAX ERROR in {rel} — {exc}\n"
                    "file not written. Fix Python syntax and retry write_file."
                )
            allow, shield_msg = scan_python_before_write(rel, content)
            if not allow:
                return shield_msg
        else:
            shield_msg = ""
        p = _resolve_path(rel)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        hint = ""
        if norm.startswith("src/") or rel.endswith("knit.py"):
            hint = " | reminder: JSON to stdout only, errors to stderr, match spec schema"
        extra = shield_msg if norm.endswith(".py") else ""
        return f"wrote {len(content)} bytes to {rel}{hint}{extra}"
    if name == "run_tests":
        code, out = run_bash(public_test_command)
        return f"exit={code}\n{out}"
    return f"error: unknown tool {name}"


def tools_as_ollama_json() -> list[dict[str, Any]]:
    return TOOL_SCHEMAS
