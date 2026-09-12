"""File-backed adapter: read model outputs from {dir}/{task_id}.txt."""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


class FileAdapter:
    def __init__(self, directory: str = "outputs"):
        self.directory = Path(directory)
        self.name = "file"

    def generate(self, task) -> str:
        f = self.directory / f"{task.id}.txt"
        if not f.exists():
            logger.warning("No output file for task %s: %s", task.id, f)
            return ""
        return f.read_text(encoding="utf-8")
