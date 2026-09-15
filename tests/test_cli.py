import csv
import json
import logging

from typer.testing import CliRunner

from agent_benchmark.cli import app

runner = CliRunner()


def _tiny_task_dir(tmp_path):
    """One exact_match task + a file-adapter output dir: keeps CLI tests fast."""
    tasks_dir = tmp_path / "tasks"
    tasks_dir.mkdir()
    (tasks_dir / "t-001.yaml").write_text(
        "id: t-001\n"
        "title: tiny\n"
        "category: coding\n"
        "eval:\n"
        "  exact_match:\n"
        "    weight: 1.0\n"
        "    target: hello\n",
        encoding="utf-8",
    )
    outputs = tmp_path / "outputs"
    outputs.mkdir()
    (outputs / "t-001.txt").write_text("hello", encoding="utf-8")
    return tasks_dir, outputs


def test_cli_run_echo(tmp_path):
    out = tmp_path / "results"
    result = runner.invoke(
        app,
        ["run", "tasks", "--adapter", "echo", "--out-dir", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert (out / "results.json").exists()
    assert (out / "REPORT.md").exists()
    assert (out / "results.csv").exists()
    assert "Overall" in result.output


def test_cli_list_command():
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0, result.output
    assert "28 tasks" in result.output


def test_cli_config_precedence_cli_wins(tmp_path):
    tasks_dir, outputs = _tiny_task_dir(tmp_path)
    cfg = tmp_path / "cfg.yaml"
    cfg.write_text(
        f"tasks: [{tasks_dir.as_posix()}]\n"
        "adapter: file\n"
        "threshold: 40.0\n"
        f"adapter_opts:\n  dir: {outputs.as_posix()}\n",
        encoding="utf-8",
    )
    out = tmp_path / "results"
    result = runner.invoke(
        app,
        [
            "run", "--config", str(cfg), "--adapter", "echo", "--threshold", "70",
            "--out-dir", str(out),
        ],
    )
    assert result.exit_code == 0, result.output
    data = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert data["meta"]["adapter"] == "echo"
    assert data["meta"]["threshold"] == 70.0


def test_cli_fail_under_exit_code(tmp_path):
    tasks_dir, outputs = _tiny_task_dir(tmp_path)
    out = tmp_path / "results"
    base = ["run", str(tasks_dir), "--adapter", "file", "--opt", f"dir={outputs}", "--out-dir", str(out)]
    fail = runner.invoke(app, base + ["--fail-under", "101"])
    assert fail.exit_code == 1, fail.output
    ok = runner.invoke(app, base + ["--fail-under", "100"])
    assert ok.exit_code == 0, ok.output


def test_cli_tag_creates_subdir(tmp_path):
    tasks_dir, outputs = _tiny_task_dir(tmp_path)
    out = tmp_path / "results"
    result = runner.invoke(
        app,
        [
            "run", str(tasks_dir), "--adapter", "file", "--opt", f"dir={outputs}",
            "--out-dir", str(out), "--tag", "demo",
        ],
    )
    assert result.exit_code == 0, result.output
    assert (out / "demo" / "results.json").exists()


def test_cli_outputs_persisted(tmp_path):
    tasks_dir, outputs = _tiny_task_dir(tmp_path)
    out = tmp_path / "results"
    result = runner.invoke(
        app,
        ["run", str(tasks_dir), "--adapter", "file", "--opt", f"dir={outputs}", "--out-dir", str(out)],
    )
    assert result.exit_code == 0, result.output
    data = json.loads((out / "results.json").read_text(encoding="utf-8"))
    assert data["results"][0]["output"] == "hello"
    with (out / "results.csv").open(encoding="utf-8", newline="") as f:
        rows = list(csv.DictReader(f))
    assert rows[0]["output"] == "hello"


def test_cli_echo_warns_on_unknown_tasks(tmp_path, caplog):
    tasks_dir, _ = _tiny_task_dir(tmp_path)
    with caplog.at_level(logging.WARNING):
        result = runner.invoke(
            app,
            ["run", str(tasks_dir), "--adapter", "echo", "--out-dir", str(tmp_path / "results")],
        )
    assert result.exit_code == 0, result.output
    assert "t-001" in caplog.text
