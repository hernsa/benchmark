"""Run the same tasks against several models and keep per-model summaries."""

from .report import summarize
from .runner import run as run_tasks


def compare_models(tasks, adapters: list, threshold: float = 70.0) -> dict:
    models = {}
    for adapter in adapters:
        results = run_tasks(tasks, adapter, threshold=threshold)
        summary = summarize(results)
        summary["meta"] = {"adapter": adapter.name, "threshold": threshold}
        models[adapter.name] = summary
    order = [a.name for a in adapters]
    return {"threshold": threshold, "model_order": order, "models": models}
