"""Load agent/config.yaml without extra dependencies."""

from __future__ import annotations

from pathlib import Path
from typing import Any

CONFIG_PATH = Path(__file__).resolve().parent / "config.yaml"


def load_config() -> dict[str, Any]:
    defaults: dict[str, Any] = {
        "primary_model": "qwen2.5-coder:7b",
        "provider": "Ollama",
        "ollama_base_url": "http://127.0.0.1:11434",
        "max_iterations": 40,
        "max_tool_rounds_per_iteration": 12,
        "request_timeout_seconds": 300,
        "public_test_command": "python3 knit.py compile examples/hello.knit 2>&1",
    }
    if not CONFIG_PATH.exists():
        return defaults

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
    return data
