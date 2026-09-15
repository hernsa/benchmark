"""Shared helpers for evaluators."""

import re


class EvaluationError(Exception):
    """Raised when an evaluator cannot run (bad task config, timeout, ...)."""


def normalize(text: str) -> str:
    return text.strip()


def normalize_answer(text) -> str:
    t = str(text).strip().lower()
    t = re.sub(r"(?<=\d),(?=\d)", "", t)  # 1,000 -> 1000
    t = t.replace("$", "")
    t = t.replace(",", " ")  # a,b -> a b
    t = re.sub(r"\s+", " ", t)
    t = t.rstrip(".")
    return t.strip("'\"")


def extract_code(output: str, language: str = "python") -> str:
    """Extract the LAST fenced code block; fall back to the whole output.

    Models typically show an example block first and the solution last, so the
    final fence is the best candidate. When no fence exists, the raw output is
    returned so prose-only answers fail compilation instead of silently
    returning 0 with no trace.
    """
    for pattern in (r"```" + language + r"\s*\n(.*?)```", r"```\s*\n(.*?)```"):
        blocks = re.findall(pattern, output, re.DOTALL)
        if blocks:
            return blocks[-1].strip()
    return output.strip()
