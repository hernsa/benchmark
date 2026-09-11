from benchmark.loader import load_tasks


def test_loads_sample_task():
    tasks = load_tasks(["tasks/coding/001-reverse-string.yaml"])
    assert len(tasks) == 1
    assert tasks[0].id == "coding-reverse-string"
    assert "reverse" in tasks[0].prompt.lower()
