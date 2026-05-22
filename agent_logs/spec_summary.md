# Spec summary (template)

Setup mode: llm_setup disabled (use --llm-setup)

Operator task:
 Build a knitting compiler from secret_spec/SECRET_SPEC.md in knit.py

Specification excerpt:
# Secret Spec: A Knitting Compiler

## 1. Goal

Build a command-line tool called **Knitting Compiler**.

The tool reads knitting pattern files written in a small domain-specific language, parses them, validates them, expands repeats, simulates stitch counts row by row, and prints one structured JSON document to stdout.

This is a compiler/interpreter-style problem. The domain is knitting because the sponsor is called Needle, and apparently we are all committed to the bit. The technical task is still serious: parsing, validation, simulation, error recovery, and deterministic output.

## 2. Required CLI

Your tool must support exactly this command shape:

```bash
python knit.py compile <input_file>
```

Example:

```bash
python knit.py compile examples/scarf.knit
```

The `compile` command must print exactly one JSON document to stdout.

It must not print logs, debug output, explanations, success messages, stack traces, or any other non-JSON text to stdout.

All diagnostic or debug output, if any, must go to stderr. For judging, stdout is the contract.

## 3. Input Files

Input files use the `.knit` extension.

Example:

```text
pattern "Tiny Doom Scarf"

cast_on 10

row 1: k10
row 2: p10
row 3: k2, yo, k6, k2tog

repeat rows 1-3 x2

bind_off
```

Blank lines are allowed.

Line numbers are 1-based physical line numbers in the input file. Blank lines and comments still count for line numbering.

## 4. Comments

A `#` character outside a quoted pattern name begins a comment.

A comment extends from `#` to the end of the line.

For comment stripping, double quotes are tracked lexically before pattern validation. A `#` character after an opening double quote is treated as part of the attempted quoted string until a closing double quote is found. If the quote is never closed, the line is malformed; the `#` does not start a comment in that case. Escaped quotes are not supported.

Examples:

```text
# full-line comment
row 1: k10   # inline comment
```

The parser must ignore comments.

## 5. Case Sensitivity

All keywords and stitch operations are case-sensitive and lowercase.

Valid keywords:

```text
pattern
cast_on
row
repeat
bind_off
```

Valid stitch operations:

```text
k
p
yo
k2tog
ssk
inc
dec
```

Examples:

```text
row 1: k10      # valid
row 1: K10      # invalid: UNKNOWN_STITCH
Pattern "Hat"   # invalid: UNKNOWN_STATEMENT
```

## 6. Statement Recognition and Malformed Statements

After removing comments and trimming leading/trailing whitespace:

- An empty line is ignored.
- Statement recognition requires a token boundary. A recognized keyword must be followed by whitespace or end of line. The keyword must not be glued directly to its argument or to other text. For example, `patterned "Hat"`, `pattern"Hat"`, `cast_on10`, `row1: k1`, `repeatrows 1-2 x1`, and `bind_offnow` are all `UNKNOWN_STATEMENT`, not malformed versions of their visually similar statements.
- A line beginning with a recognized statement keyword but not matching that statement's required syntax must be reported using the corresponding malformed error code.
- A line that does not begin with any recognized statement keyword must be reported as `UNKNOWN_STATEMENT`.
- Trailing non-comment text after an otherwise valid statement makes that statement malformed. For example, `cast_on 10 extra` is `MALFORMED_CAST_ON`, `row 1: k1 extra` is `MALFORMED_ROW`, and `repeat rows 1-1 x1 extra` is `MALFORMED_REPEAT`.
- If a malformed statement uses a recognized keyword, the corresponding missing-statement error is suppressed. For example, a file containing only `pattern Bad` should report `MALFORMED_PATTERN`, not both `MALFORMED_PATTERN` and `MISSING_PATTERN`.

Examples:

```text
pattern Tiny Doom Scarf     # MALFORMED_PATTERN: missing double quotes
cast on 10                  # UNKNOWN_STATEMENT: keyword is not cast_on
cast_on ten                 # MALFORMED_CAST_ON
row 1 k10                   # MALFORMED_ROW: missing colon
repeat row 1-3 x2           # MALFORMED_REPEAT
bind_off now                # MALFORMED_BIND_OFF
bind_offnow                 # UNKNOWN_STATEMENT: no token boundary after bind_off
patterned "Hat"             # UNKNOWN_STATEMENT: no token boundary after pattern
pattern"Hat"                # UNKNOWN_STATEMENT: no token boundary after pattern
cast_on10                   # UNKNOWN_STATEMENT: no token boundary after cast_on
repeatrows 1-2 x1           # UNKNOWN_STATEMENT: no token boundary after repeat
row1: k1                    # UNKNOWN_STATEMENT: no token boundary after row
cast_on 10 extra            # MALFORMED_CAST_ON: trailing non-comment text
```

