"""AST → IR → structured output (compiler v2)."""

from __future__ import annotations

from dataclasses import dataclass

from compiler_v2.parser_v2 import Expr, Program, Stmt


@dataclass
class Instruction:
    op: str
    args: list[str]
    line: int = 0


@dataclass
class CompileResult:
    ir: list[Instruction]
    stdout_lines: list[str]
    symbols: dict[str, str | int | float]


class CompileError(Exception):
    def __init__(self, message: str, line: int = 0) -> None:
        self.line = line
        super().__init__(f"line {line}: {message}")


def _eval_expr(expr: Expr, env: dict[str, str | int | float]) -> str | int | float:
    if expr.kind == "string":
        return str(expr.value)
    if expr.kind == "number":
        return expr.value if expr.value is not None else 0
    if expr.kind == "ident":
        name = str(expr.value)
        if name not in env:
            raise CompileError(f"undefined variable '{name}'")
        return env[name]
    if expr.kind == "binary" and expr.left and expr.right:
        left = _eval_expr(expr.left, env)
        right = _eval_expr(expr.right, env)
        if not isinstance(left, (int, float)) or not isinstance(right, (int, float)):
            raise CompileError("arithmetic requires numeric operands")
        if expr.value == "+":
            return left + right
        if expr.value == "-":
            return left - right
        raise CompileError(f"unknown operator {expr.value!r}")
    raise CompileError("invalid expression")


def _format_value(val: str | int | float) -> str:
    return str(val)


def compile_program(program: Program) -> CompileResult:
    env: dict[str, str | int | float] = {}
    ir: list[Instruction] = []
    stdout_lines: list[str] = []

    for stmt in program.statements:
        if stmt.kind == "let":
            if not stmt.name or stmt.expr is None:
                raise CompileError("invalid let statement", stmt.line)
            try:
                value = _eval_expr(stmt.expr, env)
            except CompileError as e:
                raise CompileError(str(e), stmt.line) from e
            env[stmt.name] = value
            ir.append(
                Instruction(
                    op="STORE",
                    args=[stmt.name, _format_value(value)],
                    line=stmt.line,
                )
            )
        elif stmt.kind == "print":
            if not stmt.args:
                raise CompileError("print requires at least one argument", stmt.line)
            parts: list[str] = []
            for arg in stmt.args:
                try:
                    parts.append(_format_value(_eval_expr(arg, env)))
                except CompileError as e:
                    raise CompileError(str(e), stmt.line) from e
            line = " ".join(parts)
            stdout_lines.append(line)
            ir.append(Instruction(op="PRINT", args=parts, line=stmt.line))
        else:
            raise CompileError(f"unknown statement kind {stmt.kind!r}", stmt.line)

    return CompileResult(ir=ir, stdout_lines=stdout_lines, symbols=env)


def build_output_payload(
    source_path: str,
    program: Program,
    result: CompileResult,
) -> dict:
    return {
        "compiler": "v2",
        "version": 2,
        "source": source_path,
        "ok": True,
        "ast": {
            "statements": [
                {
                    "kind": s.kind,
                    "name": s.name,
                    "line": s.line,
                    "args": len(s.args) if s.args else 0,
                }
                for s in program.statements
            ]
        },
        "symbols": result.symbols,
        "ir": [{"op": i.op, "args": i.args, "line": i.line} for i in result.ir],
        "stdout": result.stdout_lines,
    }
