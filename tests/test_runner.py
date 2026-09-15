from agent_benchmark.adapters.echo import EchoAdapter
from agent_benchmark.models import Task
from agent_benchmark.runner import run


def test_runner_scores_demo_task():
    t = Task(
        id="coding-001-reverse-string",
        title="t",
        category="coding",
        eval={"pytest": {"weight": 1.0, "test_code": "from solution import reverse_string\n\n\ndef test_ok():\n    assert reverse_string(\"ab\") == \"ba\"\n"}},
    )
    results = run([t], EchoAdapter(), threshold=70.0)
    assert results[0].total == 100.0 and results[0].passed is True
    assert results[0].difficulty == "easy"
    assert results[0].error is None


class FlakyAdapter:
    name = "flaky"

    def __init__(self, fail_id):
        self.fail_id = fail_id

    def generate(self, task):
        if task.id == self.fail_id:
            raise RuntimeError("boom")
        return EchoAdapter().generate(task)


def test_runner_isolates_adapter_errors():
    good = Task(
        id="coding-001-reverse-string",
        title="t",
        category="coding",
        eval={"pytest": {"weight": 1.0, "test_code": "from solution import reverse_string\n\n\ndef test_ok():\n    assert reverse_string(\"ab\") == \"ba\"\n"}},
    )
    bad = Task(
        id="crash-me",
        title="t",
        category="coding",
        eval={"exact_match": {"weight": 1.0, "target": "hello", "source": "demo"}},
    )
    results = run([bad, good], FlakyAdapter("crash-me"), threshold=70.0)
    assert results[0].error is not None
    assert "boom" in results[0].error
    assert results[0].total == 0.0
    assert results[0].passed is False
    assert results[1].total == 100.0
    assert results[1].passed is True
    assert results[1].error is None
