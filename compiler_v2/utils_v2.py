"""Shared helpers for compiler v2 (no imports from src/ or v1)."""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, is_dataclass
from pathlib import Path
from typing import Any

LOG = logging.getLogger("compiler_v2")


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="[compiler_v2] %(levelname)s: %(message)s",
    )


def read_source(path: str | Path) -> str:
    p = Path(path)
    if not p.is_file():
        raise FileNotFoundError(f"input file not found: {p}")
    return p.read_text(encoding="utf-8")


def default_output_path(input_path: str | Path) -> Path:
    p = Path(input_path)
    return p.with_suffix(p.suffix + ".out.json")


def serialize(obj: Any) -> Any:
    if is_dataclass(obj) and not isinstance(obj, type):
        return {k: serialize(v) for k, v in asdict(obj).items()}
    if isinstance(obj, list):
        return [serialize(x) for x in obj]
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, (str, int, float, bool)) or obj is None:
        return obj
    return str(obj)


def emit_json(payload: dict[str, Any], indent: int = 2) -> str:
    return json.dumps(serialize(payload), indent=indent, ensure_ascii=False) + "\n"
