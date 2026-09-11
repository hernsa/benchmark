"""Function-call evaluation (BFCL style): tool name + argument matching.

Expected config in task YAML::

    function_call:
      function: get_weather
      args: {city: Paris, unit: celsius}
      strict: false          # penalize extra arguments

or, for parallel calls::

    function_call:
      calls:
        - {function: get_weather, args: {city: Paris}}
        - {function: get_weather, args: {city: Tokyo}}

Scoring per call: wrong/missing tool name -> 0; otherwise
40 (name) + 60 * (matched expected args / total expected args).
With ``strict: true``, extra arguments shrink the argument score.
"""

import json
import re


def extract_json(text: str):
    """Extract the first JSON value (object or array) from text."""
    fence = re.search(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            pass
    starts = [i for i in (text.find("{"), text.find("[")) if i != -1]
    if not starts:
        return None
    start = min(starts)
    depth = 0
    in_string = False
    escaped = False
    for i in range(start, len(text)):
        ch = text[i]
        if in_string:
            if escaped:
                escaped = False
            elif ch == "\\":
                escaped = True
            elif ch == '"':
                in_string = False
            continue
        if ch == '"':
            in_string = True
        elif ch in "{[":
            depth += 1
        elif ch in "}]":
            depth -= 1
            if depth == 0:
                try:
                    return json.loads(text[start : i + 1])
                except json.JSONDecodeError:
                    return None
    return None


def _score_call(expected_fn, expected_args, actual, strict: bool) -> float:
    if not isinstance(actual, dict):
        return 0.0
    name = actual.get("name", actual.get("function"))
    args = actual.get("arguments", actual.get("args", {}))
    if not isinstance(args, dict):
        args = {}
    if expected_fn is not None and name != expected_fn:
        return 0.0
    if not expected_args:
        return 100.0
    matched = sum(1 for k, v in expected_args.items() if k in args and args[k] == v)
    arg_score = matched / len(expected_args)
    if strict and len(args) > len(expected_args):
        arg_score *= len(expected_args) / len(args)
    return round(40.0 + 60.0 * arg_score, 1)


def score(task, output: str) -> float:
    cfg = task.eval.get("function_call", {})
    strict = bool(cfg.get("strict", False))
    parsed = extract_json(output)

    if "calls" in cfg:
        expected = cfg["calls"]
        actual_list = parsed if isinstance(parsed, list) else [parsed]
        scores = []
        for i, call in enumerate(expected):
            actual = actual_list[i] if i < len(actual_list) else None
            scores.append(
                _score_call(call.get("function"), call.get("args", {}), actual, strict)
            )
        return round(sum(scores) / len(scores), 1) if scores else 0.0

    return _score_call(cfg.get("function"), cfg.get("args", {}), parsed, strict)
