# Test: calculator in `knit.py` (flexible mode)

Uses the **minimal** mock spec [`secret_spec/MOCK_CALCULATOR_SPEC.md`](../secret_spec/MOCK_CALCULATOR_SPEC.md) — on purpose, not detailed.

## What changed (why early runs “passed” but `add` failed)

Several agent fixes landed in commit `e0f5866` (and earlier `499d847`). Without them, the loop could report **PASSED** while `knit.py` was still the old compiler.

| Problem (before) | Symptom | Fix (now) |
|------------------|---------|-----------|
| **False pass** | Agent said done; `python3 knit.py add 2 3` → `invalid choice: 'add'` | Flexible mode + mock calculator spec uses **behavior** check: `python3 knit.py add 2 3` must exit 0 (not `py_compile` only). |
| **Tool JSON not run** | Model printed `{"name": "read_file", ...}` or ` ```json ... ``` ` but no `read_file` / `write_file` in logs | `agent/ollama_client.py` parses JSON tool calls from markdown fences and runs them. |
| **Broken test command** | Crash: `.../python3/bin//.../python3` | `agent/config_loader.py` only rewrites a leading `python3` token, not paths inside `sys.executable`. |
| **Slow / timeout setup** | Hung on “Phase 1 — Read specification” | Default setup is **template** (`plan.md` / `spec_summary.md`); optional `--llm-setup` only if you want one LLM planning call. |
| **Model wrote docs not code** | First `write_file` was markdown usage text → `SyntaxError` | Iteration **failed** the real verify command; repair message + next iteration produced real Python in `knit.py`. |

**Successful run pattern (what you should see in the terminal):**

1. Iteration 1 — test fails (still `compile` / `compile-v2`).
2. Iteration 2 — `write_file knit.py` with Python, `bash: python3 knit.py add 2 3` → `5.0`, exit 0.
3. Phase 4 — `RESULT: PASSED` with `5.0` in output.
4. Manual check: `python3 knit.py add 2 3` → `5.0` (you confirmed `mul` / `div` too).

**Files touched for this test path:** `agent/ollama_client.py`, `agent/config_loader.py`, `agent/agent.py`, `agent/config.yaml` (`task_mode: flexible` or `--mode flexible`).

## 1. Install and Ollama

```bash
ollama serve
ollama pull qwen2.5-coder:7b
python3 agent/agent.py doctor
```

Optional warm-up (avoids long first call):

```bash
ollama run qwen2.5-coder:7b
# exit after it responds
```

## 2. Activate the mock spec

```bash
cp secret_spec/MOCK_CALCULATOR_SPEC.md secret_spec/SECRET_SPEC.md
```

## 3. Run the agent

```bash
python3 agent/agent.py run --mode flexible --force-setup \
  "Build the CLI calculator from secret_spec/SECRET_SPEC.md in knit.py"
```

(This is the same command as the **Teammate smoke test** block in the root [README.md](../README.md).)

Single iteration (smoke):

```bash
python3 agent/agent.py run-once --mode flexible --force-setup \
  "Build the CLI calculator in knit.py per the mock spec"
```

## 4. Check results yourself

**Success looks like:**

```bash
python3 knit.py add 2 3
# 5.0
echo $?   # 0
python3 knit.py mul 15 3
# 45.0
python3 knit.py div 15 3
# 5.0
```

**Failure (agent did not build a calculator yet):**

```text
invalid choice: 'add' (choose from 'compile', 'compile-v2')
```

More checks:

```bash
python3 knit.py mul 4 5
python3 knit.py div 10 0    # expect non-zero exit
```

The agent loop only stops when `knit.py add 2 3` exits 0 (auto when mock spec mentions “calculator”).

Logs: `agent_logs/decisions.log`, `agent_logs/plan.md`, `agent_logs/commands.log`.

## Save the calculator (and teammate experiments)

Before another flexible run, copy the working app:

```bash
cp knit.py backups/knit_calculator.py   # already in repo as reference
cp knit.py backups/knit_<your_app>.py # your experiments
```

| What | Where |
|------|--------|
| Saved `knit.py` apps | [`backups/`](../backups/README.md) |
| Manual test notes | [`tests/manual/`](../tests/manual/README.md) |
| Shared pytest | [`tests/test_knit.py`](../tests/test_knit.py) |
| Agent logs | [`agent_logs/`](../agent_logs/) |

Restore compiler CLI: `git restore knit.py`

## Optional: stricter auto-verify

```bash
export AGENT_VERIFY_COMMAND='python3 knit.py add 2 3'
python3 agent/agent.py run-once --mode flexible --force-setup \
  "Build calculator in knit.py; add must print 5"
```

The loop passes when that command exits 0.

## Restore hackathon spec later

Replace `secret_spec/SECRET_SPEC.md` with the real file from the event repo when the hidden task drops.

```bash
# after 20:00
python3 agent/agent.py run --mode hackathon --force-setup
```
