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
    output: str
    scores: dict[str, float]
    total: float
    passed: bool
