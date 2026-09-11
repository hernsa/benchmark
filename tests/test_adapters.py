from benchmark.adapters.echo import EchoAdapter
from benchmark.adapters.file_adapter import FileAdapter
from benchmark.models import Task


def test_echo_adapter_demo_task():
    t = Task(id="coding-reverse-string", title="t", category="coding", prompt="p")
    assert EchoAdapter().generate(t) == "olleh"


def test_file_adapter_missing_returns_empty(tmp_path):
    t = Task(id="nope", title="t", category="coding", prompt="p")
    assert FileAdapter(str(tmp_path)).generate(t) == ""
