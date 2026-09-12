import importlib


def test_package_importable():
    mod = importlib.import_module("agent_benchmark")
    assert isinstance(mod.__version__, str)
