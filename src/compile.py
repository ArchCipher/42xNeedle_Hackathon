"""Core compile logic — agent implements per secret_spec/SECRET_SPEC.md."""

from __future__ import annotations

import json
import sys

from src.io import is_empty_content, read_input_text


def compile_file(input_path: str) -> int:
    """
    Success: print spec-compliant JSON to stdout, return 0.
    Invalid: print diagnostics to stderr only, return 1.
    """
    try:
        raw = read_input_text(input_path)
    except FileNotFoundError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    if is_empty_content(raw):
        print("empty input", file=sys.stderr)
        return 1

    # TODO(agent): parse input, row expansion, emit exact JSON schema from spec.
    print("compile logic not implemented — read secret_spec/SECRET_SPEC.md", file=sys.stderr)
    return 1


def emit_json(payload: dict) -> None:
    """Write final result to stdout only (no extra lines)."""
    sys.stdout.write(json.dumps(payload, ensure_ascii=False) + "\n")
