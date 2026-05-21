# Team collaboration guide

How to split work when **everyone uses agents** to build the project. The final product must stay **fully free** (local models, no paid APIs after the hidden spec is released at 20:00 Thursday).

Assign roles among the four teammates yourselves. Each role owns specific paths so agents do not edit the same files at once.

---

## Division of labor (pick who owns each role)

### Role 1 — Agent core & orchestration

**Owns:** `agent/agent.py`, `agent/config.yaml`, agent architecture notes in `README.md`

**Status:** Implemented (Ollama only, no paid APIs). Verify: `python3 agent/agent.py doctor`

**Teammate smoke test (calculator):** [docs/TEST_CALCULATOR.md](TEST_CALCULATOR.md) — `run --mode flexible --force-setup` with `secret_spec/MOCK_CALCULATOR_SPEC.md`.

**Responsibilities:**

- Main loop: read spec → plan → act → test → repair
- Wire a **free** model (e.g. Ollama: `qwen2.5-coder:7b` or similar)
- Iteration limits, stop conditions, crash recovery
- Ensure every loop step uses `AgentLogger` in `agent/logger.py`

**Example agent prompts:**

- Implement `_run_iteration()` to read `secret_spec/SECRET_SPEC.md` and produce a plan.
- Add tool dispatch for read / write / bash without touching `src/`.

**Avoid:** Deep changes in `src/`; writing `final_report.md` (except supplying architecture notes).

---

### Role 2 — Compiler implementation

**Owns:** `src/`, `knit.py` (CLI behavior)

**Responsibilities:**

- Implement `python3 knit.py compile <input_file>` per the hidden spec
- Parser, codegen, errors, exit codes
- Minimal working path first, then edge cases

**Example agent prompts:**

- Implement minimal compile for the first valid case; do not refactor `agent/`.
- Fix exit codes for invalid input per spec section X.

**Avoid:** `agent/agent.py` loop logic; `agent_manifest.json`.

**Handoff:** Notify the team when a build runs; share sample input files.

---

### Role 3 — Test loop & failure feedback

**Owns:** Public test integration, `test_runs.log` discipline, test commands wired into the agent

**Responsibilities:**

- Script/command to run **public** tests (use the exact command from the spec when released)
- Parse failures into structured summaries (category, expected vs actual)
- Coordinate with Role 1 only on the call site for `run_public_tests()` in `agent/agent.py`
- Log score progression on every run

**Example agent prompts:**

- Parse public runner output into failure categories.
- Add self-tests for exit codes from the spec; log to `test_runs.log`.

**Avoid:** Large parser rewrites in `src/`; prefer a “failure packet” for Role 2’s agent.

**Deliverable:** One canonical test command + log format for the team.

---

### Role 4 — Process, logging, submission & presentation

**Owns:** `agent_logs/` quality, `agent_manifest.json`, `final_report.md`, README submission sections, presentation outline

**Responsibilities:**

- Enforce log formats after hidden task release (prompts, human interventions, decisions)
- Fill `agent_manifest.json` (free models only; honest disclosure)
- README: setup, final command, checkpoint tag, known limitations
- Maintain `final_report.md` during and after the run
- Friday checklist and presentation (focus on the **agent**, not long compiler walkthroughs)

**Example agent prompts:**

- Draft `final_report.md` sections from `test_runs.log` and `decisions.log`.
- Prepare a `human_interventions.log` entry when someone restarts the agent.

**Avoid:** Compiler logic in `src/`. Flag any manual edits to final program logic (not allowed after release).

---

## Free stack (whole team)

| Layer | Free choice |
|--------|-------------|
| Model | Ollama local (e.g. `qwen2.5-coder:7b`; optional second model for reviewing failures) |
| Runtime | Python 3 + `agent/agent.py` |
| IDE assist | Disclose in `agent_manifest.json`; no paid Copilot on hidden task **after 20:00** |
| Secrets | Never commit `.env` or API keys; do not log credentials |

Record exact model names in `agent/config.yaml` and `agent_manifest.json`.

---

## Coordination rules

1. **One owner per path** — do not run two agents on the same file; use branches per role.
2. **Shared contracts** — agree in chat or here on: test command, compile command, failure log format.
3. **Sync points**
   - **Before 19:45:** agent skeleton runs; `knit.py` stub exists; logger works.
   - **20:00:** copy `SECRET_SPEC.md` into `secret_spec/`; Role 1’s agent reads it; others wait for a short plan.
   - **During build:** Role 3 posts scores; Role 2 fixes by category; Role 1 reruns the agent when a test packet is ready.
4. **Human interventions** — log every post-release human action:

   ```bash
   python3 agent/agent.py log-human --type <TYPE> --what "..."
   ```

5. **Git** — short-lived branches, e.g. `agent/loop`, `compiler/parser`, `tests/public`, `docs/submission`; merge via PR or pair review.

---

## Suggested timeline

| Phase | Role 1 | Role 2 | Role 3 | Role 4 |
|--------|--------|--------|--------|--------|
| Before 19:45 | Agent loop + tools | `knit.py` + `src/` layout | Test hook placeholder | README + manifest template |
| 19:45 | Checkpoint commit | Checkpoint commit | Checkpoint commit | Tag `agent-readiness-1945` + push |
| 20:00+ | Agent plans from spec | Compiler MVP | Run public tests | Log prompts; spec in repo |
| Overnight | Loop + tool fixes | Fix by failure category | Score tracking | `final_report` draft |
| Friday AM | Stabilize agent | Freeze compiler | Last public run | Submission checklist |
| Present | Architecture + loop | ≤1 slide on compiler | Score progression | Interventions + lessons |

---

## Repository map (quick reference)

```text
agent/              → Role 1
src/, knit.py       → Role 2
test runner hook    → Role 3 (wire in agent/agent.py with Role 1)
agent_logs/, manifest, final_report, README submission → Role 4
secret_spec/        → copy spec at 20:00; all roles read, Role 1 plans
```

---

## Team members

Kiruthika Murugananthan, Sreya Thota, Ran Mo, Pedro Castro

**Team name:** SPARK
