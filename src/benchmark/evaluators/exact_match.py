from ..models import Task
from .base import normalize


def score(task: Task, output: str) -> float:
    cfg = task.eval.get("exact_match", {})
    target = str(cfg.get("target", task.expected_output or ""))
    if cfg.get("source") == "demo":
        candidate = normalize(output)
    else:
        lines = [ln for ln in output.strip().splitlines() if ln.strip()]
        candidate = normalize(lines[-1]) if lines else ""
    return 100.0 if candidate == normalize(target) else 0.0
