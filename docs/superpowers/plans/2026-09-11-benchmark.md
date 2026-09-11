# Benchmark Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a simple, professional, plugin-based Python benchmark runner that sends coding/debugging/tool-use tasks to AI agents and auto-scores results as percentages with a simple aggregate dashboard.

**Architecture:** Core runner loads YAML tasks, calls a ModelAdapter for output, runs hybrid evaluator plugins (exact/fuzzy match, pytest, code-quality), aggregates weighted percentage scores, and renders a Rich CLI dashboard plus JSON/CSV reports.

**Tech Stack:** Python >=3.10, Typer (CLI), Rich (dashboard tables), PyYAML (task/config), pytest (self-tests + task test execution), httpx (optional OpenAI-compatible adapter).

**Spec:** Brainstorm design agreed in chat 2026-09-11: Python plugin framework, hybrid auto-evaluation, existing-style + custom YAML tasks, simple aggregate dashboard (overall %, per-category bars, recent runs table). No web UI in v1 — CLI dashboard only to stay simple.

## Global Constraints

- Python requires-python >=3.10 (env has 3.12).
- Keep dependencies minimal: typer, rich, pyyaml, pytest, httpx.
- No secrets in repo; adapters read keys from env vars only.
- Every task YAML must have id, title, category, prompt, and at least one evaluator config.
- Scores are always 0-100 percentages; aggregate = mean of task scores.
- Windows + Linux compatible (no shell-specific tricks; use pathlib/subprocess list args).

---

### Task 1: Scaffold professional repo

**Files:**
- Create: `pyproject.toml`
- Create: `.gitignore`
- Create: `LICENSE`
- Create: `README.md`
- Create: `.github/workflows/ci.yml`
- Create: `src/benchmark/__init__.py`
- Create: `src/benchmark/__main__.py`
- Test: `tests/test_scaffold.py`

**Interfaces:**
- Consumes: none
- Produces: installable package `benchmark` with `benchmark` CLI entry point; `__version__` string in `src/benchmark/__init__.py`.

- [ ] **Step 1: Write the failing test**

```python
# tests/test_scaffold.py
import importlib
def test_package_importable():
    mod = importlib.import_module("benchmark")
    assert isinstance(mod.__version__, str)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_scaffold.py -v`
Expected: FAIL (module/paths missing)

- [ ] **Step 3: Write minimal implementation**

```toml
# pyproject.toml (key parts)
[build-system]
requires = ["setuptools>=68"]
build-backend = "setuptools.build_meta"
[project]
name = "agent-benchmark"
version = "0.1.0"
requires-python = ">=3.10"
dependencies = ["typer>=0.9", "rich>=13", "pyyaml>=6", "httpx>=0.27"]
[project.scripts]
benchmark = "benchmark.cli:app"
[tool.setuptools.packages.find]
where = ["src"]
[tool.pytest.ini_options]
testpaths = ["tests"]
```

```python
# src/benchmark/__init__.py
__version__ = "0.1.0"
```

```python
# src/benchmark/__main__.py
from benchmark.cli import app
if __name__ == "__main__":
    app()
```

`.gitignore`: `__pycache__/`, `*.pyc`, `.venv/`, `dist/`, `build/`, `*.egg-info/`, `.pytest_cache/`, `reports/`, `.coverage`.
`LICENSE`: MIT text.
`README.md`: title, badges placeholder, quickstart (`pip install -e .`, `benchmark list`, `benchmark run --adapter echo`), task format example, scoring explanation.
`.github/workflows/ci.yml`: on push/PR, setup-python 3.12, `pip install -e .[test]` or `pip install -e . && pip install pytest`, `pytest -q`.

- [ ] **Step 4: Run test to verify it passes**

Run: `pip install -e .; python -m pytest tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml .gitignore LICENSE README.md .github/workflows/ci.yml src/benchmark/__init__.py src/benchmark/__main__.py tests/test_scaffold.py
git commit -m "feat: scaffold professional benchmark repo"
```

### Task 2: Core models + YAML task loader

**Files:**
- Create: `src/benchmark/models.py`
- Create: `src/benchmark/loader.py`
- Test: `tests/test_loader.py`
- Create: `tasks/coding/001-reverse-string.yaml` (fixture + real task)

**Interfaces:**
- Consumes: YAML files on disk.
- Produces: `models.Task(id, title, category, difficulty, prompt, expected_output, eval, meta)`, `models.TaskResult(task_id, output, scores, total, passed)`, `loader.load_tasks(paths) -> list[Task]`.

