"""Data models shared across the benchmark."""

from dataclasses import dataclass, field


@dataclass
class Task:
    id: str
    title: str
    category: str
    difficulty: str = "easy"
    prompt: str = ""
    expected_output: str | None = None
    eval: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)


@dataclass
class TaskResult:
    task_id: str
    category: str
    difficulty: str = "easy"
    output: str = ""
    scores: dict[str, float] = field(default_factory=dict)
    total: float = 0.0
    passed: bool = False
    error: str | None = None
