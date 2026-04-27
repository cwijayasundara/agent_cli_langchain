---
name: writing-evals
description: Use when adding eval examples or evaluators to this project.
---

# Writing Evals

- **Add an example:** append a JSON line to `evals/datasets/smoke.jsonl` (or create a new `.jsonl` file).
- **Add an evaluator:** define a function in `evals/evaluators.py` and append it to `EVALUATORS`.
- **Run:** `lcagents eval run`. Smoke-only: `lcagents eval run --smoke`.
- **Compare:** `lcagents eval compare evals/results/A.json evals/results/B.json`.

`LANGSMITH_API_KEY` must be set.
