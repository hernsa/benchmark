"""Evaluator registry: each configured evaluator maps to score(task, output) -> 0..100."""

import logging

from . import code_quality, exact_match, final_answer, function_call, json_match, pytest_eval
from .base import EvaluationError  # noqa: F401 — re-exported for consumers

logger = logging.getLogger(__name__)

_EVALUATORS = {
    "exact_match": exact_match.score,
    "pytest": pytest_eval.score,
    "code_quality": code_quality.score,
    "final_answer": final_answer.score,
    "function_call": function_call.score,
    "json_match": json_match.score,
}


def evaluate(task, output: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for name in (task.eval or {}):
        fn = _EVALUATORS.get(name)
        if fn is None:
            logger.warning(
                "Task %s: unknown evaluator %r (known: %s) — skipping",
                task.id,
                name,
                ", ".join(sorted(_EVALUATORS)),
            )
            continue
        scores[name] = float(fn(task, output))
    return scores


def weighted_total(task, scores: dict[str, float]) -> float:
    if not scores:
        return 0.0
    total_weight = 0.0
    weighted = 0.0
    for name, value in scores.items():
        cfg = (task.eval or {}).get(name, {}) or {}
        w = cfg.get("weight", 1.0)
        if isinstance(w, bool) or not isinstance(w, (int, float)):
            raise ValueError(
                f"Task {task.id}: evaluator {name!r} weight must be a number, got {w!r}"
            )
        total_weight += float(w)
        weighted += float(value) * float(w)
    if total_weight == 0:
        return 0.0
    return weighted / total_weight
