import logging

import pytest

from agent_benchmark.loader import load_tasks


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


def test_loads_yml_files(tmp_path):
    (tmp_path / "foo.yml").write_text(
        "id: yml-task\ntitle: t\ncategory: coding\n", encoding="utf-8"
    )
    tasks = load_tasks([tmp_path])
    assert [t.id for t in tasks] == ["yml-task"]


def test_duplicate_ids_warn_and_first_kept(tmp_path, caplog):
    for name in ("a.yaml", "b.yaml"):
        (tmp_path / name).write_text("id: dup\ntitle: t\ncategory: coding\n", encoding="utf-8")
    with caplog.at_level(logging.WARNING):
        tasks = load_tasks([tmp_path])
    assert len(tasks) == 1
    assert "duplicate" in caplog.text.lower()


def test_nonexistent_path_raises_clean_error():
    with pytest.raises(FileNotFoundError, match="does-not-exist"):
        load_tasks(["does-not-exist"])


def test_invalid_yaml_error_includes_path(tmp_path):
    (tmp_path / "bad.yaml").write_text("id: [unclosed\n  bad: :", encoding="utf-8")
    with pytest.raises(ValueError, match="bad.yaml"):
        load_tasks([tmp_path])


def test_missing_id_error_includes_path(tmp_path):
    (tmp_path / "noid.yaml").write_text("title: t\ncategory: coding\n", encoding="utf-8")
    with pytest.raises(ValueError, match="noid.yaml"):
        load_tasks([tmp_path])


def test_exact_match_eval_requires_target(tmp_path):
    (tmp_path / "nope.yaml").write_text(
        "id: x\ntitle: t\ncategory: coding\neval:\n  exact_match:\n    weight: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="exact_match"):
        load_tasks([tmp_path])


def test_pytest_eval_requires_test_code(tmp_path):
    (tmp_path / "nope.yaml").write_text(
        "id: x\ntitle: t\ncategory: coding\neval:\n  pytest:\n    weight: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="test_code"):
        load_tasks([tmp_path])


def test_function_call_eval_requires_function_or_calls(tmp_path):
    (tmp_path / "nope.yaml").write_text(
        "id: x\ntitle: t\ncategory: coding\neval:\n  function_call:\n    weight: 1.0\n",
        encoding="utf-8",
    )
    with pytest.raises(ValueError, match="function_call"):
        load_tasks([tmp_path])