```python
# src/benchmark/models.py
from dataclasses import dataclass, field
@dataclass
class Task:
    id: str
    title: str
    category: str
    difficulty: str = "easy"
    prompt: str = ""
    expected_output: str | None = None
    eval: dict = field(default_factory=dict)
    meta: dict = field(default_factory=dict)

@dataclass
class TaskResult:
    task_id: str
    category: str
    output: str
    scores: dict[str, float]
    total: float
    passed: bool
```

```python
# src/benchmark/loader.py
from pathlib import Path
import yaml
from .models import Task
def load_tasks(paths: list[str | Path]) -> list[Task]:
    found: list[Task] = []
    for p in paths:
        path = Path(p)
        files = sorted(path.rglob("*.yaml")) if path.is_dir() else [path]
        for f in files:
            if f.name.startswith("_"):
                continue
            data = yaml.safe_load(f.read_text(encoding="utf-8"))
            items = data if isinstance(data, list) else [data]
            for d in items:
                found.append(Task(id=str(d["id"]), title=d.get("title", d["id"]),
                    category=d.get("category", "general"), difficulty=d.get("difficulty", "easy"),
                    prompt=d.get("prompt", ""), expected_output=d.get("expected_output"),
                    eval=d.get("eval", {}) or {}, meta=d.get("meta", {}) or {}))
    return found
```

```yaml
# tasks/coding/001-reverse-string.yaml
id: coding-reverse-string
title: Reverse a string function
category: coding
difficulty: easy
prompt: "Write a Python function `reverse_string(s: str) -> str` that returns the reversed string. Output code only in a ```python block."
expected_output: "olleh"
eval:
  exact_match:
    weight: 1.0
    target: "olleh"
    source: demo
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_loader.py
from benchmark.loader import load_tasks
def test_loads_sample_task():
    tasks = load_tasks(["tasks/coding/001-reverse-string.yaml"])
    assert len(tasks) == 1
    assert tasks[0].id == "coding-reverse-string"
    assert "reverse" in tasks[0].prompt.lower()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_loader.py -v`
Expected: FAIL (loader/models missing)

- [ ] **Step 3: Write minimal implementation**

Write `src/benchmark/models.py` and `src/benchmark/loader.py` exactly as in Interfaces above. Create the sample YAML.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_loader.py tests/test_scaffold.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/benchmark/models.py src/benchmark/loader.py tests/test_loader.py tasks/coding/001-reverse-string.yaml
git commit -m "feat: add task models and YAML loader"
```

### Task 3: Model adapters (echo + file + OpenAI-compatible)

**Files:**
- Create: `src/benchmark/adapters/__init__.py`
- Create: `src/benchmark/adapters/base.py`
- Create: `src/benchmark/adapters/echo.py`
- Create: `src/benchmark/adapters/file_adapter.py`
- Create: `src/benchmark/adapters/openai_compat.py`
- Test: `tests/test_adapters.py`

**Interfaces:**
- Consumes: `models.Task`.
- Produces: `base.ModelAdapter` protocol with `name: str` and `generate(task: Task) -> str`; `echo.EchoAdapter` (deterministic demo output per task id); `file_adapter.FileAdapter(directory)` (reads `<task_id>.txt`); `openai_compat.OpenAICompatAdapter(model, base_url, api_key_env)` using httpx chat-completions.

```python
# src/benchmark/adapters/base.py
from typing import Protocol
from ..models import Task
class ModelAdapter(Protocol):
    name: str
    def generate(self, task: Task) -> str: ...
```

```python
# src/benchmark/adapters/echo.py
from ..models import Task
class EchoAdapter:
    name = "echo"
    def generate(self, task: Task) -> str:
        if task.id == "coding-reverse-string":
            return "olleh"
        if task.id == "coding-debug-offbyone":
            return "fixed"
        return f"echo:{task.id}"
```

```python
# src/benchmark/adapters/file_adapter.py
from pathlib import Path
from ..models import Task
class FileAdapter:
    name = "file"
    def __init__(self, directory: str = "outputs"):
        self.directory = Path(directory)
    def generate(self, task: Task) -> str:
        f = self.directory / f"{task.id}.txt"
        return f.read_text(encoding="utf-8") if f.exists() else ""
```

