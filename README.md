# 42 x Needle Hackathon — SPARK

Autonomous coding agent that builds the **Knit compiler** (`knit.py`). This repo is the team workspace for checkpoint, logs, agent code, and final submission.

## Repository layout

```text
├── agent/
│   ├── agent.py          # main agent loop
│   ├── logger.py         # writes to agent_logs/ (use this everywhere)
│   └── config.yaml       # model settings (see agent_manifest.json)
├── agent_logs/
│   ├── prompts.log
│   ├── decisions.log
│   ├── commands.log
│   ├── test_runs.log
│   ├── errors.log
│   ├── human_interventions.log
│   └── final_report.md
├── agent_manifest.json   # model disclosure (required for submission)
├── knit.py               # final compiler CLI
├── src/                  # compiler implementation (agent fills in)
├── secret_spec/          # copy SECRET_SPEC.md here at 20:00 Thursday
├── requirements.txt
└── README.md
```

## Quick start (teammates)

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # add API keys only locally; never commit .env
```

### Compiler (final program)

```bash
python3 knit.py compile <input_file>
```

Stub returns exit code 1 until `src/` is implemented.

### Compiler v1 vs v2

| | v1 (`compile`) | v2 (`compile-v2`) |
|---|----------------|-------------------|
| Entry | `knit.py` / `main.py compile` | `knit.py` / `main.py compile-v2` |
| Code | `knit.py` + `src/` (agent) | `compiler_v2/` (isolated) |
| Status | Unchanged stub until spec | Runnable pipeline |

```bash
python main.py compile examples/hello.knit      # v1 — same as knit.py
python main.py compile-v2 examples/hello.knit   # v2 — JSON + stdout
python knit.py compile-v2 examples/hello.knit
```

v2 writes `<input>.out.json` (structured IR, symbols, stdout) and prints runtime lines to stdout.

### Agent (free — Ollama only)

```bash
ollama serve && ollama pull qwen2.5-coder:7b
python3 agent/agent.py doctor
python3 agent/agent.py run              # default: fast template setup, then implement loop
python3 agent/agent.py run-once         # one implement → test → repair cycle
python3 agent/agent.py run --llm-setup  # optional: one LLM call for plan (only if SECRET_SPEC.md exists)
# use -q for logs-only (quiet)
```

**If Ollama is slow or times out:** warm up first with `ollama run qwen2.5-coder:7b`, then run the agent. Default setup does **not** call the model (writes `plan.md` from templates). See [Agent architecture](#agent-architecture) below.

**Windows:** use `py -3` instead of `python3`. Full guide: [docs/RUN_AND_TEST.md](docs/RUN_AND_TEST.md).

### Overnight monitor UI

```bash
python3 log_server.py
# open http://127.0.0.1:8765/index.html
```

See [docs/MONITOR_UI.md](docs/MONITOR_UI.md).

**Your prompt** goes on the `run` command line, in `$env:AGENT_TASK`, or at the interactive `Task:` prompt — not in a repo file by default.

Do **not** set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — the agent refuses paid APIs.

```bash
python3 agent/agent.py log-prompt "..." --context "..."
python3 agent/agent.py log-human --type PROMPT_EDIT --what "..."
```

Config: `agent/config.yaml`. **Rule:** use `agent/logger.py` for all agent activity logs.

If macOS prints `MallocStackLogging` lines in the terminal, run `unset MallocStackLogging` once before the agent (harmless noise; subprocess output is filtered).

## 19:45 checkpoint (Thursday)

Before the hidden spec drops at 20:00:

```bash
git add -A
git commit -m "Agent readiness checkpoint"
git tag agent-readiness-1945
git push --follow-tags
```

## Hidden task (20:00 Thursday)

Copy `SECRET_SPEC.md` from the [event repo](https://github.com/anavoronkova/42xNeedle_Hackathon/tree/main/secret_spec) into `secret_spec/`, then run the agent.

## Final submission (Friday 12:00)

Include in this repository:

- Final compiler (`knit.py`, `src/`)
- `agent_manifest.json`
- `agent_logs/` (all log files + `final_report.md`)
- `README.md` with exact run command and setup
- `requirements.txt` (if needed)

Required command shape:

```bash
python3 knit.py compile <input_file>
```

Fill in `agent_logs/final_report.md` before submitting.

## Team (edit before submission)

| Field | Value |
|-------|-------|
| Team name | SPARK |
| Members | Kiruthika Murugananthan, Sreya Thota, Ran Mo, Pedro Castro |
| Checkpoint tag | `agent-readiness-1945` |

**Collaboration:** [docs/COLLABORATION.md](docs/COLLABORATION.md) — role split, free stack, sync points (assign roles among yourselves).

## Agent architecture

**One Ollama model** (`agent/config.yaml`), **one Python loop** (`agent/agent.py`). No paid APIs.

### What is what

| Component | Purpose |
|-----------|---------|
| `knit.py` + `src/` | **Final product** — compiler the hackathon judges run |
| `run_tests.py` + `tests/` | **Team test harness** — pytest smoke tests for `knit.py` |
| `agent/agent.py` | **Autonomous agent** — reads spec, edits code, runs tests, logs |

### Loop (where the code lives)

Entry: `main()` → `run_agent()` in `agent/agent.py`.

```text
run_agent()
  │
  ├─ doctor path: ensure Ollama + model
  ├─ warm-up: tiny Ollama request (loads model into RAM)
  ├─ setup (fast by default):
  │     • template → agent_logs/spec_summary.md + plan.md  (no LLM)
  │     • OR --llm-setup + SECRET_SPEC.md → one LLM summary/plan call
  │
  └─ for iteration = 1 .. max_iterations (config: 40):
        _run_iteration()
          ├─ Phase 3 IMPLEMENT: _tool_rounds() — Ollama + tools
          │     read_file, write_file, bash, run_tests
          ├─ Phase 4 TEST: run_public_tests() — python3 run_tests.py (no LLM)
          ├─ if pass → stop
          └─ if fail → repair message (+ optional --diagnose LLM) → next iteration
