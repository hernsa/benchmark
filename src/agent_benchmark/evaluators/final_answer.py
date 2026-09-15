"""Final-answer scoring (regex extraction, numeric or text comparison)."""

import re

from .base import EvaluationError, normalize_answer

DEFAULT_PATTERN = r"####\s*(.+)"


def _compile_pattern(pattern: str):
    try:
        return re.compile(pattern, re.MULTILINE)
    except re.error as exc:
        raise EvaluationError(f"final_answer: invalid regex {pattern!r}: {exc}") from exc


def _to_number(text) -> float | None:
    """Pull the last number out of arbitrary text ('#### 80 km/h' -> 80.0)."""
    matches = re.findall(r"[-+]?\d[\d,]*(?:\.\d+)?", str(text))
    if not matches:
        return None
    return float(matches[-1].replace(",", ""))


def score(task, output: str) -> float:
    cfg = task.eval.get("final_answer", {}) or {}
    raw_target = cfg.get("target", task.expected_output)
    if raw_target is None:
        raise EvaluationError(
            f"final_answer: no target for task {task.id!r} "
            "(set eval.final_answer.target or task.expected_output)"
        )
    target = str(raw_target)
    pattern = cfg.get("regex", DEFAULT_PATTERN)
    mode = cfg.get("mode", "exact")
    fallback = cfg.get("fallback", "last_line")
    regex = _compile_pattern(pattern)
    m = regex.search(output)
    if m:
        candidate = str(m.group(1)) if m.groups() else m.group(0)
    elif fallback == "last_line":
        lines = [ln.strip() for ln in output.strip().splitlines() if ln.strip()]
        candidate = lines[-1] if lines else ""
    else:
        return 0.0

    if mode == "numeric":
        got = _to_number(candidate)
        want = _to_number(target)
        if got is None or want is None:
            return 0.0
        rel = cfg.get("rel_tolerance")
        if rel is not None:
            ok = abs(got - want) <= float(rel) * max(abs(want), 1.0)
        else:
            ok = abs(got - want) <= float(cfg.get("tolerance", 1e-6))
        return 100.0 if ok else 0.0
    return 100.0 if normalize_answer(candidate) == normalize_answer(target) else 0.0
