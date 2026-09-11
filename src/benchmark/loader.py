from pathlib import Path

import yaml

from .models import Task


def load_tasks(paths: list[str | Path]) -> list[Task]:
    found: list[Task] = []
    for p in paths:
        path = Path(p)
        files = sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
        for f in files:
            if f.name.startswith("_"):
                continue
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            for d in items:
                found.append(
                    Task(
                        id=str(d["id"]),
                        title=d.get("title", d["id"]),
                        category=d.get("category", "general"),
                        difficulty=d.get("difficulty", "easy"),
                        prompt=d.get("prompt", ""),
                        expected_output=d.get("expected_output"),
                        eval=d.get("eval", {}) or {},
                        meta=d.get("meta", {}) or {},
                    )
                )
    return found
