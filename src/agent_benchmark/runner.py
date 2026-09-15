"""Run tasks against a model adapter and collect results."""

import logging

from .evaluators import evaluate, weighted_total
from .models import TaskResult

logger = logging.getLogger(__name__)


def run(tasks, adapter, threshold: float = 70.0) -> list[TaskResult]:
    results = []
    for task in tasks:
        try:
            output = adapter.generate(task)
            scores = evaluate(task, output)
            total = weighted_total(task, scores) if scores else 0.0
            results.append(
                TaskResult(
                    task_id=task.id,
                    category=task.category,
                    difficulty=task.difficulty,
                    output=output,
                    scores=scores,
                    total=total,
                    passed=total >= threshold,
                )
            )
        except Exception as exc:  # noqa: BLE001 — one bad task must not kill the run
            logger.warning("Task %s failed: %s: %s", task.id, type(exc).__name__, exc)
            results.append(
                TaskResult(
                    task_id=task.id,
                    category=task.category,
                    difficulty=task.difficulty,
                    output="",
                    scores={},
                    total=0.0,
                    passed=False,
                    error=f"{type(exc).__name__}: {exc}",
                )
            )
    return results
