from pathlib import Path

from ..models import Task


class FileAdapter:
    name = "file"

    def __init__(self, directory: str = "outputs"):
        self.directory = Path(directory)

    def generate(self, task: Task) -> str:
        f = self.directory / f"{task.id}.txt"
        return f.read_text(encoding="utf-8") if f.exists() else ""