```

**`run-once`** sets `max_iterations = 1` (one implement → test → repair cycle).

**Config:** `agent/config.yaml` — model, timeouts, `public_test_command`, `llm_setup`, `diagnose_on_failure`.

**Logs:** all steps append to `agent_logs/` via `agent/logger.py` (`decisions.log`, `commands.log`, `test_runs.log`, `errors.log`, …).

### Why a run might “hang” or crash

1. **First Ollama call on CPU** can take many minutes (not frozen — loading 7B weights).
2. **Old default** ran two LLM setup calls before any tools; that is now **template setup** (instant) unless you pass `--llm-setup`.
3. **`socket.timeout`** after `request_timeout_seconds` (default 900s) — warm up with `ollama run qwen2.5-coder:7b` or increase timeout in config.

### Task modes (`knit.py` is always the app)

| Mode | When | What the agent builds |
|------|------|------------------------|
| **`hackathon`** (default) | After spec / submission | `knit.py compile` compiler in `src/`; tests = `run_tests.py` |
| **`flexible`** | Before spec, demos | **Any app** the prompt describes, implemented **inside `knit.py`** (calculator, calendar, …) |

Mock calculator spec (minimal, for testing): [`secret_spec/MOCK_CALCULATOR_SPEC.md`](secret_spec/MOCK_CALCULATOR_SPEC.md) — steps in [`docs/TEST_CALCULATOR.md`](docs/TEST_CALCULATOR.md).

```bash
# Calculator (or any app) as knit.py:
cp secret_spec/MOCK_CALCULATOR_SPEC.md secret_spec/SECRET_SPEC.md
python3 agent/agent.py run --mode flexible --force-setup \
  "Build the calculator from secret_spec/SECRET_SPEC.md in knit.py"
# or: ./scripts/test_calculator_agent.sh
```

# After SECRET_SPEC.md arrives — switch back:
python3 agent/agent.py run --mode hackathon --force-setup
```

Flexible mode checks `python3 -m py_compile knit.py` each iteration; the model should use **bash** to run `python3 knit.py ...` and verify behavior. Set `AGENT_VERIFY_COMMAND` for a custom smoke command.

### Commands

| Command | Effect |
|---------|--------|
| `agent/agent.py run` | Full loop, template setup |
| `agent/agent.py run --mode flexible "..."` | Build prompt's app in `knit.py` |
| `agent/agent.py run-once` | Single iteration (good smoke test) |
| `agent/agent.py run --skip-setup` | Reuse existing `plan.md` |
| `agent/agent.py run --force-setup` | Regenerate template plan |
| `agent/agent.py run --llm-setup` | One LLM plan call (needs spec file) |
| `agent/agent.py run --diagnose` | Extra LLM call after test failures |
| `agent/agent.py plan` | Print checklist (no Ollama) |

## Agent docs (submission)

### Models used

See `agent_manifest.json` and `agent/config.yaml` (Ollama `qwen2.5-coder:7b`).

### Tools

`bash`, `read_file`, `write_file`, `run_tests` (runs `public_test_command` from config).

### Human interventions

```bash
python3 agent/agent.py log-human --type <TYPE> --what "..."
```

If none: `human_interventions.log` should state no post-release human edits.

## Resources

- [Rules and agenda](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/RULES_AND_AGENDA.md)
- [Agent spec](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/AGENT_SPEC.md)
- [Submission rules](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/SUBMISSION.md)
- [Judging criteria](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/JUDGING_CRITERIA.md)
- [Slides](https://docs.google.com/presentation/d/1-aUeomBiClmMT1SPtBEnupSbxZ9Kn3bjvy64RJBgdJI/edit?slide=id.g3a891c5084b_1_6#slide=id.g3a891c5084b_1_6)

## Final submission checklist

- [ ] `python3 knit.py compile <input_file>` works
- [ ] `agent_manifest.json` filled (no secrets)
- [ ] All `agent_logs/*` populated with timestamps
- [ ] `final_report.md` complete
- [ ] Checkpoint tag pushed
- [ ] No `.env`, `.venv/`, or API keys committed
