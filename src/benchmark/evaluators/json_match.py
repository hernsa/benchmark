"""Structured-output evaluation: deep JSON comparison.

Parses the first JSON value in the output and compares it to the expected
value. Dicts are scored by matched keys over the union of keys; everything
else is binary.
"""

from .function_call import extract_json


def score(task, output: str) -> float:
    cfg = task.eval.get("json_match", {})
    expected = cfg.get("expected")
    parsed = extract_json(output)
    if parsed is None:
        return 0.0
    if isinstance(expected, dict) and isinstance(parsed, dict):
        keys = set(expected) | set(parsed)
        if not keys:
            return 100.0
        matched = sum(
            1 for k in keys if k in expected and k in parsed and expected[k] == parsed[k]
        )
        return round(100.0 * matched / len(keys), 1)
    return 100.0 if parsed == expected else 0.0
