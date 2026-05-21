"""Tests for knit.py CLI."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
KNIT = Path(os.environ.get("KNIT_TARGET", str(ROOT / "knit.py")))
HELLO = ROOT / "examples" / "hello.knit"


def run_knit(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(KNIT), *args],
        capture_output=True,
        text=True,
        cwd=ROOT,
    )


class TestKnitCli:
    def test_requires_subcommand(self) -> None:
        result = run_knit()
        assert result.returncode == 2
        assert "required: command" in result.stderr

    def test_compile_v2_hello_exits_zero(self) -> None:
        result = run_knit("compile-v2", str(HELLO))
        assert result.returncode == 0, f"stderr: {result.stderr}"

    def test_compile_v2_hello_stdout(self) -> None:
        result = run_knit("compile-v2", str(HELLO))
        assert "Hello Knit" in result.stdout, f"stdout: {result.stdout!r}"

    def test_compile_hello_not_implemented_yet(self) -> None:
        """v1 submission path — update when src/compile.py is complete."""
        result = run_knit("compile", str(HELLO))
        assert result.returncode == 1
        assert "not implemented" in result.stderr.lower()
