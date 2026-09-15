import logging
import subprocess

import pytest

from agent_benchmark.evaluators import evaluate, weighted_total
from agent_benchmark.evaluators.base import EvaluationError
from agent_benchmark.evaluators.function_call import extract_json
from agent_benchmark.evaluators.pytest_eval import _scrubbed_env
from agent_benchmark.models import Task


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


# --- extraction hardening (function_call) ---


def test_extract_json_prose_brackets():
    text = (
        "I'll call [get_weather] now with "
        '{"name": "get_weather", "arguments": {"city": "Paris"}}'
    )
    parsed = extract_json(text)
    assert parsed["name"] == "get_weather"


def test_extract_json_last_fence_wins():
    text = (
        'Example:\n```json\n{"name": "decoy"}\n```\n'
        'Answer:\n```json\n{"name": "get_weather", "arguments": {"city": "Paris"}}\n```'
    )
    assert extract_json(text)["name"] == "get_weather"


def test_function_call_wrapper_dict_unwrapped():
    t = _task(
        {
            "function_call": {
                "weight": 1.0,
                "calls": [{"function": "get_weather", "args": {"city": "Paris"}}],
            }
        }
    )
    wrapped = '{"calls": [{"name": "get_weather", "arguments": {"city": "Paris"}}]}'
    assert evaluate(t, wrapped)["function_call"] == 100.0


# --- json_match deep compare ---


def test_json_match_deep_compare():
    t = _task(
        {"json_match": {"weight": 1.0, "expected": {"a": 1, "b": {"c": 2, "d": 3}}}}
    )
    assert evaluate(t, '{"a": 1, "b": {"c": 2, "d": 4}}')["json_match"] == 66.7


def test_json_match_type_mismatch_binary():
    t = _task({"json_match": {"weight": 1.0, "expected": {"a": 1}}})
    assert evaluate(t, "[1]")["json_match"] == 0.0


# --- registry warnings / validation ---


def test_unknown_evaluator_warns_and_skips(caplog):
    t = _task({"nope_eval": {"weight": 1.0}})
    with caplog.at_level(logging.WARNING):
        scores = evaluate(t, "whatever")
    assert scores == {}
    assert "unknown evaluator" in caplog.text
    assert "nope_eval" in caplog.text


def test_weight_must_be_number():
    t = _task({"exact_match": {"weight": "1.0", "target": "x", "source": "demo"}})
    scores = evaluate(t, "x")
    with pytest.raises(ValueError, match="weight"):
        weighted_total(t, scores)


# --- exact_match target validation ---


def test_exact_match_missing_target_raises():
    t = _task({"exact_match": {"weight": 1.0}})
    with pytest.raises(EvaluationError):
        evaluate(t, "hello")


# --- final_answer: units, tolerance, regex safety ---


def test_final_answer_numeric_units():
    t = _task({"final_answer": {"weight": 1.0, "target": "80", "mode": "numeric"}})
    assert evaluate(t, "#### 80 km/h")["final_answer"] == 100.0


def test_final_answer_relative_tolerance():
    t = _task(
        {
            "final_answer": {
                "weight": 1.0,
                "target": "1000",
                "mode": "numeric",
                "rel_tolerance": 0.01,
            }
        }
    )
    assert evaluate(t, "#### 1010")["final_answer"] == 100.0
    assert evaluate(t, "#### 1100")["final_answer"] == 0.0


def test_final_answer_invalid_regex_raises():
    t = _task({"final_answer": {"weight": 1.0, "target": "x", "regex": "([unclosed"}})
    with pytest.raises(EvaluationError):
        evaluate(t, "anything")


# --- pytest_eval hardening ---


def test_pytest_last_fence_wins():
    t = _task(
        {
            "pytest": {
                "weight": 1.0,
                "test_code": "from solution import add\n\n\ndef test_ok():\n    assert add(1, 2) == 3\n",
            }
        }
    )
    output = (
        "Decoy:\n```python\ndef add(a, b):\n    return 'decoy'\n```\n"
        "Final:\n```python\ndef add(a, b):\n    return a + b\n```"
    )
    assert evaluate(t, output)["pytest"] == 100.0


def test_pytest_timeout_raises(monkeypatch):
    def boom(*args, **kwargs):
        raise subprocess.TimeoutExpired(cmd="pytest", timeout=5)

    monkeypatch.setattr("agent_benchmark.evaluators.pytest_eval.subprocess.run", boom)
    t = _task(
        {
            "pytest": {
                "weight": 1.0,
                "test_code": "from solution import add\n\n\ndef test_ok():\n    assert add(1, 2) == 3\n",
                "timeout": 5,
            }
        }
    )
    output = "```python\ndef add(a, b):\n    return a + b\n```"
    with pytest.raises(EvaluationError, match="timed out"):
        evaluate(t, output)


def test_scrubbed_env_strips_secrets(monkeypatch):
    monkeypatch.setenv("MY_API_KEY", "s3cret")
    monkeypatch.setenv("MY_TOKEN", "s3cret")
    monkeypatch.setenv("DB_PASSWORD", "s3cret")
    env = _scrubbed_env()
    assert "MY_API_KEY" not in env
    assert "MY_TOKEN" not in env
    assert "DB_PASSWORD" not in env
    assert "PATH" in env


# --- code_quality extraction ---


def test_code_quality_prose_wrapped():
    t = _task({"code_quality": {"weight": 1.0}})
    output = "Here is my solution:\n```python\ndef f():\n    return 1\n```"
    assert evaluate(t, output)["code_quality"] == 100.0