```python
# src/benchmark/adapters/openai_compat.py
import os, httpx
from ..models import Task
class OpenAICompatAdapter:
    def __init__(self, model: str, base_url: str = "https://api.openai.com/v1", api_key_env: str = "OPENAI_API_KEY"):
        self.name = f"openai-compat:{model}"
        self.model, self.base_url, self.api_key_env = model, base_url.rstrip("/"), api_key_env
    def generate(self, task: Task) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"Missing env var {self.api_key_env}")
        r = httpx.post(f"{self.base_url}/chat/completions", headers={"Authorization": f"Bearer {key}"},
            json={"model": self.model, "messages": [{"role": "user", "content": task.prompt}], "temperature": 0}, timeout=120)
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
```

- [ ] **Step 1: Write the failing test**

```python
# tests/test_adapters.py
from benchmark.models import Task
from benchmark.adapters.echo import EchoAdapter
from benchmark.adapters.file_adapter import FileAdapter
def test_echo_adapter_demo_task():
    t = Task(id="coding-reverse-string", title="t", category="coding", prompt="p")
    assert EchoAdapter().generate(t) == "olleh"
def test_file_adapter_missing_returns_empty(tmp_path):
    t = Task(id="nope", title="t", category="coding", prompt="p")
    assert FileAdapter(str(tmp_path)).generate(t) == ""
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_adapters.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Create the five adapter files exactly as above plus `__init__.py` re-exporting them.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_adapters.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/benchmark/adapters tests/test_adapters.py
git commit -m "feat: add model adapters (echo, file, openai-compatible)"
```

### Task 4: Hybrid evaluators + runner + aggregation

**Files:**
- Create: `src/benchmark/evaluators/__init__.py`
- Create: `src/benchmark/evaluators/base.py`
- Create: `src/benchmark/evaluators/exact_match.py`
- Create: `src/benchmark/evaluators/pytest_eval.py`
- Create: `src/benchmark/evaluators/code_quality.py`
- Create: `src/benchmark/runner.py`
- Create: `src/benchmark/report.py`
- Test: `tests/test_evaluators.py`
- Test: `tests/test_runner.py`

**Interfaces:**
- Consumes: `Task`, `ModelAdapter`.
- Produces: `evaluators.evaluate(task, output) -> dict[str, float]` (each 0-100); `runner.run(tasks, adapter, threshold=70.0) -> list[TaskResult]`; `report.summarize(results) -> dict` with `overall_pct`, `by_category`, `passed`, `total`.

Evaluator rules:
- `exact_match`: config at `task.eval["exact_match"]` with `target`; score 100 if normalized output == target else 0. `source: demo` means compare raw output; default extracts last non-empty line.
- `pytest_eval`: config `task.eval["pytest"]` with `code_block: python`, `test_code` (pytest source), writes output code + test to temp dir, runs `pytest -q`, 100 on pass else 0. Timeout 60s.
- `code_quality`: 100 if `compile()` succeeds else 0, minus 20 if output > 4000 chars (cap at 0). No external linters.
- Weighted total = sum(score*weight)/sum(weights); no eval config means total 0 and passed False.

```python
# summarize() output shape
{"overall_pct": 87.5, "total": 4, "passed": 3, "pass_rate": 75.0,
 "by_category": {"coding": {"pct": 90.0, "passed": 2, "total": 2}},
 "results": [{"task_id": ..., "category": ..., "total": ..., "passed": ..., "scores": {...}}]}
```

- [ ] **Step 1: Write the failing tests**

```python
# tests/test_evaluators.py
from benchmark.models import Task
from benchmark.evaluators import evaluate
def test_exact_match_pass():
    t = Task(id="x", title="t", category="coding", expected_output="olleh",
             eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}})
    assert evaluate(t, "olleh")["exact_match"] == 100.0
def test_exact_match_fail():
    t = Task(id="x", title="t", category="coding",
             eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}})
    assert evaluate(t, "hello")["exact_match"] == 0.0
def test_code_quality_compiles():
    t = Task(id="x", title="t", category="coding", eval={"code_quality": {"weight": 1.0}})
    assert evaluate(t, "def f():\n    return 1\n")["code_quality"] == 100.0
```

```python
# tests/test_runner.py
from benchmark.models import Task
from benchmark.adapters.echo import EchoAdapter
from benchmark.runner import run
def test_runner_scores_demo_task():
    t = Task(id="coding-reverse-string", title="t", category="coding",
             eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}})
    results = run([t], EchoAdapter(), threshold=70.0)
    assert results[0].total == 100.0 and results[0].passed is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest tests/test_evaluators.py tests/test_runner.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Implement evaluators, `runner.run`, and `report.summarize` per rules above.

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest tests/ -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add src/benchmark/evaluators src/benchmark/runner.py src/benchmark/report.py tests/test_evaluators.py tests/test_runner.py
git commit -m "feat: add hybrid evaluators, runner, and aggregation"
```

