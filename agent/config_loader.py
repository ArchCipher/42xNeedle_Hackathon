"""Load agent/config.yaml without extra dependencies."""

from __future__ import annotations

import os
import shutil
import sys
from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"
ROOT = Path(__file__).resolve().parent.parent


def python_launcher() -> str:
    """Portable Python command (Windows: py -3, else current interpreter)."""
    if os.getenv("AGENT_PYTHON"):
        return os.environ["AGENT_PYTHON"].strip()
    exe = sys.executable
    if exe:
        return exe
    if shutil.which("python3"):
        return "python3"
    if sys.platform == "win32" and shutil.which("py"):
        return "py -3"
    return "python3"


def default_public_test_command() -> str:
    py = python_launcher()
    knit = f'"{py}" knit.py' if " " in py else f"{py} knit.py"
    official = ROOT / "secret_spec" / "test_runner" / "run_tests.py"
    if official.is_file():
        return f'"{py}" "{official}" --program "{knit}" --suite public'
    team_runner = ROOT / "run_tests.py"
    if team_runner.is_file():
        return f"{py} run_tests.py" if " " not in py else f'"{py}" run_tests.py'
    return f"{knit} compile examples/hello.knit 2>&1"


def normalize_test_command(command: str) -> str:
    py = python_launcher()
    if "python3" in command:
        return command.replace("python3", py)
    return command


def flexible_verify_command() -> str:
    """Default check for flexible mode: knit.py must at least compile."""
    if os.getenv("AGENT_VERIFY_COMMAND"):
        return normalize_test_command(os.environ["AGENT_VERIFY_COMMAND"].strip())
    py = python_launcher()
    return normalize_test_command(f"{py} -m py_compile knit.py")


def apply_task_mode(data: dict[str, Any]) -> dict[str, Any]:
    mode = str(data.get("task_mode", "hackathon")).strip().lower()
    if os.getenv("AGENT_MODE"):
        mode = os.environ["AGENT_MODE"].strip().lower()
    data["task_mode"] = mode
    if mode == "flexible":
        custom = data.get("flexible_verify_command")
        if custom:
            data["public_test_command"] = normalize_test_command(str(custom))
        else:
            data["public_test_command"] = flexible_verify_command()
    return data


def load_config() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "primary_model": "qwen2.5-coder:7b",
        "provider": "Ollama",
        "ollama_base_url": "http://127.0.0.1:11434",
        "max_iterations": 40,
        "max_tool_rounds_per_iteration": 12,
        "request_timeout_seconds": 900,
        "public_test_command": default_public_test_command(),
        "llm_setup": False,
        "diagnose_on_failure": False,
        "task_mode": "hackathon",
    }
    if not CONFIG_PATH.exists():
        return apply_task_mode(defaults)

    data = dict(defaults)
    for raw in CONFIG_PATH.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        key, value = key.strip(), value.strip()
        if not value:
            continue
        if value.isdigit():
            data[key] = int(value)
        elif value.lower() in ("true", "false"):
            data[key] = value.lower() == "true"
        else:
            data[key] = value
    data["public_test_command"] = normalize_test_command(str(data["public_test_command"]))
    return apply_task_mode(data)
