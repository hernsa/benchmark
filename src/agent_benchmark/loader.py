"""Load benchmark tasks from YAML files."""

import logging
from pathlib import Path

import yaml

from .models import Task

logger = logging.getLogger(__name__)

_TASK_EXTENSIONS = (".yaml", ".yml")


def _validate_eval(task_id: str, data: dict, path: Path) -> None:
    """Raise ValueError when an evaluator config is missing required keys."""
    eval_cfg = data.get("eval", {}) or {}
    if not isinstance(eval_cfg, dict):
        raise ValueError(f"{path}: task {task_id!r}: 'eval' must be a mapping")
    for name, cfg in eval_cfg.items():
        has_target = isinstance(cfg, dict) and (
            cfg.get("target") is not None or data.get("expected_output") is not None
        )
        if name == "exact_match" and not has_target:
            raise ValueError(
                f"{path}: task {task_id!r}: exact_match needs "
                "eval.exact_match.target or expected_output"
            )
        elif name == "final_answer" and not has_target:
            raise ValueError(
                f"{path}: task {task_id!r}: final_answer needs "
                "eval.final_answer.target or expected_output"
            )
        elif name == "pytest" and not (isinstance(cfg, dict) and cfg.get("test_code")):
            raise ValueError(
                f"{path}: task {task_id!r}: pytest eval needs eval.pytest.test_code"
            )
        elif name == "json_match" and not (isinstance(cfg, dict) and "expected" in cfg):
            raise ValueError(
                f"{path}: task {task_id!r}: json_match eval needs eval.json_match.expected"
            )
        elif name == "function_call" and not (
            isinstance(cfg, dict) and (cfg.get("function") or cfg.get("calls"))
        ):
            raise ValueError(
                f"{path}: task {task_id!r}: function_call needs "
                "eval.function_call.function or .calls"
            )


def load_tasks(paths) -> list[Task]:
    tasks: list[Task] = []
    seen: set[str] = set()
    for p in paths:
        path = Path(p)
        if path.is_dir():
            files = sorted(
                f for f in path.rglob("*") if f.suffix.lower() in _TASK_EXTENSIONS
            )
        elif path.exists():
            files = [path]
        else:
            raise FileNotFoundError(f"Task path not found: {path}")
        for f in files:
            if f.name.startswith("_"):
                continue
            try:
                data = yaml.safe_load(f.read_text(encoding="utf-8"))
            except yaml.YAMLError as exc:
                raise ValueError(f"Invalid YAML in {f}: {exc}") from exc
            items = data if isinstance(data, list) else [data]
            for d in items:
                if not isinstance(d, dict):
                    raise ValueError(
                        f"{f}: task entry must be a mapping, got {type(d).__name__}"
                    )
                if "id" not in d:
                    raise ValueError(f"{f}: task is missing required field 'id'")
                task_id = str(d["id"])
                if task_id in seen:
                    logger.warning(
                        "Duplicate task id %r in %s (keeping first occurrence)",
                        task_id,
                        f,
                    )
                    continue
                seen.add(task_id)
                _validate_eval(task_id, d, f)
                tasks.append(
                    Task(
                        id=task_id,
                        title=d.get("title", task_id),
                        category=d.get("category", "general"),
                        difficulty=d.get("difficulty", "easy"),
                        prompt=d.get("prompt", ""),
                        expected_output=d.get("expected_output"),
                        eval=d.get("eval", {}) or {},
                        meta=d.get("meta", {}) or {},
                    )
                )
    return tasks
