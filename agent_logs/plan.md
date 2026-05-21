# Implementation plan (template)

## Operator task
read the spec and write knit.py

## knit.py is the app
All user-facing behavior lives in knit.py (helpers in src/).

## Steps
1. Design CLI or UX for knit.py matching the operator task
2. Implement logic in knit.py and src/
3. bash: python3 knit.py <smoke args> until behavior matches task
4. run_tests (py_compile) after each meaningful change
