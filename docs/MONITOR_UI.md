# SPRK Agent Monitor UI

Real-time dashboard for overnight hackathon agent monitoring.

## Run (required)

`fetch()` and POST need HTTP — do **not** open `index.html` as `file://`.

```powershell
cd E:\Needle_42\Compiler
py -3 log_server.py
```

Open: **http://127.0.0.1:8765/index.html**

## Features

- Live log feed (all `agent_logs/*.log`) — refreshes every 3s
- Pipeline step detection from `decisions.log`
- Score progression + failure category table from `test_runs.log`
- Syntax-highlighted `solution.py` viewer
- Control tab: queue prompts → `agent_logs/pending_prompt.txt`
- Human intervention logging (hackathon requirement)
- START / STOP buttons

## Agent integration

On each iteration the agent reads and clears `agent_logs/pending_prompt.txt` if present.

## Keyboard shortcuts

| Key | Action |
|-----|--------|
| Ctrl+Enter | Send prompt |
| Ctrl+K | Focus prompt box |
| Ctrl+1–7 | Switch tabs |
| Escape | Close modal / clear search |
| R | Force refresh |
