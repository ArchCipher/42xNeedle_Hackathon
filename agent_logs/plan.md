# Implementation plan (template)

## Operator task
Implement knit.py compile and src/ per secret_spec/SECRET_SPEC.md and agent_logs/plan.md. Priority: CLI + exit codes, JSON on stdout only, row_expansion, invalid input, edge cases. Use run_tests after each meaningful change.

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
