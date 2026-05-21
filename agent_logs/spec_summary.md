# Spec summary (template)

Setup mode: no spec file

Operator task:
read the spec and write knit.py

Specification excerpt:
(secret_spec/SECRET_SPEC.md not present — copy from event repo at 20:00.)


SPEC CHECKLIST (complete before coding):
  [ ] CLI command and arguments
  [ ] Input format (CSV/JSON/text, encoding)
  [ ] Output JSON schema — all keys and types
  [ ] row_expansion definition in this spec
  [ ] Invalid input -> exit code
  [ ] Edge cases listed in spec
  [ ] stdout vs stderr rules
IMPLEMENTATION ORDER: CLI -> reader -> JSON schema -> row_expansion -> invalid handler -> edges
