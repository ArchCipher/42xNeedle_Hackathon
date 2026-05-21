# Test Runner

`run_tests.py` runs the public Knitting Compiler tests against your `knit.py` and compares the output to the provided reference outputs.

The release runner discovers tests from `RELEASE_2000/public_tests/`. You do not need `manifest.json`.

## Basic Command

From the repository root:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py"
```

The runner invokes normal compile tests as:

```bash
python3 knit.py compile <input_file>
```

## Run One Level

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --category level_03_brackets
```

## Options

Limit printed failures:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --failures 5
```

Write a JSON report:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --json-report public_report.json
```

Run a quick exit-code smoke check:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py" --mode exit-only
```

Smoke mode does not fully score JSON output. It is only a quick sanity check.

## What Is Compared

For valid and invalid compile runs, stdout must be exactly one JSON object.

The runner compares:

- process exit code
- top-level JSON fields
- expanded rows
- flattened instruction objects
- final stitch count
- bind-off value
- error order and normalized error fields

For invalid outputs, exact error message wording is not compared. The runner compares only:

- `type`
- `code`
- `line`
- `row`

Each error `message` only has to be a non-empty string.

For usage errors, exit code must be `2` and stdout must be empty.

## Common Failures

```text
exit code expected 0, got 1
```

The test is expected to be valid, but your compiler reported an invalid compile.

```text
$.expanded_rows[2].source_row: expected 1, got 3
```

Your output was JSON, but a field did not match the reference output.

```text
stdout contains non-JSON text after the JSON document
```

Your compiler printed extra text to stdout. Debug output should go to stderr.

```text
missing expected output
```

The expected-output folder is missing or the release package was moved incorrectly. By default the runner expects `RELEASE_2000/expected_outputs/`.
