---
name: langchain-agents-langsmith-evals
description: Use when authoring eval datasets, writing evaluators, running evals against a LangChain / LangGraph / DeepAgents project, or comparing eval results between runs.
---

# LangSmith Evals

Use the `langsmith` Python SDK directly. There is no CLI wrapper — write a small `evals/run.py` and run it with `python evals/run.py`.

`LANGSMITH_API_KEY` must be set. `LANGSMITH_PROJECT` controls which project the trace lands in.

## Dataset shape

`evals/datasets/smoke.jsonl` — one JSON object per line:

```jsonl
{"input": {"messages": [{"role": "user", "content": "Say hello in one word."}]}, "reference": "Hi"}
{"input": {"messages": [{"role": "user", "content": "What is 2+2?"}]}, "reference": "4"}
```

`reference` is optional and only used by evaluators that compare against a known answer (correctness LLM-as-judge, exact-match, etc.).

## Evaluators

`evals/evaluators.py`:

```python
"""LangSmith evaluators. Each takes (run, example) and returns a result dict."""
from typing import Any

def correctness_llm_judge(run: Any, example: Any) -> dict[str, Any]:
    """LLM-as-judge against `example.outputs['reference']`."""
    # ... call an LLM with run.outputs and example.outputs['reference']
    return {"key": "correctness", "score": 0.9, "comment": "close enough"}

def trajectory(run: Any, example: Any) -> dict[str, Any]:
    """Did the expected tool calls fire?"""
    expected = example.outputs.get("expected_tools", [])
    actual = [c["name"] for c in run.outputs.get("tool_calls", [])]
    score = 1.0 if set(expected).issubset(actual) else 0.0
    return {"key": "trajectory", "score": score}

EVALUATORS = [correctness_llm_judge, trajectory]
```

## Runner

`evals/run.py`:

```python
"""Run LangSmith evals. Usage: python evals/run.py [--smoke]"""
import argparse, json, os
from datetime import UTC, datetime
from pathlib import Path

import langsmith
from agent.agent import agent
from evals.evaluators import EVALUATORS

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"
RESULTS = ROOT / "results"


def _load(name: str) -> list[dict]:
    path = DATASETS / f"{name}.jsonl"
    return [json.loads(l) for l in path.read_text("utf-8").splitlines() if l.strip()]


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    if not os.getenv("LANGSMITH_API_KEY"):
        print("ERROR: LANGSMITH_API_KEY is not set.")
        return 2

    datasets = ["smoke"] if args.smoke else [p.stem for p in DATASETS.glob("*.jsonl")]
    RESULTS.mkdir(exist_ok=True)
    results: dict[str, list[dict]] = {}

    for ds in datasets:
        examples = _load(ds)
        out = langsmith.evaluate(
            lambda inp: agent.invoke(inp),
            data=examples,
            evaluators=EVALUATORS,
            experiment_prefix=f"{ds}-",
        )
        results[ds] = list(out)

    out_path = RESULTS / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.write_text(json.dumps(results, default=str, indent=2), encoding="utf-8")
    print(f"Wrote {out_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

Run with: `python evals/run.py` (full) or `python evals/run.py --smoke` (smoke only).

## Comparing two runs

The `langsmith` UI is the best place to compare experiments side-by-side. For a quick CLI diff between two `evals/results/*.json` files, write a 30-line script that loads both and prints metric deltas — there's no built-in CLI for this.

## Suggested smoke pattern (for deploy gating)

Keep `evals/datasets/smoke.jsonl` small (3–5 rows) and fast (<60 s total). Run `python evals/run.py --smoke` before any deploy. **If smoke fails, fix the agent or the smoke dataset — never bypass.** This pattern is recommended but not enforced; the `langchain-agents-deploy` skill expects you to do it manually.
