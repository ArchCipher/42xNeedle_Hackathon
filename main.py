#!/usr/bin/env python3
"""CLI entrypoint — delegates v1 to knit.py, runs v2 in compiler_v2/."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def cmd_compile_v1(input_file: str) -> int:
    knit = ROOT / "knit.py"
    proc = subprocess.run(
        [sys.executable, str(knit), "compile", input_file],
        cwd=ROOT,
    )
    return proc.returncode


def cmd_compile_v2(input_file: str, output_file: str | None, verbose: bool) -> int:
    from compiler_v2.runner_v2 import compile_file

    return compile_file(input_file, output_file=output_file, verbose=verbose)


def main() -> int:
    parser = argparse.ArgumentParser(description="Knit compiler (v1 + v2)")
    sub = parser.add_subparsers(dest="command", required=True)

    compile_v1 = sub.add_parser("compile", help="Compile with v1 (knit.py)")
    compile_v1.add_argument("input_file")

    compile_v2 = sub.add_parser("compile-v2", help="Compile with v2 pipeline")
    compile_v2.add_argument("input_file")
    compile_v2.add_argument("-o", "--output", dest="output_file", default=None)
    compile_v2.add_argument("-v", "--verbose", action="store_true")

    args = parser.parse_args()

    if args.command == "compile":
        return cmd_compile_v1(args.input_file)
    if args.command == "compile-v2":
        return cmd_compile_v2(args.input_file, args.output_file, args.verbose)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
