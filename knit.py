#!/usr/bin/env python3
"""Knit compiler CLI — final program entrypoint (hidden spec defines behavior)."""

from __future__ import annotations

import argparse
import sys


def cmd_compile(input_file: str) -> int:
    # TODO: implement after secret_spec/ is released
    print(f"compile not implemented yet: {input_file}", file=sys.stderr)
    return 1


def main() -> int:
    parser = argparse.ArgumentParser(description="Knit compiler")
    sub = parser.add_subparsers(dest="command", required=True)
    compile_parser = sub.add_parser("compile", help="Compile input file")
    compile_parser.add_argument("input_file", help="Path to input file")
    args = parser.parse_args()

    if args.command == "compile":
        return cmd_compile(args.input_file)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
