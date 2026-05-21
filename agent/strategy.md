# Hidden task strategy (agent playbook)

Use this with `secret_spec/SECRET_SPEC.md`. Read both before editing code.

## Likely task shape (from hackathon signals)

CLI program that:

1. Takes an input file path (`knit.py compile <file>` or spec-defined command)
2. Reads structured input (CSV, JSON, or text — **spec is authoritative**)
3. Transforms data — **row_expansion** is usually the highest-value feature (one input row -> many output rows)
4. Prints **exactly one JSON document to stdout** on success (schema from spec)
5. Uses **exit 0** on success, **non-zero** on invalid input / usage errors
6. Keeps diagnostics on **stderr only** (stdout discipline)

Example categories seen in judging materials: `row_expansion`, `invalid_schema`, `basic_cli`, edge cases.

## Spec reading checklist (do first)

When `SECRET_SPEC.md` exists, extract and log:

1. Exact CLI: command name, arguments, stdin vs file
2. Input format: CSV/JSON columns, delimiters, encoding (UTF-8)
3. Output JSON schema: every key name and type — **match exactly**
4. What **row expansion** means in *this* spec (split field, recurrence, line items, etc.)
5. Invalid input rules -> which exit code (usually 1)
6. Edge cases: empty file, missing fields, nulls, duplicates, special characters
7. stdout vs stderr rules

## Build order (highest test value first)

1. CLI in `knit.py` + wire to `src/`
2. Input reader (`utf-8`, empty file -> invalid)
3. Output JSON builder (schema skeleton with correct keys)
4. **Row expansion** logic
5. Invalid input handler + correct exit codes
6. Edge cases and stderr-only errors

## Score killers — avoid

| Risk | Fix |
|------|-----|
| Debug `print()` on stdout | Only final JSON on stdout; errors to stderr |
| Wrong JSON keys | Copy names from spec verbatim |
| Row expansion off-by-one | Test 0, 1, 2, 10 items in a splittable field |
| Wrong exit code | `return 0` success, `return 1` invalid (unless spec says otherwise) |
| Empty input crash | Check `path.read_text()` / zero rows first |

## Files you may edit

- `knit.py` — CLI entry (`compile` subcommand)
- `src/` — implementation
- Do **not** edit `agent/`, `compiler_v2/` (parallel experiment), or `agent_logs/` by hand

## Agent loop (one Ollama model)

Each `agent/agent.py run`:

1. **Setup (default: template, no LLM)** — writes `agent_logs/plan.md` + `spec_summary.md`
2. **Implement** — tools: `read_file`, `write_file`, `bash`, `run_tests` (per iteration)
3. **Test** — `python3 run_tests.py` (no LLM)
4. **Repair** — test output fed back to the model (optional `--diagnose` adds an LLM analysis)
5. Repeat 2–4 until pass or `max_iterations`

Use `--llm-setup` only after `SECRET_SPEC.md` exists and you want one LLM planning call.

## After each change

Call `run_tests` or let the iteration runner execute the configured public test command.

Focus the next patch on the **worst failing category** in test output (e.g. `row_expansion: 0/20` before cosmetic fixes).
