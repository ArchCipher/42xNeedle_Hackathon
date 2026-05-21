"""Input/output helpers — extend per secret_spec/SECRET_SPEC.md."""

from __future__ import annotations

from pathlib import Path


def read_input_text(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"input file not found: {p}")
    return p.read_text(encoding="utf-8")


def is_empty_content(text: str) -> bool:
    return not text.strip()
