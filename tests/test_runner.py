from benchmark.adapters.echo import EchoAdapter
from benchmark.models import Task
from benchmark.runner import run


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
