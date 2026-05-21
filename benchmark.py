#!/usr/bin/env python3
"""Quick agent readiness benchmark. Run this and compare scores with teammates.
Usage: python3 benchmark.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).parent

# Use venv python if available, otherwise current interpreter
_venv_py = ROOT / ".venv" / "bin" / "python3"
PY = str(_venv_py) if _venv_py.exists() else sys.executable

PASS = "\033[92mPASS\033[0m"
FAIL = "\033[91mFAIL\033[0m"
score = 0
total = 0


def check(label, points, condition, detail=""):
    global score, total
    total += points
    ok = bool(condition)
    if ok:
        score += points
    status = PASS if ok else FAIL
    suffix = f"  ({detail})" if detail and not ok else ""
    print(f"  [{status}] {label:50s} +{points}{suffix}")
    return ok


def run(cmd, timeout=15):
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=ROOT)
        return r.returncode, r.stdout + r.stderr
    except Exception as e:
        return 1, str(e)


print("\n=== Agent Readiness Benchmark ===\n")

# --- Required files (20 pts) ---
print("Required files:")
check("README.md exists",          3, (ROOT / "README.md").exists())
check("requirements.txt exists",   3, (ROOT / "requirements.txt").exists())
check("agent_manifest.json exists",3, (ROOT / "agent_manifest.json").exists())
check("knit.py exists",            3, (ROOT / "knit.py").exists())
check("agent/agent.py exists",     4, (ROOT / "agent" / "agent.py").exists())
check("run_tests.py exists",       4, (ROOT / "run_tests.py").exists())

# --- Log files (21 pts) ---
print("\nLog files (judges need all of these):")
logs = ["prompts.log", "decisions.log", "commands.log",
        "test_runs.log", "errors.log", "human_interventions.log", "final_report.md"]
for log in logs:
    p = ROOT / "agent_logs" / log
    check(f"agent_logs/{log}",     3, p.exists() and p.stat().st_size > 0,
          "missing or empty")

# --- Log quality (15 pts) ---
print("\nLog quality:")
decisions = (ROOT / "agent_logs" / "decisions.log")
commands  = (ROOT / "agent_logs" / "commands.log")
test_runs = (ROOT / "agent_logs" / "test_runs.log")
d_entries = decisions.read_text().count("[20") if decisions.exists() else 0
c_entries = commands.read_text().count("[20")  if commands.exists()  else 0
t_entries = test_runs.read_text().count("[20") if test_runs.exists() else 0
check("decisions.log has 10+ timestamped entries",  5, d_entries >= 10, f"found {d_entries}")
check("commands.log has 10+ timestamped entries",   5, c_entries >= 10, f"found {c_entries}")
check("test_runs.log has 3+ timestamped entries",   5, t_entries >= 3,  f"found {t_entries}")

# --- agent_manifest.json filled (10 pts) ---
print("\nModel disclosure:")
mf = ROOT / "agent_manifest.json"
if mf.exists():
    try:
        data = json.loads(mf.read_text())
        check("primary_model declared",            4, data.get("primary_model", ""))
        check("provider declared",                 3, data.get("provider", ""))
        check("paid_frontier_models=false",        3,
              data.get("paid_frontier_models_used_after_spec_release") == False,
              "field missing or true")
    except Exception:
        check("agent_manifest.json is valid JSON", 10, False, "parse error")
else:
    check("agent_manifest.json readable",         10, False)

# --- Tests pass (15 pts) ---
print("\nTest suite:")
code, out = run(f'"{PY}" run_tests.py', timeout=30)
passed = "passed" in out
any_result = "passed" in out or "failed" in out or "error" in out
check("run_tests.py runs without crash",           5, any_result, "crashed")
check("all public tests passing",                 10, code == 0 and passed,
      f"exit={code}")

# --- Agent boots (10 pts) ---
print("\nAgent boot:")
code2, out2 = run(f'"{PY}" agent/agent.py plan', timeout=15)
check("agent/agent.py plan runs without error",   10, code2 == 0,
      out2[:80] if code2 != 0 else "")

# --- Checkpoint tag (9 pts) ---
print("\nCheckpoint:")
code3, out3 = run("git tag --list agent-readiness-1945")
check("git tag agent-readiness-1945 exists",       9, "agent-readiness-1945" in out3,
      "run: git tag agent-readiness-1945")

# --- Summary ---
pct = int(100 * score / total)
print(f"\n{'='*45}")
print(f"  SCORE: {score}/{total}  ({pct}%)")
print(f"{'='*45}\n")
if pct >= 85:
    print("  Excellent — ready for the reveal.")
elif pct >= 60:
    print("  Good — fix the FAILs above before 20:00.")
else:
    print("  Needs work — check the FAILs above now.")
print()
