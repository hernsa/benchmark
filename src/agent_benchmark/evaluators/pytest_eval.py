"""Pytest-based code scoring.

Runs the model's code in an isolated temp directory with a scrubbed
environment. Model-generated code is still executed on the host — see the
README security notes before pointing this evaluator at untrusted models.
"""

import os
import re
import subprocess
import sys
import tempfile

from .base import EvaluationError, extract_code

_SECRET_PATTERN = re.compile(r"API_KEY|TOKEN|SECRET|PASSWORD|CREDENTIAL", re.IGNORECASE)


def _scrubbed_env() -> dict:
    """Subprocess environment with obvious secret-ish variables stripped."""
    env = {k: v for k, v in os.environ.items() if not _SECRET_PATTERN.search(k)}
    env.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    return env


def _parse_pytest_summary(text: str) -> tuple[int, int, int]:
    passed = sum(int(n) for n in re.findall(r"(\d+) passed", text))
    failed = sum(int(n) for n in re.findall(r"(\d+) failed", text))
    errors = sum(int(n) for n in re.findall(r"(\d+) error", text))
    return passed, failed, errors


def score(task, output: str) -> float:
    cfg = task.eval.get("pytest", {}) or {}
    test_code = cfg.get("test_code", "")
    code = extract_code(output)
    if not code.strip():
        return 0.0
    timeout = float(cfg.get("timeout", 60))
    with tempfile.TemporaryDirectory() as tmp:
        with open(os.path.join(tmp, "solution.py"), "w", encoding="utf-8") as f:
            f.write(code)
        with open(os.path.join(tmp, "test_solution.py"), "w", encoding="utf-8") as f:
            f.write(test_code)
        try:
            proc = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "test_solution.py"],
                cwd=tmp,
                capture_output=True,
                text=True,
                timeout=timeout,
                env=_scrubbed_env(),
            )
        except subprocess.TimeoutExpired:
            raise EvaluationError(f"pytest eval timed out after {timeout}s") from None
    if proc.returncode == 0:
        return 100.0
    combined = (proc.stdout or "") + (proc.stderr or "")
    passed, failed, errors = _parse_pytest_summary(combined)
    total = passed + failed + errors
    if total == 0:
        return 0.0
    return round(100.0 * passed / total, 1)
