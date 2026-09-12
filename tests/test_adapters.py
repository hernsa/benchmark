import json
import logging

from agent_benchmark.adapters.echo import EchoAdapter
from agent_benchmark.adapters.file_adapter import FileAdapter
from agent_benchmark.models import Task


def test_echo_adapter_coding_demo():
    t = Task(id="coding-001-reverse-string", title="t", category="coding", prompt="p")
    out = EchoAdapter().generate(t)
    assert "reverse_string" in out


def test_echo_adapter_tooluse_demo():
    t = Task(id="tooluse-001-simple-call", title="t", category="tool-use", prompt="p")
    out = EchoAdapter().generate(t)
    assert json.loads(out)["name"] == "get_weather"


def test_echo_adapter_unknown_falls_back():
    t = Task(id="nope", title="t", category="coding", prompt="p")
    assert EchoAdapter().generate(t) == "echo:nope"


def test_file_adapter_missing_returns_empty(tmp_path):
    t = Task(id="nope", title="t", category="coding", prompt="p")
    assert FileAdapter(str(tmp_path)).generate(t) == ""


def test_file_adapter_missing_warns(tmp_path, caplog):
    t = Task(id="nope", title="t", category="coding", prompt="p")
    with caplog.at_level(logging.WARNING):
        assert FileAdapter(str(tmp_path)).generate(t) == ""
    assert "nope" in caplog.text
