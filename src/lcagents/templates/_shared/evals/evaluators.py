"""LangSmith evaluators for this project. Edit freely."""
from __future__ import annotations

from typing import Any


def correctness(run: Any, example: Any) -> dict[str, Any]:
    """Trivial pass-through; replace with an LLM-as-judge for real use."""
    return {"key": "correctness", "score": 1.0, "comment": "stub"}


EVALUATORS = [correctness]
