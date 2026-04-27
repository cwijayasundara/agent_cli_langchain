"""Run LangSmith evals for this project.

Invoked by `lcagents eval run`, but also runnable directly: `python evals/run.py`.
"""
from __future__ import annotations

import argparse
import json
import os
from datetime import UTC, datetime
from pathlib import Path

from agent.agent import agent
from evals.evaluators import EVALUATORS

ROOT = Path(__file__).resolve().parent
DATASETS = ROOT / "datasets"
RESULTS = ROOT / "results"


def _load_dataset(name: str) -> list[dict]:
    path = DATASETS / f"{name}.jsonl"
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--smoke", action="store_true", help="Run only the smoke dataset.")
    args = parser.parse_args()

    if not os.getenv("LANGSMITH_API_KEY"):
        print("ERROR: LANGSMITH_API_KEY is not set.")
        return 2

    datasets = ["smoke"] if args.smoke else [p.stem for p in DATASETS.glob("*.jsonl")]
    RESULTS.mkdir(exist_ok=True)
    results: dict[str, list[dict]] = {}

    try:
        from langsmith import evaluate as run_evaluation
    except ImportError:
        print("ERROR: langsmith not installed. Run `lcagents install`.")
        return 2

    for ds_name in datasets:
        examples = _load_dataset(ds_name)
        ds_results = run_evaluation(
            lambda inp: agent.invoke(inp),
            data=examples,
            evaluators=EVALUATORS,
            experiment_prefix=f"{ds_name}-",
        )
        results[ds_name] = list(ds_results)

    out = RESULTS / f"{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}.json"
    out.write_text(json.dumps(results, default=str, indent=2), encoding="utf-8")
    print(f"Wrote {out}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
