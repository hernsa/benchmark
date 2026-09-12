"""Exact-match scoring."""

from .base import EvaluationError, normalize


def score(task, output: str) -> float:
    cfg = task.eval.get("exact_match", {}) or {}
    raw = cfg.get("target", task.expected_output)
    if raw is None:
        raise EvaluationError(
            f"exact_match: no target for task {task.id!r} "
            "(set eval.exact_match.target or task.expected_output)"
        )
    target = str(raw)
    source = cfg.get("source", "last_line")
    if source == "demo":
        candidate = normalize(output)
    else:
        lines = [ln.strip() for ln in output.strip().splitlines() if ln.strip()]
        candidate = lines[-1] if lines else ""
    return 100.0 if candidate == normalize(target) else 0.0
