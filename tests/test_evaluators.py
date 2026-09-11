from benchmark.evaluators import evaluate
from benchmark.models import Task


def _task(eval_cfg: dict) -> Task:
    return Task(id="x", title="t", category="coding", eval=eval_cfg)


def test_exact_match_pass():
    t = _task({"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}})
    assert evaluate(t, "olleh")["exact_match"] == 100.0


def test_exact_match_fail():
    t = _task({"exact_match": {"weight": 1.0, "target": "olleh", "source": "demo"}})
    assert evaluate(t, "hello")["exact_match"] == 0.0


def test_code_quality_compiles():
    t = _task({"code_quality": {"weight": 1.0}})
    assert evaluate(t, "def f():\n    return 1\n")["code_quality"] == 100.0


def test_pytest_full_pass():
    t = _task(
        {
            "pytest": {
                "weight": 1.0,
                "test_code": (
                    "from solution import add\n\n\n"
                    "def test_ok():\n    assert add(1, 2) == 3\n"
                ),
            }
        }
    )
    output = "```python\ndef add(a, b):\n    return a + b\n```"
    assert evaluate(t, output)["pytest"] == 100.0


def test_pytest_partial_credit():
    t = _task(
        {
            "pytest": {
                "weight": 1.0,
                "test_code": (
                    "from solution import add\n\n\n"
                    "def test_ok():\n    assert add(1, 2) == 3\n\n\n"
                    "def test_bad():\n    assert add(1, 2) == 4\n"
                ),
            }
        }
    )
    output = "```python\ndef add(a, b):\n    return a + b\n```"
    assert evaluate(t, output)["pytest"] == 50.0


def test_pytest_broken_code_zero():
    t = _task(
        {
            "pytest": {
                "weight": 1.0,
                "test_code": "from solution import add\n\n\ndef test_ok():\n    assert add(1, 2) == 3\n",
            }
        }
    )
    assert evaluate(t, "```python\nthis is not python\n```")["pytest"] == 0.0


def test_final_answer_numeric():
    t = _task({"final_answer": {"weight": 1.0, "target": "80", "mode": "numeric"}})
    assert evaluate(t, "Speed is 120/1.5.\n\n#### 80")["final_answer"] == 100.0
    assert evaluate(t, "blah\n\n#### $80.00")["final_answer"] == 100.0
    assert evaluate(t, "blah\n\n#### 90")["final_answer"] == 0.0


def test_final_answer_exact():
    t = _task({"final_answer": {"weight": 1.0, "target": "Paris"}})
    assert evaluate(t, "The city is...\n\n#### Paris")["final_answer"] == 100.0
    assert evaluate(t, "#### paris.")["final_answer"] == 100.0
    assert evaluate(t, "#### London")["final_answer"] == 0.0


def test_function_call_single():
    t = _task(
        {
            "function_call": {
                "weight": 1.0,
                "function": "get_weather",
                "args": {"city": "Paris", "unit": "celsius"},
            }
        }
    )
    good = '{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}'
    assert evaluate(t, good)["function_call"] == 100.0
    wrong_name = '{"name": "get_forecast", "arguments": {"city": "Paris"}}'
    assert evaluate(t, wrong_name)["function_call"] == 0.0
    partial = '{"name": "get_weather", "arguments": {"city": "Paris"}}'
    assert evaluate(t, partial)["function_call"] == 70.0


def test_function_call_strict_penalizes_extra_args():
    t = _task(
        {
            "function_call": {
                "weight": 1.0,
                "function": "get_weather",
                "args": {"city": "Paris"},
                "strict": True,
            }
        }
    )
    extra = '{"name": "get_weather", "arguments": {"city": "Paris", "unit": "x"}}'
    # name 40 + 60 * (1/1 * 1/2) = 70
    assert evaluate(t, extra)["function_call"] == 70.0


def test_function_call_parallel():
    t = _task(
        {
            "function_call": {
                "weight": 1.0,
                "calls": [
                    {"function": "get_weather", "args": {"city": "Paris"}},
                    {"function": "get_weather", "args": {"city": "Tokyo"}},
                ],
            }
        }
    )
    both = (
        '[{"name": "get_weather", "arguments": {"city": "Paris"}}, '
        '{"name": "get_weather", "arguments": {"city": "Tokyo"}}]'
    )
    assert evaluate(t, both)["function_call"] == 100.0
    one = '[{"name": "get_weather", "arguments": {"city": "Paris"}}]'
    assert evaluate(t, one)["function_call"] == 50.0


def test_json_match_partial():
    t = _task({"json_match": {"weight": 1.0, "expected": {"a": 1, "b": 2}}})
    assert evaluate(t, '{"a": 1, "b": 2}')["json_match"] == 100.0
    assert evaluate(t, '{"a": 1}')["json_match"] == 50.0
    assert evaluate(t, "not json")["json_match"] == 0.0
