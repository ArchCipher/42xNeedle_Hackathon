# Implementation plan (template)

## Operator task
Build the CLI calculator from secret_spec/SECRET_SPEC.md in knit.py

## knit.py is the app
All user-facing behavior lives in knit.py (helpers in src/).

## Steps
1. read_file secret_spec/SECRET_SPEC.md
2. Implement knit.py compile in src/ per spec
3. run_tests after each meaningful change


SPEC CHECKLIST (complete before coding):
  [ ] CLI command and arguments
  [ ] Input format (CSV/JSON/text, encoding)
  [ ] Output JSON schema — all keys and types
  [ ] row_expansion definition in this spec
  [ ] Invalid input -> exit code
  [ ] Edge cases listed in spec
  [ ] stdout vs stderr rules
IMPLEMENTATION ORDER: CLI -> reader -> JSON schema -> row_expansion -> invalid handler -> edges
