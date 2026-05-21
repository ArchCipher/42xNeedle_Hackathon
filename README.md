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
python3 agent/agent.py run "Read secret_spec and implement knit.py"
python3 agent/agent.py run-once "Read secret_spec/SECRET_SPEC.md"   # single iteration (verbose terminal output)
# use -q for logs-only (quiet)
```

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

## Agent docs (fill as you build)

### Overview

TBD

### Objective

Build the Knit compiler autonomously from `secret_spec/`, iterating on public tests.

### Architecture

Ollama loop in `agent/agent.py`: read spec → model+tools (`bash`, `read_file`, `write_file`, `run_tests`) → public tests → log → repeat. Modules: `ollama_client.py`, `tools.py`, `logger.py`.

### Models used

See `agent_manifest.json` and `agent/config.yaml`.

### Tools available

TBD — bash, read/write files, public test runner, etc.

### Prompt strategy

TBD

### Test loop

TBD — document command in `test_runs.log` via `AgentLogger.test_run()`.

### Score progression

TBD — log each public run in `test_runs.log`.

### Failures + recovery

TBD — log in `errors.log` and `decisions.log`.

### Human interventions

Log every post-release human action:

```bash
python3 agent/agent.py log-human --type <TYPE> --what "..."
```

If none: ensure `human_interventions.log` contains  
`No human interventions after hidden task release.`

### What we would improve

TBD

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
