from benchmark.evaluators import evaluate
from benchmark.models import Task


def test_exact_match_pass():
    t = Task(
        id="x",
        title="t",
        category="coding",
        expected_output="olleh",
        eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}},
    )
    assert evaluate(t, "olleh")["exact_match"] == 100.0


def test_exact_match_fail():
    t = Task(
        id="x",
        title="t",
        category="coding",
        eval={"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}},
    )
    assert evaluate(t, "hello")["exact_match"] == 0.0


def test_code_quality_compiles():
    t = Task(
        id="x", title="t", category="coding", eval={"code_quality": {"weight": 1.0}}
    )
    assert evaluate(t, "def f():\n    return 1\n")["code_quality"] == 100.0
