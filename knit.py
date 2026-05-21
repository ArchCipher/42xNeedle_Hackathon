#!/usr/bin/env python3
"""Knit compiler CLI — final program entrypoint (hidden spec defines behavior)."""

from __future__ import annotations

import argparse
import sys


def cmd_compile(input_file: str) -> int:
    from src.compile import compile_file

    return compile_file(input_file)


def cmd_compile_v2(input_file: str) -> int:
    from compiler_v2.runner_v2 import compile_file

    return compile_file(input_file)


def main() -> int:
    parser = argparse.ArgumentParser(description="Knit compiler")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile", help="Compile input file")
    compile_parser.add_argument("input_file", help="Path to input file")
    compile_v2_parser = sub.add_parser(
        "compile-v2",
        help="Compile input file with compiler v2",
    )
    compile_v2_parser.add_argument("input_file", help="Path to input file")
    args = parser.parse_args()

    if args.command == "compile":
        return cmd_compile(args.input_file)
    if args.command == "compile-v2":
        return cmd_compile_v2(args.input_file)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
