from typing import Protocol

from ..models import Task


class ModelAdapter(Protocol):
    name: str

    def generate(self, task: Task) -> str: ...
