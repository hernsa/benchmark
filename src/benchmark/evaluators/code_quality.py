from ..models import Task


def score(task: Task, output: str) -> float:
    try:
        compile(output, "<output>", "exec")
    except (SyntaxError, ValueError):
        return 0.0
    s = 100.0
    if len(output) > 4000:
        s -= 20.0
    return max(s, 0.0)
