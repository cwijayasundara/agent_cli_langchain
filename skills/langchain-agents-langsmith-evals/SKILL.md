---
name: langchain-agents-langsmith-evals
description: Use when authoring eval datasets, writing evaluators, running evals against a LangChain / LangGraph / DeepAgents project, comparing eval results between runs, or writing unit/integration tests for an agent.
---

# Evals + Testing

Use the `langsmith` Python SDK directly. There is no CLI wrapper — write a small `evals/run.py` and run it with `python evals/run.py`. For per-test-function CI checks, use `pytest` with the `langsmith` pytest plugin.

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

## Suggested smoke pattern (for deploy gating)

Keep `evals/datasets/smoke.jsonl` small (3–5 rows) and fast (<60 s total). Run `python evals/run.py --smoke` before any deploy. **If smoke fails, fix the agent or the smoke dataset — never bypass.** This pattern is recommended but not enforced; the deploy skill expects you to do it manually.

## Comparing two runs

The `langsmith` UI is the best place to compare experiments side-by-side. For a quick CLI diff between two `evals/results/*.json` files, write a 30-line script that loads both and prints metric deltas — there's no built-in CLI for this.

---

# Testing strategies

The `langsmith` package ships a pytest plugin. Three layers of testing for a production agent:

## 1. Unit tests (no API calls)

Use `LLMToolEmulator` middleware to short-circuit tool execution, and a fake / mocked model:

```python
# tests/test_agent_unit.py
from langchain.agents import create_agent
from langchain.agents.middleware import LLMToolEmulator

def test_agent_handles_empty_input():
    agent = create_agent(
        model="claude-haiku-4-5",      # fastest available; or use a stub
        tools=[my_tool],
        middleware=[LLMToolEmulator()],   # tools return LLM-emulated outputs
    )
    result = agent.invoke({"messages": [{"role": "user", "content": "hi"}]})
    assert "messages" in result
```

For full hermetic unit tests with no LLM calls at all, mock `init_chat_model` or pass a `FakeChatModel` (`from langchain_core.language_models.fake import FakeChatModel`).

## 2. Integration tests (real LLM, hermetic tools)

Real model, real middleware, but tools mocked / point at sandboxes:

```python
# tests/test_agent_integration.py
import pytest
from agent.agent import agent

@pytest.mark.integration
def test_smoke_basic():
    result = agent.invoke({"messages": [{"role": "user", "content": "Say hi."}]})
    msg = result["messages"][-1]
    assert "hi" in str(msg.content).lower()
```

Run with `pytest -m integration`. Skip in CI without API keys; run locally or in a separately-credentialed CI step.

## 3. Trajectory + dataset tests via langsmith pytest plugin

```python
# tests/test_agent_trajectories.py
import pytest
from langsmith import testing as t

@t.expect(score_min=0.8, evaluator="correctness")
@pytest.mark.parametrize("example", [
    {"messages": [{"role": "user", "content": "What is 2+2?"}], "reference": "4"},
    {"messages": [{"role": "user", "content": "Capital of France?"}], "reference": "Paris"},
])
def test_basic_qa(example):
    from agent.agent import agent
    return agent.invoke({"messages": example["messages"]})
```

The plugin uploads each test result to LangSmith, runs the named evaluator(s), and fails the test if the score falls below the threshold. This is the recommended way to gate PRs on agent quality.

## Eval-as-monitor (production)

In production, the same evaluators that grade your dev runs can run continuously against live traces:

1. Set up an evaluator function in LangSmith UI.
2. Configure it to run on incoming traces (sampled or all).
3. Wire an alert when score drops below threshold.

This catches model drift, prompt rot, and gradual quality degradation that smoke evals don't see.

## Common eval gotchas

- LLM-as-judge evaluators are themselves non-deterministic. Run each example 3+ times and average, OR use a low-temperature judge model.
- Don't mix metric directions. `correctness` higher = better; `latency` higher = worse. Make this explicit in evaluator names so dashboards read correctly.
- Smoke datasets that are too large (>10 rows) become a deploy bottleneck. Keep them tight; rely on the full eval suite running async post-deploy for breadth.
- `langsmith.evaluate(...)` runs invocations in parallel by default. If your agent has rate-limited tools, set `max_concurrency=1` or accept that retries will fire.
