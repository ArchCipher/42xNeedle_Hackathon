"""Tests for the knit compiler.

Currently runs against tests/dummy_knit.py. When the real knit.py is ready,
update KNIT_TARGET in run_tests.py (or set KNIT_TARGET env var) to point at it.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent

# Swap to "knit.py" when the real implementation lands.
KNIT_TARGET = os.environ.get("KNIT_TARGET", str(ROOT / "tests" / "dummy_knit.py"))


def run_knit(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, KNIT_TARGET, *args],
        capture_output=True,
        text=True,
    )


class TestDummyStub:
    def test_exits_zero(self) -> None:
        result = run_knit()
        assert result.returncode == 0, f"Expected exit 0, got {result.returncode}\nstderr: {result.stderr}"

    def test_prints_hello(self) -> None:
        result = run_knit()
        assert "hello" in result.stdout, f"Expected 'hello' in stdout, got: {result.stdout!r}"
