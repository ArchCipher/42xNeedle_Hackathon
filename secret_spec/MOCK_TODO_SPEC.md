# Mock task — TODO app (intentionally brief)

> **Test only.** Copy to `SECRET_SPEC.md` to run the agent against this spec:
> `cp secret_spec/MOCK_TODO_SPEC.md secret_spec/SECRET_SPEC.md`

## Product

A **website for to do list creation**. The program users run is **`knit.py`** (helpers may live in `src/`).

## Behavior (minimal)

- Support add, modify, delete to do list.
- be able to set the phase- backlog, in progress, done

## Interface (not fully specified — agent must decide)

Design a reasonable simple website and give a link to the website for the todo app created.
Document usage in a short comment at the top of `knit.py`.

## Done when

- `python3 knit.py` runs without syntax errors.
- A few manual cases work (add, modify, delete to do list).
- create 2 todos: create an agent, create a secret task.
