from agent_benchmark.compare import compare_models
from agent_benchmark.charts import save_comparison_png
from agent_benchmark.models import Task, TaskResult


class Stub:
    def __init__(self, name, output):
        self.name = name
        self._out = output

    def generate(self, task):
        return self._out


def _task(tid="t1"):
    return Task(
        id=tid,
        title="T",
        category="coding",
        difficulty="easy",
        prompt="p",
        expected_output="hi",
        eval={"exact_match": {"source": "demo", "target": "hi"}},
    )


def test_compare_models_two_stubs():
    tasks = [_task()]
    a = Stub("m/a", "hi")
    b = Stub("m/b", "nope")
    c = compare_models(tasks, [a, b], threshold=70.0)
    assert c["model_order"] == ["m/a", "m/b"]
    assert c["models"]["m/a"]["overall_pct"] == 100.0
    assert c["models"]["m/b"]["overall_pct"] == 0.0


def test_save_png_four_panels(tmp_path):
    c = {
        "model_order": ["m/a", "m/b"],
        "models": {
            "m/a": {"overall_pct": 80.0, "pass_rate": 75.0,
                    "by_category": {"coding": {"pct": 80.0}},
                    "by_difficulty": {"easy": {"pct": 90.0}}},
            "m/b": {"overall_pct": 60.0, "pass_rate": 50.0,
                    "by_category": {"coding": {"pct": 60.0}},
                    "by_difficulty": {"easy": {"pct": 50.0}}},
        },
    }
    out = tmp_path / "comparison.png"
    p = save_comparison_png(c, out)
    assert p.exists() and p.stat().st_size > 10000
