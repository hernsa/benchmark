"""Basic code-quality scoring (compiles + length penalty)."""

from .base import extract_code


def score(task, output: str) -> float:
    code = extract_code(output)
    try:
        compile(code, "<output>", "exec")
    except (SyntaxError, ValueError):
        return 0.0
    s = 100.0
    if len(output) > 4000:
        s -= 20.0
    return max(s, 0.0)
