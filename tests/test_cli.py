from typer.testing import CliRunner

from benchmark.cli import app


def test_cli_run_echo(tmp_path):
    out = tmp_path / "results"
    result = CliRunner().invoke(
        app,
        ["tasks", "--adapter", "echo", "--out-dir", str(out)],
    )
    assert result.exit_code == 0, result.output
    assert (out / "results.json").exists()
    assert (out / "REPORT.md").exists()
    assert (out / "results.csv").exists()
    assert "Overall" in result.output
