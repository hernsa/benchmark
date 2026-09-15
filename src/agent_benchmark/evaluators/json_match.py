"""Deep JSON comparison scoring."""

from .function_call import extract_json


def _flatten(obj, prefix: str = "$") -> dict:
    """Flatten nested dicts into {"$path": leaf} pairs. Lists/tuples stay leaves."""
    if isinstance(obj, dict):
        if not obj:
            return {prefix: {}}
        flat = {}
        for k, v in obj.items():
            flat.update(_flatten(v, f"{prefix}.{k}"))
        return flat
    return {prefix: obj}


def score(task, output: str) -> float:
    cfg = task.eval.get("json_match", {}) or {}
    expected = cfg.get("expected")
    parsed = extract_json(output)
    if expected is None or parsed is None:
        return 0.0
    if isinstance(expected, dict) and isinstance(parsed, dict):
        leaves_expected = _flatten(expected)
        leaves_parsed = _flatten(parsed)
        paths = set(leaves_expected) | set(leaves_parsed)
        if not paths:
            return 100.0
        matched = sum(
            1
            for p in paths
            if p in leaves_expected and p in leaves_parsed and leaves_expected[p] == leaves_parsed[p]
        )
        return round(100.0 * matched / len(paths), 1)
    return 100.0 if parsed == expected else 0.0
