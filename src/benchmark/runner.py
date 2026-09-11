from .adapters.base import ModelAdapter
from .evaluators import evaluate, weighted_total
from .models import Task, TaskResult


def run(
    tasks: list[Task], adapter: ModelAdapter, threshold: float = 70.0
) -> list[TaskResult]:
    results: list[TaskResult] = []
    for task in tasks:
        output = adapter.generate(task)
        scores = evaluate(task, output)
        total = weighted_total(task, scores) if scores else 0.0
        results.append(
            TaskResult(
                task_id=task.id,
                category=task.category,
                output=output,
                scores=scores,
                total=total,
                passed=total >= threshold,
            )
        )
    return results
