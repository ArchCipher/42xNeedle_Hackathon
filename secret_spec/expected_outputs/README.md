# Expected Outputs

This folder contains the reference expected outputs for the 150 public tests.

Participants do not need to generate these files. The test runner reads them automatically.

Run public tests from the repository root with:

```bash
python3 RELEASE_2000/test_runner/run_tests.py --compiler "python3 knit.py"
```

For invalid compile outputs, exact error message text is not compared. The runner compares `type`, `code`, `line`, and `row`, and only checks that `message` is a non-empty string.
