from benchmark.adapters.echo import EchoAdapter
from benchmark.models import Task
from benchmark.runner import run


def test_runner_scores_demo_task():
    t = Task(
        id="coding-reverse-string",
        title="t",
        category="coding",
        eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}},
    )
    results = run([t], EchoAdapter(), threshold=70.0)
    assert results[0].total == 100.0 and results[0].passed is True
