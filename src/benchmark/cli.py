"""Command-line interface: run a benchmark and show the aggregate dashboard."""

import csv
import json
from datetime import datetime, timezone
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .adapters.echo import EchoAdapter
from .adapters.file_adapter import FileAdapter
from .adapters.openai_compat import OpenAICompatAdapter
from .loader import load_tasks
from .report import summarize
from .runner import run as run_tasks

app = typer.Typer(help="Simple plugin-based benchmark runner for AI agents.")
console = Console()


def _parse_opts(opts: list[str]) -> dict[str, str]:
    parsed: dict[str, str] = {}
    for item in opts:
        if "=" not in item:
            raise typer.BadParameter(f"Adapter option must be key=value, got: {item!r}")
        key, value = item.split("=", 1)
        parsed[key.strip()] = value.strip()
    return parsed


def _build_adapter(kind: str, opts: dict[str, str]):
    kind = kind.lower()
    if kind == "echo":
        return EchoAdapter()
    if kind == "file":
        return FileAdapter(opts.get("dir", "outputs"))
    if kind in ("openai-compat", "openai_compat", "openai"):
        return OpenAICompatAdapter(
            model=opts.get("model", "gpt-4o-mini"),
            base_url=opts.get("base-url", "https://api.openai.com/v1"),
            api_key_env=opts.get("api-key-env", "OPENAI_API_KEY"),
        )
    raise typer.BadParameter(f"Unknown adapter: {kind} (echo|file|openai-compat)")


def _load_config(path: str | None) -> dict:
    if not path:
        return {}
    return yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}


def _print_dashboard(summary: dict, adapter_name: str) -> None:
    table = Table(title=f"Benchmark results — {adapter_name}")
    table.add_column("Task", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Score %", justify="right")
    table.add_column("Result", justify="center")
    for r in summary["results"]:
        table.add_row(
            r["task_id"],
            r["category"],
            f"{r['total']:.1f}",
            "[green]PASS[/green]" if r["passed"] else "[red]FAIL[/red]",
        )
    console.print(table)

    cat_lines = "\n".join(
        f"{name}: {v['pct']:.1f}% ({v['passed']}/{v['total']} passed)"
        for name, v in summary["by_category"].items()
    )
    console.print(
        Panel(
            f"Overall: {summary['overall_pct']:.1f}%\n"
            f"Pass rate: {summary['pass_rate']:.1f}% "
            f"({summary['passed']}/{summary['total']})\n\n"
            f"{cat_lines}",
            title="Aggregate",
        )
    )


def _write_markdown(summary: dict, adapter_name: str, path: Path) -> None:
    lines = [
        "# Benchmark Report",
        "",
        f"- Adapter: `{adapter_name}`",
        f"- Overall score: **{summary['overall_pct']:.1f}%**",
        f"- Pass rate: **{summary['pass_rate']:.1f}%** "
        f"({summary['passed']}/{summary['total']})",
        "",
        "## By category",
        "",
        "| Category | Score % | Passed | Total |",
        "| --- | ---: | ---: | ---: |",
    ]
    for name, v in summary["by_category"].items():
        lines.append(f"| {name} | {v['pct']:.1f} | {v['passed']} | {v['total']} |")
    lines += [
        "",
        "## By task",
        "",
        "| Task | Category | Score % | Result |",
        "| --- | --- | ---: | --- |",
    ]
    for r in summary["results"]:
        mark = "PASS" if r["passed"] else "FAIL"
        lines.append(f"| {r['task_id']} | {r['category']} | {r['total']:.1f} | {mark} |")
    lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def _write_csv(summary: dict, path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["task_id", "category", "score_pct", "passed", "scores"])
        for r in summary["results"]:
            w.writerow(
                [r["task_id"], r["category"], r["total"], r["passed"], json.dumps(r["scores"])]
            )


@app.command()
def run(
    tasks: list[str] = typer.Argument(default=["tasks"], help="Task YAML files or dirs."),
    adapter: str = typer.Option("echo", help="Adapter: echo|file|openai-compat."),
    opt: list[str] = typer.Option(
        [], "--opt", help="Adapter option as key=value (repeatable)."
    ),
    threshold: float = typer.Option(70.0, help="Pass threshold in percent."),
    out_dir: str = typer.Option("results", help="Directory for JSON/MD/CSV reports."),
    config: str | None = typer.Option(None, help="YAML config file with these settings."),
) -> None:
    """Run tasks against an adapter, print the dashboard, save reports."""
    cfg = _load_config(config)
    task_paths = cfg.get("tasks", tasks)
    adapter_kind = cfg.get("adapter", adapter)
    threshold = float(cfg.get("threshold", threshold))
    out = Path(cfg.get("out_dir", out_dir))

    adapter_opts = _parse_opts(opt)
    if isinstance(cfg.get("adapter_opts"), dict):
        adapter_opts = {**cfg["adapter_opts"], **adapter_opts}

    loaded = load_tasks(task_paths)
    if not loaded:
        console.print("[red]No tasks found.[/red]")
        raise typer.Exit(1)

    model = _build_adapter(adapter_kind, adapter_opts)
    results = run_tasks(loaded, model, threshold=threshold)
    summary = summarize(results)
    summary["meta"] = {
        "adapter": model.name,
        "threshold": threshold,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }

    _print_dashboard(summary, model.name)

    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_markdown(summary, model.name, out / "REPORT.md")
    _write_csv(summary, out / "results.csv")
    console.print(f"[green]Reports saved to {out}/[/green]")
