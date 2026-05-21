# Backups — saved `knit.py` apps

The agent **overwrites** `knit.py` on each flexible-mode run. Copy working apps here before trying another prompt.

## Files

| File | What it is |
|------|------------|
| `knit_calculator.py` | CLI calculator (`add` / `sub` / `mul` / `div`) from mock spec smoke test |

## Save your own app

```bash
cp knit.py backups/knit_<your_app>.py
# example: backups/knit_taskmanager.py
```

Restore a backup as the live CLI:

```bash
cp backups/knit_calculator.py knit.py
python3 knit.py add 2 3
```

Restore the **hackathon compiler** entrypoint (from git):

```bash
git restore knit.py
```

## Where teammates save **tests** (not the same as backups)

| Kind of test | Save here | Notes |
|--------------|-----------|--------|
| **Automated pytest** (CI / `run_tests.py`) | `tests/` e.g. `tests/test_knit.py` | Shared; commit when the team agrees |
| **Manual commands you ran** | `tests/manual/<name>.md` | One short file per experiment (see `tests/manual/README.md`) |
| **Agent verify command** | `AGENT_VERIFY_COMMAND` in your shell, or note it in `tests/manual/` | Example: `python3 knit.py add 2 3` |
| **Agent run history** | `agent_logs/` | `commands.log`, `test_runs.log`, `decisions.log` — already used by the agent |
| **Working `knit.py` snapshot** | `backups/knit_<app>.py` | This folder |

Do **not** put one-off experiments only in `knit.py` without a backup — the next agent run will replace it.
