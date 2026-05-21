# Test: calculator in `knit.py` (flexible mode)

Uses the **minimal** mock spec [`secret_spec/MOCK_CALCULATOR_SPEC.md`](../secret_spec/MOCK_CALCULATOR_SPEC.md) — on purpose, not detailed.

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
# 5
echo $?   # 0
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
