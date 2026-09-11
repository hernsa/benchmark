from ..models import Task
from . import code_quality, exact_match, pytest_eval

_EVALUATORS = {
    "exact_match": exact_match.score,
    "pytest": pytest_eval.score,
    "code_quality": code_quality.score,
}


def evaluate(task: Task, output: str) -> dict[str, float]:
    scores: dict[str, float] = {}
    for name, fn in _EVALUATORS.items():
        if name in (task.eval or {}):
            scores[name] = float(fn(task, output))
    return scores


def weighted_total(task: Task, scores: dict[str, float]) -> float:
    weights = [(task.eval.get(name, {}) or {}).get("weight", 1.0) for name in scores]
    if not weights or sum(weights) == 0:
        return 0.0
    return sum(s * w for s, w in zip(scores.values(), weights)) / sum(weights)