## 6A. Positive Integers

All positive integers in this spec are parsed as base-10 integer values. Leading zeros are allowed as long as the resulting value is positive.

Examples:

```text
cast_on 05              # valid, value 5
row 01: k1              # valid row number 1
row 1: k01              # valid stitch count 1
[k1] x02                # valid repeat count 2
repeat rows 01-02 x03   # valid range 1-2, count 3
```

All output JSON must use normalized integer values, not the original textual representation. For example, `row 01: k1` has `source_row: 1`.

```text
cast_on 00              # invalid: MALFORMED_CAST_ON
row 00: k1              # invalid: MALFORMED_ROW
[k1] x00                # invalid: MALFORMED_ROW
repeat rows 00-01 x1    # invalid: INVALID_REPEAT_RANGE
```

## 7. Pattern Declaration

Every pattern must contain exactly one pattern declaration:

```text
pattern "Pattern Name"
```

The pattern name is any sequence of characters inside double quotes, excluding newline and unescaped double quote.

Escaped quotes are not supported.

Examples:

```text
pattern "Tiny Doom Scarf"   # valid
pattern ""                  # valid, empty name
pattern Tiny Doom Scarf      # invalid
pattern "Bad " Name"        # invalid
```

The output `pattern_name` value must preserve the pattern name string. JSON escaping is allowed as long as it represents the same string value after JSON parsing.

If multiple valid pattern declarations exist, the compiler must report `DUPLICATE_PATTERN` for each additional valid pattern declaration after the first. The error `line` must be the line of the additional duplicate declaration. In this case, output `pattern_name: null`.

If a file contains a recognized but malformed `pattern` statement and no valid pattern declaration, report `MALFORMED_PATTERN`, suppress `MISSING_PATTERN`, and output `pattern_name: null`.

## 8. Cast On

Every pattern must contain exactly one cast-on declaration:

```text
cast_on 24
```

Rules:

- `cast_on` must be a positive integer.
- `cast_on` must appear before any row statement.
- A row statement means any non-empty, non-comment line recognized with the `row` keyword and token boundary, including malformed rows, empty rows, rows with unknown stitches, and rows with invalid row numbers such as `row 0: k1`.
- Duplicate `cast_on` declarations are invalid.
- If any recognized `cast_on` statement appears after rows, report `CAST_ON_OUT_OF_ORDER`, even if that `cast_on` statement is malformed.
- If a `cast_on` statement appears after rows and is also a duplicate, report both `CAST_ON_OUT_OF_ORDER` and `DUPLICATE_CAST_ON`.

Examples:

```text
cast_on 24     # valid
cast_on 0      # invalid: MALFORMED_CAST_ON
cast_on -3     # invalid: MALFORMED_CAST_ON
cast_on ten    # invalid: MALFORMED_CAST_ON
```

If multiple syntactically valid `cast_on` declarations exist, the compiler must report `DUPLICATE_CAST_ON` for each additional valid `cast_on` declaration after the first. The error `line` must be the line of the additional duplicate declaration. In this case, output `cast_on: null`.

If the only syntactically valid `cast_on` appears after a row statement, output the parsed `cast_on` value, but report `CAST_ON_OUT_OF_ORDER`. That `cast_on` value is not usable for stitch simulation.

If a malformed `cast_on` appears after rows, report both `MALFORMED_CAST_ON` and `CAST_ON_OUT_OF_ORDER`
...(truncated)...


SPEC CHECKLIST (complete before coding):
  [ ] CLI command and arguments
  [ ] Input format (CSV/JSON/text, encoding)
  [ ] Output JSON schema — all keys and types
  [ ] row_expansion definition in this spec
  [ ] Invalid input -> exit code
  [ ] Edge cases listed in spec
  [ ] stdout vs stderr rules
IMPLEMENTATION ORDER: CLI -> reader -> JSON schema -> row_expansion -> invalid handler -> edges
