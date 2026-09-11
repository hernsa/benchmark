"""Final-answer extraction and comparison (GSM8K style).

Tasks end their prompt with a required marker (default ``#### <answer>``);
the evaluator extracts it and compares against the target, either as a
normalized string or as a number.
"""

import re

from .base import normalize_answer


def _to_number(text: str):
    cleaned = str(text).replace("$", "").replace("%", "").replace(",", "").strip()
    try:
        return float(cleaned)
    except ValueError:
        return None


def score(task, output: str) -> float:
    cfg = task.eval.get("final_answer", {})
    target = str(cfg.get("target", task.expected_output or ""))
    pattern = cfg.get("regex", r"####\s*(.+)")
    mode = cfg.get("mode", "exact")
    fallback = cfg.get("fallback", "last_line")

    m = re.search(pattern, output, re.MULTILINE)
    if m:
        candidate = m.group(1) if m.groups() else m.group(0)
    elif fallback == "last_line":
        lines = [ln for ln in output.strip().splitlines() if ln.strip()]
        candidate = lines[-1] if lines else ""
    else:
        return 0.0

    if mode == "numeric":
        got, want = _to_number(candidate), _to_number(target)
        if got is None or want is None:
            return 0.0
        return 100.0 if abs(got - want) < 1e-6 else 0.0
    return 100.0 if normalize_answer(candidate) == normalize_answer(target) else 0.0
