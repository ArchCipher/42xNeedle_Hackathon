"""Lexer and parser for Knit source (v2 pipeline)."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum, auto
class TokenKind(Enum):
    LET = auto()
    PRINT = auto()
    IDENT = auto()
    STRING = auto()
    NUMBER = auto()
    EQ = auto()
    COMMA = auto()
    PLUS = auto()
    MINUS = auto()
    NEWLINE = auto()
    EOF = auto()


@dataclass(frozen=True)
class Token:
    kind: TokenKind
    value: str
    line: int
    col: int


@dataclass
class Expr:
    kind: str
    value: str | float | None = None
    left: Expr | None = None
    right: Expr | None = None


@dataclass
class Stmt:
    kind: str
    name: str | None = None
    expr: Expr | None = None
    args: list[Expr] | None = None
    line: int = 0


@dataclass
class Program:
    statements: list[Stmt]


class ParseError(Exception):
    def __init__(self, message: str, line: int = 0, col: int = 0) -> None:
        self.line = line
        self.col = col
        super().__init__(f"line {line}, col {col}: {message}")


def _tokenize(source: str) -> list[Token]:
    tokens: list[Token] = []
    line = 1
    col = 1
    i = 0
    n = len(source)

    def emit(kind: TokenKind, value: str, t_line: int, t_col: int) -> None:
        tokens.append(Token(kind, value, t_line, t_col))

    while i < n:
        ch = source[i]

        if ch == "\n":
            emit(TokenKind.NEWLINE, "\n", line, col)
            line += 1
            col = 1
            i += 1
            continue

        if ch in " \t\r":
            i += 1
            col += 1
            continue

        if ch == "#":
            while i < n and source[i] != "\n":
                i += 1
            continue

        if ch == "=":
            emit(TokenKind.EQ, "=", line, col)
            i += 1
            col += 1
            continue

        if ch == ",":
            emit(TokenKind.COMMA, ",", line, col)
            i += 1
            col += 1
            continue

        if ch == "+":
            emit(TokenKind.PLUS, "+", line, col)
            i += 1
            col += 1
            continue

        if ch == "-":
            if i + 1 < n and source[i + 1].isdigit():
                start = i
                i += 1
                col += 1
                while i < n and (source[i].isdigit() or source[i] == "."):
                    i += 1
                    col += 1
                emit(TokenKind.NUMBER, source[start:i], line, start + 1)
                continue
            emit(TokenKind.MINUS, "-", line, col)
            i += 1
            col += 1
            continue

        if ch in "\"'":
            quote = ch
            start_line, start_col = line, col
            i += 1
            col += 1
            buf: list[str] = []
            while i < n:
                c = source[i]
                if c == "\\" and i + 1 < n:
                    nxt = source[i + 1]
                    escapes = {"n": "\n", "t": "\t", "\\": "\\", quote: quote}
                    buf.append(escapes.get(nxt, nxt))
                    i += 2
                    col += 2
                    if nxt == "\n":
                        line += 1
                        col = 1
                    continue
                if c == quote:
                    i += 1
                    col += 1
                    emit(TokenKind.STRING, "".join(buf), start_line, start_col)
                    break
                if c == "\n":
                    raise ParseError("unterminated string", start_line, start_col)
                buf.append(c)
                if c == "\n":
                    line += 1
                    col = 1
                else:
                    col += 1
                i += 1
            else:
                raise ParseError("unterminated string", start_line, start_col)
            continue

        if ch.isdigit():
            start = i
            while i < n and (source[i].isdigit() or source[i] == "."):
                i += 1
                col += i - start
            emit(TokenKind.NUMBER, source[start:i], line, start + 1)
            continue

        if ch.isalpha() or ch == "_":
            start = i
            while i < n and (source[i].isalnum() or source[i] == "_"):
                i += 1
            word = source[start:i]
            col += i - start
            kw = word.lower()
            if kw == "let":
                emit(TokenKind.LET, word, line, start + 1)
            elif kw == "print":
                emit(TokenKind.PRINT, word, line, start + 1)
            else:
                emit(TokenKind.IDENT, word, line, start + 1)
            continue

        raise ParseError(f"unexpected character {ch!r}", line, col)

    emit(TokenKind.EOF, "", line, col)
    return tokens


class _Parser:
    def __init__(self, tokens: list[Token]) -> None:
        self.tokens = tokens
        self.pos = 0

    def _peek(self) -> Token:
        return self.tokens[self.pos]

    def _advance(self) -> Token:
        tok = self.tokens[self.pos]
        if tok.kind != TokenKind.EOF:
            self.pos += 1
        return tok

    def _match(self, kind: TokenKind) -> Token | None:
        if self._peek().kind == kind:
            return self._advance()
        return None

    def _expect(self, kind: TokenKind, msg: str) -> Token:
        tok = self._peek()
        if tok.kind != kind:
            raise ParseError(msg, tok.line, tok.col)
        return self._advance()

    def _skip_newlines(self) -> None:
        while self._match(TokenKind.NEWLINE):
            pass

    def parse(self) -> Program:
        stmts: list[Stmt] = []
        self._skip_newlines()
        while self._peek().kind != TokenKind.EOF:
            stmts.append(self._statement())
            self._skip_newlines()
        return Program(statements=stmts)

    def _statement(self) -> Stmt:
        tok = self._peek()
        if tok.kind == TokenKind.LET:
            return self._let_stmt()
        if tok.kind == TokenKind.PRINT:
            return self._print_stmt()
        raise ParseError(
            f"expected 'let' or 'print', got {tok.value!r}",
            tok.line,
            tok.col,
        )

    def _let_stmt(self) -> Stmt:
        let_tok = self._expect(TokenKind.LET, "expected 'let'")
        name_tok = self._expect(TokenKind.IDENT, "expected variable name after 'let'")
        self._expect(TokenKind.EQ, "expected '=' after variable name")
        expr = self._expr()
        return Stmt(kind="let", name=name_tok.value, expr=expr, line=let_tok.line)

    def _print_stmt(self) -> Stmt:
        print_tok = self._expect(TokenKind.PRINT, "expected 'print'")
        args = [self._expr()]
        while self._match(TokenKind.COMMA):
            args.append(self._expr())
        return Stmt(kind="print", args=args, line=print_tok.line)

    def _expr(self) -> Expr:
        left = self._primary()
        while self._peek().kind in (TokenKind.PLUS, TokenKind.MINUS):
            op = self._advance()
            right = self._primary()
            left = Expr(
                kind="binary",
                value=op.value,
                left=left,
                right=right,
            )
        return left

    def _primary(self) -> Expr:
        tok = self._peek()
        if tok.kind == TokenKind.STRING:
            self._advance()
            return Expr(kind="string", value=tok.value)
        if tok.kind == TokenKind.NUMBER:
            self._advance()
            raw = tok.value
            val: float | int = float(raw) if "." in raw else int(raw)
            return Expr(kind="number", value=val)
        if tok.kind == TokenKind.IDENT:
            self._advance()
            return Expr(kind="ident", value=tok.value)
        raise ParseError("expected expression", tok.line, tok.col)


def parse(source: str) -> Program:
    tokens = [t for t in _tokenize(source) if t.kind != TokenKind.NEWLINE]
    return _Parser(tokens).parse()
