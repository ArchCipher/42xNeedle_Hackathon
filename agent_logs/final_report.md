# Final Report

## Team

Team name:

Team members:

Repository link:

Final submission commit hash:

---

## Final result

Public test score:

Hidden test score, if known after judging:

Final command to run the program:

```bash
# Example:
python3 solution.py compile <input_file>
```

Known limitations:

---

## Models used

Primary model:

Provider/runtime:

Additional models:

Paid frontier models used after hidden task release: yes/no

Copilot or paid IDE assistant used after hidden task release: yes/no

Institutional/work/school model quota used after hidden task release: yes/no

Notes:

Example:

```text
Primary model: qwen2.5-coder:7b
Provider/runtime: Ollama
Additional models: llama3.1:8b for reviewing failed test summaries
Paid frontier models used after hidden task release: no
Copilot or paid IDE assistant used after hidden task release: no
Institutional/work/school model quota used after hidden task release: no
```

---

## Agent architecture

Describe your agent setup.

Include:

- main loop structure;
- model call strategy;
- available tools;
- file editing method;
- test-running method;
- logging system;
- state/memory strategy, if any.

Diagram or pseudocode is welcome but not required.

---

## Tools available to the agent

List tools your agent could use.

Examples:

- read files;
- write/edit files;
- run shell commands;
- run public tests;
- inspect stdout/stderr/exit codes;
- use git;
- generate self-tests;
- summarize failures;
- rollback or restore previous state.

---

## Prompting strategy

Describe how you prompted the agent.

Include:

- initial post-reveal prompt;
- whether it worked in phases;
- how you prevented large random rewrites;
- how you asked it to use public test failures;
- any important prompt changes after reveal.

Reference `agent_logs/prompts.log` where useful.

---

## Implementation strategy

How did the agent approach the task?

Examples:

- implemented minimal CLI first;
- implemented valid cases first;
- added error handling later;
- used public tests by category;
- generated extra self-tests;
- patched failing groups one at a time.

---

## Test strategy

Public score progression:

```text
20:45 — 31/250
21:30 — 86/250
23:00 — 151/250
02:00 — 203/250
09:00 — 226/250
```

Main failing categories:

Self-generated tests:

Did public test improvements transfer to other cases?

---

## Human interventions

Summarize interventions after hidden task release.

If none:

```text
No human interventions after hidden task release.
```

If yes, summarize:

- number of interventions;
- types of interventions;
- whether final task code was touched directly;
- where details are logged.

Reference `agent_logs/human_interventions.log`.

---

## What worked

What parts of your agent setup were effective?

Examples:

- phased planning;
- small patches;
- category-based test fixing;
- self-generated tests;
- rollback strategy;
- command-output parsing;
- prompt templates.

---

## What failed

What broke or underperformed?

Examples:

- model misunderstood the spec;
- repeated same patch;
- broke passing tests;
- failed to parse test output;
- got stuck in a loop;
- generated code with debug stdout;
- overfit public tests.

Be honest. Failure analysis is part of the score. Yes, finally, suffering has academic value.

---

## Most interesting failure mode

Describe one concrete failure that taught you something.

Include:

- what happened;
- how you noticed;
- what the agent did;
- what humans did, if anything;
- whether it was fixed.

---

## What you would improve

If you had another day, what would you improve?

Examples:

- better planner;
- stricter patch size limits;
- better test-output summarizer;
- rollback mechanism;
- model routing;
- self-test generation;
- logging automation;
- clearer stop condition.

---

## Final notes

Anything judges should know before reviewing your submission:

