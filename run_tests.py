#!/usr/bin/env python3
"""Test runner entry point.

Usage:
    python run_tests.py               # run all tests against dummy stub
    KNIT_TARGET=knit.py python run_tests.py   # run against real knit.py
"""

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent


def main() -> int:
    result = subprocess.run(
        [sys.executable, "-m", "pytest", str(ROOT / "tests"), "-v", *sys.argv[1:]],
        cwd=ROOT,
    )
    return result.returncode


if __name__ == "__main__":
    raise SystemExit(main())