### Task 5: Built-in task packs (coding, debugging, tool-use)

**Files:**
- Create: `tasks/coding/002-fizzbuzz.yaml`
- Create: `tasks/coding/003-debug-offbyone.yaml`
- Create: `tasks/tooluse/001-summarize-diff.yaml`
- Create: `config/benchmark.example.yaml`
- Create: `config/models.example.yaml`
- Test: `tests/test_taskpacks.py`

**Interfaces:**
- Consumes: loader.
- Produces: >=4 loadable tasks across coding/debugging/tool-use; example configs.

Task contents:
- `002-fizzbuzz.yaml`: pytest evaluator; prompt asks for `fizzbuzz(n)`; embed `test_code` asserting fizz/buzz/fizzbuzz/numbers.
- `003-debug-offbyone.yaml`: id `coding-debug-offbyone`; pytest evaluator with buggy-behavior test; echo adapter returns "fixed" so give it exact_match target "fixed" too (hybrid demo).
- `001-summarize-diff.yaml`: category `tool-use`; exact_match demo target.
- `config/benchmark.example.yaml`: `tasks: ["tasks/coding", "tasks/tooluse"]`, `threshold: 70`, `reports_dir: reports`.
- `config/models.example.yaml`: echo adapter + commented openai-compat examples (env-based, no keys).

- [ ] **Step 1: Write the failing test**

```python
# tests/test_taskpacks.py
from benchmark.loader import load_tasks
def test_packs_load():
    tasks = load_tasks(["tasks"])
    assert len(tasks) >= 4
    cats = {t.category for t in tasks}
    assert {"coding", "tool-use"} <= cats
    assert all(t.prompt and t.eval for t in tasks)
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_taskpacks.py -v`
Expected: FAIL (files missing)

- [ ] **Step 3: Write minimal implementation**

Create the YAML tasks and example configs.

- [ ] **Step 4: Run test to verify it passes**

Run: `python -m pytest tests/test_taskpacks.py -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add tasks config tests/test_taskpacks.py
git commit -m "feat: add built-in coding, debugging, and tool-use tasks"
```

### Task 6: CLI + simple aggregate dashboard + sample verification run

**Files:**
- Create: `src/benchmark/cli.py`
- Test: `tests/test_cli.py`

**Interfaces:**
- Consumes: loader, adapters, runner, report.
- Produces: `benchmark list --tasks-dir tasks`, `benchmark run --tasks-dir tasks --adapter echo --threshold 70 --reports-dir reports` printing Rich table (task, category, score %, pass) + aggregate summary (overall %, pass rate, per-category %) and writing `reports/report.json` + `reports/report.csv` + `reports/report.md`.

```python
# tests/test_cli.py
from typer.testing import CliRunner
from benchmark.cli import app
def test_list_command():
    r = CliRunner().invoke(app, ["list", "--tasks-dir", "tasks"])
    assert r.exit_code == 0 and "coding-reverse-string" in r.output
def test_run_command_writes_report(tmp_path):
    from typer.testing import CliRunner
    r = CliRunner().invoke(app, ["run", "--tasks-dir", "tasks", "--adapter", "echo", "--reports-dir", str(tmp_path)])
    assert r.exit_code == 0 and (tmp_path / "report.json").exists()
```

- [ ] **Step 1: Write the failing test**

Create `tests/test_cli.py` as above.

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest tests/test_cli.py -v`
Expected: FAIL

- [ ] **Step 3: Write minimal implementation**

Implement `src/benchmark/cli.py` with `list` and `run` commands, Rich tables, JSON/CSV/MD writers.

- [ ] **Step 4: Run tests + sample run to verify**

Run: `python -m pytest tests/ -q`
Expected: PASS
Run: `benchmark run --tasks-dir tasks --adapter echo --reports-dir reports`
Expected: overall % printed; `reports/report.json` exists.

- [ ] **Step 5: Commit**

```bash
git add src/benchmark/cli.py tests/test_cli.py
git commit -m "feat: add CLI with aggregate dashboard and reports"
```

## Self-Review

- Spec coverage: plugin runner, hybrid evaluators, custom+built-in tasks, simple aggregate dashboard, percentage scoring — each has a task above. No web UI (intentionally deferred for simplicity).
- Placeholder scan: all steps include exact code/config; no TBDs.
- Type consistency: `Task`, `TaskResult`, `ModelAdapter.generate`, `evaluate`, `run`, `summarize` signatures reused verbatim across tasks.
