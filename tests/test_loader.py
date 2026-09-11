from benchmark.loader import load_tasks


def test_loads_sample_task():
    tasks = load_tasks(["tasks/coding/001-reverse-string.yaml"])
    assert len(tasks) == 1
    assert tasks[0].id == "coding-001-reverse-string"
    assert tasks[0].difficulty == "easy"
    assert "reverse" in tasks[0].prompt.lower()


def test_loads_all_builtin_tasks():
    tasks = load_tasks(["tasks"])
    assert len(tasks) == 16
    categories = {t.category for t in tasks}
    assert categories == {"coding", "debugging", "tool-use", "reasoning", "instruction-following"}
    difficulties = {t.difficulty for t in tasks}
    assert difficulties == {"easy", "medium", "hard"}
