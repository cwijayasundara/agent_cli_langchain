---
name: lcagents-langsmith-evals
description: Use when authoring eval datasets, evaluators, or interpreting the output of `lcagents eval run` and `lcagents eval compare`.
---

# lcagents Evals

Evals run via LangSmith. `LANGSMITH_API_KEY` must be set.

## Datasets

`evals/datasets/*.jsonl` — one JSON object per line:

    {"input": {"messages": [{"role": "user", "content": "..."}]}, "reference": "optional"}

`smoke.jsonl` is the 3-row gate that `lcagents deploy` runs as a pre-flight.

## Evaluators

`evals/evaluators.py` exports `EVALUATORS` — a list of LangSmith evaluator callables. Each takes `(run, example)` and returns `{"key": str, "score": float, "comment": str?}`.

## Running

- `lcagents eval run` — full
- `lcagents eval run --smoke` — smoke only
- `lcagents eval compare evals/results/A.json evals/results/B.json` — metric deltas

## Reading `compare`

Look at the `delta` column. `+` means metric went up. Whether that's good depends on the metric: `+` is good for `correctness`, bad for `latency`/`token_cost`.
