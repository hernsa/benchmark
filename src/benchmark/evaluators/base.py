"""Shared helpers for evaluators."""

import re


def normalize(text: str) -> str:
    """Basic whitespace normalization."""
    return text.strip()


def normalize_answer(text: str) -> str:
    """Aggressive normalization for answer comparison (GSM8K/MMLU style)."""
    t = str(text).strip().lower()
    t = t.replace(",", "").replace("$", "").strip()
    t = re.sub(r"\s+", " ", t)
    t = t.rstrip(".")
    t = t.strip("'\"")
    return t
