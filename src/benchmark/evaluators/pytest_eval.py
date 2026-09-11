import re
import subprocess
import sys
import tempfile
from pathlib import Path

from ..models import Task


def extract_code(output: str, language: str = "python") -> str:
    m = re.search(rf"```{language}\n(.*?)```", output, re.DOTALL)
    if m:
        return m.group(1).strip()
    m = re.search(r"```\n(.*?)```", output, re.DOTALL)
    if m:
        return m.group(1).strip()
    return output.strip()


def score(task: Task, output: str) -> float:
    cfg = task.eval.get("pytest", {})
    test_code = cfg.get("test_code", "")
    if not test_code:
        return 0.0
    code = extract_code(output, cfg.get("code_block", "python"))
    with tempfile.TemporaryDirectory() as tmp:
        d = Path(tmp)
        (d / "solution.py").write_text(code, encoding="utf-8")
        (d / "test_solution.py").write_text(test_code, encoding="utf-8")
        try:
            r = subprocess.run(
                [sys.executable, "-m", "pytest", "-q", "test_solution.py"],
                cwd=d,
                capture_output=True,
                text=True,
                timeout=60,
            )
        except subprocess.TimeoutExpired:
            return 0.0
    return 100.0 if r.returncode == 0 else 0.0
