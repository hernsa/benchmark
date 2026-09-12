"""Function-call scoring."""

import json
import re


def _try_json(text: str):
    try:
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return None


def _scan_from(text: str, start: int):
    """Parse a balanced {..}/[..] block starting at `start`; None if invalid."""
    open_char = text[start]
    close_char = "}" if open_char == "{" else "]"
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
            if depth == 0 and ch == close_char:
                return _try_json(text[start:i + 1])
    return None


def extract_json(text: str):
    """Best-effort JSON extraction.

    Order of attempts: fenced code blocks (last one first — models often show
    an example before the answer), then every '{' or '[' position in the raw
    text so prose like 'I'll call [tool] with {...}' still finds the object.
    """
    fences = re.findall(r"```(?:json)?\s*\n(.*?)```", text, re.DOTALL)
    for body in reversed(fences):
        val = _try_json(body.strip())
        if val is not None:
            return val
    for i, ch in enumerate(text):
        if ch in "{[":
            val = _scan_from(text, i)
            if val is not None:
                return val
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
    cfg = task.eval.get("function_call", {}) or {}
    strict = bool(cfg.get("strict", False))
    parsed = extract_json(output)
    if "calls" in cfg:
        expected_calls = cfg["calls"]
        if isinstance(parsed, dict) and isinstance(parsed.get("calls"), list):
            actual_list = parsed["calls"]
        elif isinstance(parsed, list):
            actual_list = parsed
        else:
            actual_list = [parsed]
        scores = []
        for i, call in enumerate(expected_calls):
            actual = actual_list[i] if i < len(actual_list) else None
            scores.append(
                _score_call(call.get("function"), call.get("args", {}), actual, strict)
            )
        return round(sum(scores) / len(scores), 1) if scores else 0.0
    if isinstance(parsed, list) and len(parsed) == 1:
        parsed = parsed[0]
    return _score_call(cfg.get("function"), cfg.get("args", {}), parsed, strict)
