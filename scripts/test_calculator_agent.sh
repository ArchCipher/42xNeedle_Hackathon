#!/usr/bin/env bash
# Quick test: mock calculator spec + flexible agent mode
set -euo pipefail
cd "$(dirname "$0")/.."

cp secret_spec/MOCK_CALCULATOR_SPEC.md secret_spec/SECRET_SPEC.md
echo "Using mock spec as secret_spec/SECRET_SPEC.md"

export AGENT_VERIFY_COMMAND="${AGENT_VERIFY_COMMAND:-python3 knit.py add 2 3}"

python3 agent/agent.py run-once --mode flexible --force-setup \
  "Build the CLI calculator from secret_spec/SECRET_SPEC.md in knit.py (use src/ if needed)."

echo ""
echo "Manual check:"
python3 -m py_compile knit.py
python3 knit.py add 2 3 || true
