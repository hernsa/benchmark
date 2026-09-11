"""Pytest-based code evaluation with partial credit (HumanEval/MBPP style).

The model output must contain a solution; the task YAML carries hidden tests
(``test_code``). Score is the fraction of tests that pass, so partial
solutions earn partial credit instead of a binary 0/100.
"""

import re
import subprocess
import sys
import tempfile
from pathlib import Path

from .base import normalize

_TIMEOUT = 60


def extract_code(output: str, language: str = "python") -> str:
    """Extract a fenced code block from model output, or fall back to raw text."""
    fence = re.search(r"```" + language + r"\s*\n(.*?)```", output, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    fence = re.search(r"```\s*\n(.*?)```", output, re.DOTALL)
    if fence:
        return fence.group(1).strip()
    return normalize(output)


def _parse_pytest_summary(text: str) -> tuple[int, int, int]:
    passed = sum(int(n) for n in re.findall(r"(\d+) passed", text))
    failed = sum(int(n) for n in re.findall(r"(\d+) failed", text))
    errors = sum(int(n) for n in re.findall(r"(\d+) error", text))
    return passed, failed, errors


def score(task, output: str) -> float:
    cfg = task.eval.get("pytest", {})
    test_code = cfg.get("test_code", "")
    code = extract_code(output)
    if not code.strip():
        return 0.0

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "solution.py").write_text(code, encoding="utf-8")
        (tmp_path / "test_solution.py").write_text(test_code, encoding="utf-8")
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "test_solution.py"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=_TIMEOUT,
            )
        except subprocess.TimeoutExpired:
            return 0.0

        combined = (proc.stdout or "") + (proc.stderr or "")
        if proc.returncode == 0:
            return 100.0
        passed, failed, errors = _parse_pytest_summary(combined)
        total = passed + failed + errors
        if total == 0:
            return 0.0
        return round(100.0 * passed / total, 1)
