# Run and test guide (Windows + Linux)

## Setup (once)

```powershell
cd E:\Needle_42\Compiler
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
ollama serve
ollama pull qwen2.5-coder:7b
```

Copy `SECRET_SPEC.md` into `secret_spec/` when the hackathon releases it.

---

## Compiler (Role 2)

| Command | Purpose |
|---------|---------|
| `py -3 knit.py compile <file>` | v1 submission path (stub until `src/` is done) |
| `py -3 knit.py compile-v2 <file>` | v2 pipeline (works now) |
| `py -3 main.py compile-v2 examples/hello.knit` | same as above via `main.py` |

**v2 test:**

```powershell
py -3 knit.py compile-v2 examples\hello.knit
# expect exit 0, stdout "Hello Knit", file examples\hello.knit.out.json
```

---

## Agent (Role 1) — where to put your prompt

**Option A — inline:**

```powershell
py -3 agent\agent.py run "Read secret_spec/SECRET_SPEC.md and implement knit.py in src/"
```

**Option B — environment variable:**

```powershell
$env:AGENT_TASK = "Your task here"
py -3 agent\agent.py run
```

**Option C — interactive:** `py -3 agent\agent.py run` then type at `Task:`.

**Print checklist before spec drops (no Ollama):**

```powershell
py -3 agent\agent.py plan
```

**Default hidden-task prompt (press Enter at Task: or use run-once):**

```powershell
py -3 agent\agent.py run-once
```

**Single iteration with custom prompt:**

```powershell
py -3 agent\agent.py run-once "Read secret_spec/SECRET_SPEC.md and implement row_expansion first"
```

**Health check:**

```powershell
py -3 agent\agent.py doctor
```

Logs: `agent_logs\` (`prompts.log`, `decisions.log`, `commands.log`, `test_runs.log`, `errors.log`).

---

## Config

- Model / iterations: `agent\config.yaml`
- Test command: auto-uses current Python (`sys.executable`); rewrites `python3` on load
- Override Python: `$env:AGENT_PYTHON = "py -3"`

When `secret_spec/test_runner/run_tests.py` exists, the agent switches to the public runner automatically.

---

## Quick test script

```powershell
.\scripts\smoke_test.ps1
```
