# Spec summary (template)

Setup mode: llm_setup disabled (use --llm-setup)

Operator task:
Build the CLI calculator from secret_spec/SECRET_SPEC.md in knit.py

Specification excerpt:
# Mock task — CLI calculator (intentionally brief)

> **Test only.** Copy to `SECRET_SPEC.md` to run the agent against this spec:
> `cp secret_spec/MOCK_CALCULATOR_SPEC.md secret_spec/SECRET_SPEC.md`

## Product

A **command-line calculator**. The program users run is **`knit.py`** (helpers may live in `src/`).

## Behavior (minimal)

- Support **add**, **subtract**, **multiply**, **divide** on two numbers.
- Invalid input or divide-by-zero → non-zero exit, message on **stderr**.
- Successful operation → print the numeric result on **stdout**, exit **0**.

## Interface (not fully specified — agent must decide)

Design a reasonable CLI, for example subcommands or positional arguments. Document usage in a short comment at the top of `knit.py`.

Example shapes (pick one or similar):

```text
python3 knit.py add 2 3
python3 knit.py calc add 2 3
```

## Non-goals

- No GUI, no network, no database.
- Does not need to keep the existing `compile` / `compile-v2` commands unless you wire them as aliases.

## Done when

- `python3 knit.py` runs without syntax errors.
- A few manual cases work (e.g. add, div, bad input).



SPEC CHECKLIST (complete before coding):
  [ ] CLI command and arguments
  [ ] Input format (CSV/JSON/text, encoding)
  [ ] Output JSON schema — all keys and types
  [ ] row_expansion definition in this spec
  [ ] Invalid input -> exit code
  [ ] Edge cases listed in spec
  [ ] stdout vs stderr rules
IMPLEMENTATION ORDER: CLI -> reader -> JSON schema -> row_expansion -> invalid handler -> edges
