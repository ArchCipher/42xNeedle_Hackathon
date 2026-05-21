# Manual test notes (teammates)

Use this folder for **human-run checks** that are not worth automating in `tests/test_knit.py` yet.

## What to add

Create a file per experiment:

```text
tests/manual/<your_name>_<app>.md
```

Example: `tests/manual/kiru_calculator.md`

Include:

- Date and branch
- Command you ran the agent with (`--mode flexible` / `hackathon`)
- `AGENT_VERIFY_COMMAND` if you set one
- Commands you typed to verify (copy-paste from terminal)
- Pass / fail and one-line notes

## Example

```markdown
# Calculator smoke test

- Agent: `python3 agent/agent.py run --mode flexible --force-setup "Build calculator..."`
- Verify: `python3 knit.py add 2 3` → `5.0`, exit 0
- Backup: `backups/knit_calculator.py`
```

## Automated tests stay in `tests/`

Shared pytest for the repo: `tests/test_knit.py`, run with `python3 run_tests.py`.
