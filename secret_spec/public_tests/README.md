# Public Tests

This folder contains 150 public tests for the Knitting Compiler challenge. The tests are grouped into levels so you can work through `SECRET_SPEC.md` in a practical order.

Each test is either:

- a `.knit` input file plus a metadata `.json` file, or
- a metadata-only CLI test for usage errors such as missing arguments.

The metadata exists so the runner knows how to invoke the test and what exit code is expected. You do not need to edit these files.

## Levels

- `level_01_valid_basics` - 20 valid tests for `pattern`, `cast_on`, optional `bind_off`, no-row patterns, simple knit/purl rows, comments, blank lines, whitespace, leading zeros, and the `SECRET_SPEC.md` valid output example.
- `level_02_stitches` - 25 valid tests for every stitch operation, counted `kN`/`pN`, stitch-count changes, instruction object shape, and start/end stitch propagation.
- `level_03_brackets` - 25 valid tests for flat bracket repeats, nested bracket repeats, bracket repeats mixed with normal stitches, leading-zero repeat counts, and flattened instruction output.
- `level_04_row_repeats` - 20 valid tests for `repeat rows <start>-<end> x<count>`, source-row mapping, multiple repeat statements, repeats mixed with bracketed rows, and source-order expansion.
- `level_05_single_errors` - 30 invalid tests covering every defined error code at least once. These are mostly small diagnostic tests.
- `level_06_multi_error_recovery` - 15 invalid tests for recovery behavior, multiple errors across lines, same-line error ordering, duplicate/out-of-order interactions, and the `SECRET_SPEC.md` multiple-error example.
- `level_07_cli_output` - 5 CLI/output tests for valid exit `0`, invalid exit `1`, usage exit `2`, JSON-only stdout for compile runs, and empty stdout for usage errors.
- `level_08_stress` - 10 larger public tests for many rows, larger bracket/repeat expansion, comments, near-boundary stitch counts, and defined underflow/overflow behavior.

## Running Tests

From the repository root:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py"
```

Run one level:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --category level_04_row_repeats
```

Limit printed failures:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --failures 5
```

## Comparison Rules

For compile runs, stdout must be exactly one JSON object.

For usage errors, stdout must be empty and the process must exit `2`.

For invalid compile output, exact error message text is not compared. The runner compares `type`, `code`, `line`, and `row`; `message` only needs to be a non-empty string.

## About Hidden Tests

Hidden tests use the same frozen `SECRET_SPEC.md` and the same comparison rules. They are similar in spirit to the public tests, but combine rules more heavily and are not included in this package.
