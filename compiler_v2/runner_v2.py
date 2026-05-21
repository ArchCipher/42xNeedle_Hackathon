"""Entry point for the v2 compile pipeline."""

from __future__ import annotations

import sys
from pathlib import Path

from compiler_v2.compiler_v2 import (
    CompileError,
    build_output_payload,
    compile_program,
)
from compiler_v2.parser_v2 import ParseError, parse
from compiler_v2.utils_v2 import (
    default_output_path,
    emit_json,
    read_source,
    setup_logging,
)


def compile_file(
    input_file: str,
    *,
    output_file: str | None = None,
    write_stdout: bool = True,
    verbose: bool = False,
) -> int:
    setup_logging(verbose)
    path = Path(input_file)

    try:
        source = read_source(path)
        program = parse(source)
        result = compile_program(program)
        payload = build_output_payload(str(path), program, result)
    except FileNotFoundError as e:
        print(str(e), file=sys.stderr)
        return 1
    except ParseError as e:
        print(f"parse error: {e}", file=sys.stderr)
        return 1
    except CompileError as e:
        print(f"compile error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        print(f"error: {e}", file=sys.stderr)
        return 1

    out_path = Path(output_file) if output_file else default_output_path(path)
    out_path.write_text(emit_json(payload), encoding="utf-8")

    if write_stdout:
        for line in payload.get("stdout", []):
            print(line)

    print(f"wrote {out_path}", file=sys.stderr)
    return 0
