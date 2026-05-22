# 42 x Needle Hackathon — SPARK

Autonomous coding agent that builds the **Knitting Compiler** (`python3 knit.py compile <file.knit>` → JSON on stdout). This repo contains the agent loop, official public tests, logs, and `src/` implementation work.

## Repository layout

```text
├── agent/
│   ├── agent.py          # main agent loop
│   ├── config.yaml       # model, timeouts, public_test_command
│   ├── logger.py         # writes to agent_logs/
│   └── strategy.md
├── agent_logs/
│   ├── prompts.log
│   ├── decisions.log
│   ├── commands.log
│   ├── test_runs.log
│   ├── errors.log
│   ├── human_interventions.log
│   ├── pending_prompt.txt   # operator steering (read each iteration)
│   ├── plan.md
│   ├── spec_summary.md
│   └── final_report.md
├── agent_manifest.json
├── knit.py               # submission CLI entrypoint
├── src/                  # compile logic (agent implements)
├── secret_spec/
│   ├── SECRET_SPEC.md    # hidden task (knitting DSL compiler)
│   ├── public_tests/
│   ├── expected_outputs/
│   └── test_runner/run_tests.py
├── run_tests.py          # team pytest smoke tests (4 tests)
├── tests/
├── benchmark.py          # readiness score script
├── compiler_v2/          # optional reference pipeline (compile-v2 only)
├── backups/              # saved knit.py snapshots from practice runs
└── log_server.py         # monitor UI
```

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env        # local only; never commit .env
```

### Compiler (submission program)

```bash
python3 knit.py compile secret_spec/public_tests/level_01_valid_basics/pub_level_01_valid_basics_001.knit
```

`src/compile.py` must implement behavior per `secret_spec/SECRET_SPEC.md` (parse, validate, simulate stitch counts, emit **one JSON document on stdout**). Until then, the stub exits non-zero.

### Public tests (official scoreboard — 150 tests)

```bash
python3 secret_spec/test_runner/run_tests.py --compiler "python3 knit.py" --suite public
```

The agent uses this command in hackathon mode (`agent/config.yaml` → `public_test_command`). A stub compiler typically scores **3/150** (three CLI usage checks only); real progress shows up in `level_01_valid_basics` and above.

### Team smoke tests (pytest, 4 tests)

```bash
python3 run_tests.py
```

Quick check that `knit.py` exists, `compile-v2` works on `examples/hello.knit`, and `compile` is wired (may fail until implemented).

### Compiler v1 vs v2 (reference only)

| | v1 (`compile`) — **submission** | v2 (`compile-v2`) — practice |
|---|----------------------------------|------------------------------|
| Code | `knit.py` + `src/` | `compiler_v2/` (do not edit for submission) |
| Tests | Official 150 + team pytest | `examples/hello.knit` smoke |

```bash
python3 knit.py compile-v2 examples/hello.knit
```

## Agent (Ollama only — no paid APIs)

```bash
ollama serve && ollama pull qwen2.5-coder:7b
python3 agent/agent.py doctor
```

**Hackathon run** (real task — after `secret_spec/` is present):

```bash
python3 agent/agent.py run --mode hackathon --skip-setup \
  "Build the knitting compiler from secret_spec/SECRET_SPEC.md in knit.py and src/"
```

Use `--force-setup` on first run to regenerate `agent_logs/plan.md` and `spec_summary.md`. Use `--skip-setup` on restarts.

Other useful flags:

| Flag | Effect |
|------|--------|
| `--diagnose` | Extra LLM pass on test failures (slower) |
| `--llm-setup` | One LLM call for plan (default is fast template setup) |
| `run-once` | Single iteration only |

**Steer a running agent** — write the next instruction to `agent_logs/pending_prompt.txt` (cleared each iteration). Log it for judges:

```bash
python3 agent/agent.py log-human --type PROMPT_EDIT --what "..."
```

**Readiness benchmark** (checkpoint checklist):

```bash
python3 benchmark.py
```

**Monitor UI** (live logs):

```bash
python3 log_server.py
# http://127.0.0.1:8765/index.html
```

See [docs/MONITOR_UI.md](docs/MONITOR_UI.md).

**If Ollama is slow or times out:** warm up with `ollama run qwen2.5-coder:7b`, then run the agent. Default `request_timeout_seconds` is **1200** in `agent/config.yaml`. macOS `MallocStackLogging` noise is harmless — `unset MallocStackLogging` optional.

Do **not** set `OPENAI_API_KEY` or `ANTHROPIC_API_KEY` — the agent refuses paid APIs.

**Windows:** use `py -3` instead of `python3`. See [docs/RUN_AND_TEST.md](docs/RUN_AND_TEST.md).

### Practice only: calculator in `knit.py` (mock spec)

Not the submission task. Full walkthrough: [docs/TEST_CALCULATOR.md](docs/TEST_CALCULATOR.md).

```bash
cp secret_spec/MOCK_CALCULATOR_SPEC.md secret_spec/SECRET_SPEC.md
python3 agent/agent.py run --mode flexible --force-setup \
  "Build the CLI calculator from secret_spec/SECRET_SPEC.md in knit.py"
```

Restore real spec before hackathon runs: copy from [event repo `secret_spec/`](https://github.com/anavoronkova/42xNeedle_Hackathon/tree/main/secret_spec).

## Secret spec (released)

The hidden task is the **Knitting Compiler** — a `.knit` DSL, not a calculator. Materials live in `secret_spec/` (also mirrored from the [event repository](https://github.com/anavoronkova/42xNeedle_Hackathon/tree/main/secret_spec)).

To refresh from upstream:

```bash
# example: re-download into secret_spec/ (keep MOCK_*.md mocks)
curl -sL https://github.com/anavoronkova/42xNeedle_Hackathon/archive/refs/heads/main.tar.gz \
  | tar -xz --strip-components=2 '*/secret_spec/SECRET_SPEC.md' '*/secret_spec/public_tests' \
         '*/secret_spec/expected_outputs' '*/secret_spec/test_runner'
```

## Checkpoints

```bash
git tag -l 'agent-readiness*'
# agent-readiness-1945       → readiness @ 19:45
# agent-readiness-1945-final → later agent fixes
```

## Final submission (Friday 12:00)

Include:

- `knit.py` + `src/` (working `compile` per spec)
- `agent_manifest.json`
- `agent_logs/` (all logs + completed `final_report.md`)
- `README.md`, `requirements.txt`

Required command:

```bash
python3 knit.py compile <input_file>
```

## Team

| Field | Value |
|-------|-------|
| Team name | SPARK |
| Members | Kiruthika Murugananthan, Sreya Thota, Ran Mo, Pedro Castro |
| Checkpoint tag | `agent-readiness-1945` |

**Collaboration:** [docs/COLLABORATION.md](docs/COLLABORATION.md)

## Agent architecture

One Ollama model (`qwen2.5-coder:7b`), one loop in `agent/agent.py`.

### What is what

| Component | Purpose |
|-----------|---------|
| `knit.py` + `src/` | **Final product** — judges run `compile` |
| `secret_spec/test_runner/` | **Official tests** (150 public) — hackathon score |
| `run_tests.py` + `tests/` | **Team pytest** — fast smoke (4 tests) |
| `agent/agent.py` | Autonomous implement → test → repair loop |
| `agent_logs/` | Required audit trail |

### Loop

```text
setup (once): template plan.md + spec_summary.md  [or --llm-setup]
for each iteration (max 40):
  read pending_prompt.txt if present → inject operator instruction
  Phase 3 IMPLEMENT: Ollama + tools (read_file, write_file, bash, run_tests)
  Phase 4 TEST:     public_test_command (official runner; no LLM)
  if fail → append test output (+ optional --diagnose) → next iteration
```

`config_loader.py` auto-prefers `secret_spec/test_runner/run_tests.py` when present; `agent/config.yaml` sets the hackathon command explicitly.

### Task modes

| Mode | Tests | Builds |
|------|-------|--------|
| **`hackathon`** (default) | Official 150 via `test_runner` | Knitting compiler in `src/` |
| **`flexible`** | `py_compile` or `AGENT_VERIFY_COMMAND` | Any app in `knit.py` (practice) |

### Human interventions

Log every post-release action that affects the agent, environment, or solution:

```bash
python3 agent/agent.py log-human --type PROMPT_EDIT --what "..."
python3 agent/agent.py log-human --type MANUAL_CODE_EDIT --what "..."
```

See `agent_logs/human_interventions.log` for format. `PROMPT_EDIT` = `pending_prompt.txt` only (`Touched: no`). `MANUAL_CODE_EDIT` = you edited `src/` or restored a broken file (`Touched: yes`).

## Resources

- [Rules and agenda](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/RULES_AND_AGENDA.md)
- [Agent spec](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/AGENT_SPEC.md)
- [Submission rules](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/SUBMISSION.md)
- [Judging criteria](https://github.com/anavoronkova/42xNeedle_Hackathon/blob/main/JUDGING_CRITERIA.md)

## Submission checklist

- [ ] `python3 knit.py compile <input.knit>` emits spec-compliant JSON
- [ ] Official tests: `secret_spec/test_runner/run_tests.py --compiler "python3 knit.py" --suite public`
- [ ] `agent_manifest.json` filled (no secrets)
- [ ] All `agent_logs/*` populated with timestamps
- [ ] `human_interventions.log` documents steering and any manual restores
- [ ] `final_report.md` complete
- [ ] Tags pushed (`agent-readiness-1945`)
- [ ] No `.env`, `.venv/`, or API keys committed
