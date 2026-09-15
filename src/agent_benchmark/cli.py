"""Command-line interface for the benchmark runner."""

import csv
import importlib.util
import json
import logging
from datetime import datetime, timezone
from pathlib import Path

import typer
import yaml
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from .adapters.echo import DEMO_OUTPUTS, EchoAdapter
from .adapters.file_adapter import FileAdapter
from .adapters.opencode import OpencodeAdapter, list_opencode_models
from .adapters.openai_compat import OpenAICompatAdapter
from .compare import compare_models
from .charts import save_comparison_png
from .loader import load_tasks
from .report import summarize
from .runner import run as run_tasks

app = typer.Typer(help="Benchmark runner for AI agents.")
console = Console()
logger = logging.getLogger("agent_benchmark")


def _setup_logging() -> None:
    logging.basicConfig(level=logging.WARNING, format="%(levelname)s %(name)s: %(message)s")


def _parse_opts(opts: list[str]) -> dict:
    out = {}
    for opt in opts:
        if "=" not in opt:
            raise typer.BadParameter(f"Invalid option {opt!r} — expected key=value")
        k, v = opt.split("=", 1)
        out[k] = v
    return out


def _build_adapter(kind: str, opts: dict):
    if kind == "echo":
        return EchoAdapter()
    if kind == "file":
        return FileAdapter(opts.get("dir", "outputs"))
    if kind in ("openai-compat", "openai_compat", "openai"):
        try:
            return OpenAICompatAdapter(
                model=opts.get("model", "gpt-4o-mini"),
                base_url=opts.get("base-url", "https://api.openai.com/v1"),
                api_key_env=opts.get("api-key-env", "OPENAI_API_KEY"),
                timeout=float(opts.get("timeout", "120")),
                temperature=float(opts.get("temperature", "0")),
                insecure=str(opts.get("insecure", "false")).lower() in ("1", "true", "yes"),
                max_retries=int(opts.get("max-retries", "3")),
                backoff=float(opts.get("backoff", "1.0")),
            )
        except (TypeError, ValueError) as exc:
            raise typer.BadParameter(f"Invalid adapter option: {exc}") from exc
    if kind in ("opencode", "oc"):
        try:
            return OpencodeAdapter(
                model_ref=opts.get("model", ""),
                config_path=opts.get("config"),
                timeout=float(opts.get("timeout", "120")),
                temperature=float(opts.get("temperature", "0")),
                max_retries=int(opts.get("max-retries", "3")),
                backoff=float(opts.get("backoff", "1.0")),
            )
        except (TypeError, ValueError) as exc:
            raise typer.BadParameter(f"Invalid adapter option: {exc}") from exc
    raise typer.BadParameter(f"Unknown adapter: {kind} (echo|file|openai-compat|opencode)")


def _load_config(path: str | None) -> dict:
    if path is None:
        return {}
    p = Path(path)
    try:
        text = p.read_text(encoding="utf-8")
    except OSError as exc:
        raise typer.BadParameter(f"Cannot read config {p}: {exc}") from exc
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as exc:
        raise typer.BadParameter(f"Invalid YAML in config {p}: {exc}") from exc
    return data or {}


def _breakdown_lines(breakdown: dict) -> str:
    return "\n".join(
        f"{name}: {v['pct']}% ({v['passed']}/{v['total']} passed)"
        for name, v in breakdown.items()
    )


def _print_dashboard(summary: dict, adapter_name: str) -> None:
    table = Table(title=f"Benchmark results — {adapter_name}")
    table.add_column("Task", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Score %", justify="right")
    table.add_column("Result", justify="center")
    for r in summary["results"]:
        table.add_row(
            r["task_id"],
            r["category"],
            r["difficulty"],
            f"{r['total']:.1f}",
            "[green]PASS[/green]" if r["passed"] else "[red]FAIL[/red]",
        )
    console.print(table)
    body = (
        f"Overall: {summary['overall_pct']}%\n"
        f"Pass rate: {summary['pass_rate']}% ({summary['passed']}/{summary['total']})\n\n"
        f"By category:\n{_breakdown_lines(summary['by_category'])}\n\n"
        f"By difficulty:\n{_breakdown_lines(summary['by_difficulty'])}"
    )
    console.print(Panel(body, title="Summary"))


def _write_markdown(summary: dict, adapter_name: str, path: Path) -> None:
    lines = ["# Benchmark Report", ""]
    meta = summary.get("meta", {})
    lines.append(f"- Adapter: `{adapter_name}`")
    if "threshold" in meta:
        lines.append(f"- Threshold: {meta['threshold']}")
    if "ran_at" in meta:
        lines.append(f"- Ran at: {meta['ran_at']}")
    lines.append(f"- Overall: **{summary['overall_pct']}%**")
    lines.append(
        f"- Pass rate: **{summary['pass_rate']}%** ({summary['passed']}/{summary['total']})"
    )
    lines += ["", "## By category", "", "| Category | Score % | Passed | Total |", "|---|---|---|---|"]
    for name, v in summary["by_category"].items():
        lines.append(f"| {name} | {v['pct']} | {v['passed']} | {v['total']} |")
    lines += ["", "## By difficulty", "", "| Difficulty | Score % | Passed | Total |", "|---|---|---|---|"]
    for name, v in summary["by_difficulty"].items():
        lines.append(f"| {name} | {v['pct']} | {v['passed']} | {v['total']} |")
    lines += ["", "## By task", "", "| Task | Category | Difficulty | Score % | Result |", "|---|---|---|---|---|"]
    for r in summary["results"]:
        lines.append(
            f"| {r['task_id']} | {r['category']} | {r['difficulty']} | {r['total']} "
            f"| {'PASS' if r['passed'] else 'FAIL'} |"
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _write_csv(summary: dict, path: Path) -> None:
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(
            ["task_id", "category", "difficulty", "score_pct", "passed", "scores", "output"]
        )
        for r in summary["results"]:
            writer.writerow(
                [
                    r["task_id"],
                    r["category"],
                    r["difficulty"],
                    r["total"],
                    r["passed"],
                    json.dumps(r["scores"]),
                    r["output"],
                ]
            )


@app.command()
def run(
    tasks: list[str] = typer.Argument(None, help="Task YAML files or dirs."),
    adapter: str = typer.Option(None, help="Adapter: echo|file|openai-compat|opencode."),
    opt: list[str] = typer.Option([], "--opt", help="Adapter option as key=value (repeatable)."),
    threshold: float = typer.Option(None, help="Pass threshold (0-100)."),
    out_dir: str = typer.Option(None, help="Directory for reports."),
    fail_under: float = typer.Option(None, help="Exit 1 if overall percent is below this."),
    tag: str = typer.Option(None, help="Subdirectory under out-dir for this run."),
    config: str = typer.Option(None, help="YAML config file."),
):
    _setup_logging()
    cfg = _load_config(config)

    def pick(cli_value, cfg_key, default):
        if cli_value is not None and cli_value != []:
            return cli_value
        if cfg_key in cfg and cfg[cfg_key] not in (None, []):
            return cfg[cfg_key]
        return default

    task_paths = pick(tasks, "tasks", ["tasks"])
    adapter_kind = str(pick(adapter, "adapter", "echo"))
    eff_threshold = float(pick(threshold, "threshold", 70.0))
    out = Path(pick(out_dir, "out_dir", "results"))
    if tag:
        out = out / tag

    adapter_opts = _parse_opts(opt)
    cfg_opts = cfg.get("adapter_opts")
    if isinstance(cfg_opts, dict):
        adapter_opts = {**{str(k): v for k, v in cfg_opts.items()}, **adapter_opts}

    loaded = load_tasks(task_paths)
    if not loaded:
        console.print("[red]No tasks found.[/red]")
        raise typer.Exit(1)

    pytest_ids = [t.id for t in loaded if "pytest" in (t.eval or {})]
    if pytest_ids and importlib.util.find_spec("pytest") is None:
        console.print(
            "[red]pytest is required for tasks using the pytest evaluator: "
            + ", ".join(pytest_ids)
            + "\nInstall it with: pip install 'agent-benchmark[test]'[/red]"
        )
        raise typer.Exit(1)

    model = _build_adapter(adapter_kind, adapter_opts)
    if adapter_kind == "echo":
        unknown = [t.id for t in loaded if t.id not in DEMO_OUTPUTS]
        if unknown:
            logger.warning(
                "Echo adapter has no demo output for %d task(s): %s — they will score ~0",
                len(unknown),
                ", ".join(unknown),
            )

    results = run_tasks(loaded, model, threshold=eff_threshold)
    summary = summarize(results)
    summary["meta"] = {
        "adapter": model.name,
        "threshold": eff_threshold,
        "ran_at": datetime.now(timezone.utc).isoformat(),
    }
    _print_dashboard(summary, model.name)

    out.mkdir(parents=True, exist_ok=True)
    (out / "results.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    _write_markdown(summary, model.name, out / "REPORT.md")
    _write_csv(summary, out / "results.csv")
    console.print(f"[green]Reports saved to {out}/[/green]")

    if fail_under is not None and summary["overall_pct"] < float(fail_under):
        console.print(
            f"[red]Overall {summary['overall_pct']}% is below --fail-under {fail_under}[/red]"
        )
        raise typer.Exit(1)


@app.command("list")
def list_tasks(
    tasks: list[str] = typer.Argument(None, help="Task YAML files or dirs."),
    config: str = typer.Option(None, help="YAML config file."),
):
    _setup_logging()
    cfg = _load_config(config)
    task_paths = tasks if tasks else cfg.get("tasks", ["tasks"])
    loaded = load_tasks(task_paths)
    if not loaded:
        console.print("[red]No tasks found.[/red]")
        raise typer.Exit(1)
    table = Table(title="Benchmark tasks")
    table.add_column("ID", style="cyan")
    table.add_column("Category", style="magenta")
    table.add_column("Difficulty", style="yellow")
    table.add_column("Evaluators", style="green")
    for t in loaded:
        evals = ", ".join(sorted((t.eval or {}).keys()))
        table.add_row(t.id, t.category, t.difficulty, evals)
    console.print(table)
    console.print(f"[green]{len(loaded)} tasks[/green]")


@app.command("models")
def list_models(
    config_path: str = typer.Option(None, "--config-path", help="Path to opencode.jsonc."),
):
    """List provider/model refs from opencode.jsonc (e.g. xpiki/claude-sonnet-5)."""
    _setup_logging()
    try:
        refs = list_opencode_models(config_path)
    except (OSError, ValueError) as exc:
        console.print(f"[red]{exc}[/red]")
        raise typer.Exit(1)
    table = Table(title="opencode models")
    table.add_column("Model ref", style="cyan")
    for r in refs:
        table.add_row(r)
    console.print(table)
    console.print(f"[green]{len(refs)} models[/green]")


def _write_comparison_markdown(comparison: dict, out: Path) -> None:
    order = comparison["model_order"]
    models = comparison["models"]
    lines = ["# Model Comparison", ""]
    lines.append("| Model | Overall % | Pass rate % | Passed | Total |")
    lines.append("|---|---|---|---|---|")
    for m in order:
        s = models[m]
        lines.append(f"| `{m}` | {s['overall_pct']} | {s['pass_rate']} | {s['passed']} | {s['total']} |")
    cats = sorted({c for m in order for c in models[m].get("by_category", {})})
    if cats:
        lines += ["", "## By category", "",
                  "| Category | " + " | ".join(f"`{m}`" for m in order) + " |",
                  "|" + "|".join(["---"] * (len(order) + 1)) + "|"]
        for c in cats:
            vals = [str(models[m].get("by_category", {}).get(c, {}).get("pct", 0.0))
                    for m in order]
            lines.append(f"| {c} | " + " | ".join(vals) + " |")
    diffs = sorted({d for m in order for d in models[m].get("by_difficulty", {})})
    if diffs:
        lines += ["", "## By difficulty", "",
                  "| Difficulty | " + " | ".join(f"`{m}`" for m in order) + " |",
                  "|" + "|".join(["---"] * (len(order) + 1)) + "|"]
        for d in diffs:
            vals = [str(models[m].get("by_difficulty", {}).get(d, {}).get("pct", 0.0))
                    for m in order]
            lines.append(f"| {d} | " + " | ".join(vals) + " |")
    lines += ["", "![comparison](comparison.png)", ""]
    (out / "REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


@app.command("compare")
def compare(
    models: str = typer.Option(..., "--models", help="Comma-separated opencode refs, e.g. 'xpiki/claude-sonnet-5,vyceai/deepseek-v4-flash'."),
    tasks: list[str] = typer.Argument(None, help="Task YAML files or dirs."),
    threshold: float = typer.Option(70.0, help="Pass threshold (0-100)."),
    out_dir: str = typer.Option("results/compare", help="Directory for comparison reports."),
    tag: str = typer.Option(None, help="Subdirectory under out-dir for this run."),
    config_path: str = typer.Option(None, "--config-path", help="Path to opencode.jsonc."),
    temperature: float = typer.Option(0.0, help="Sampling temperature."),
    timeout: float = typer.Option(120.0, help="Request timeout (seconds)."),
):
    """Run the same tasks against several opencode models and chart the winner."""
    _setup_logging()
    refs = [m.strip() for m in models.split(",") if m.strip()]
    if len(refs) < 2:
        console.print("[red]--models needs at least 2 comma-separated refs.[/red]")
        raise typer.Exit(1)
    task_paths = tasks or ["tasks"]
    loaded = load_tasks(task_paths)
    if not loaded:
        console.print("[red]No tasks found.[/red]")
        raise typer.Exit(1)
    adapters = []
    for ref in refs:
        try:
            adapters.append(OpencodeAdapter(ref, config_path=config_path,
                                            timeout=timeout, temperature=temperature))
        except (OSError, ValueError) as exc:
            console.print(f"[red]{exc}[/red]")
            raise typer.Exit(1)
    out = Path(out_dir)
    if tag:
        out = out / tag
    comparison = compare_models(loaded, adapters, threshold=threshold)
    out.mkdir(parents=True, exist_ok=True)
    (out / "comparison.json").write_text(json.dumps(comparison, indent=2), encoding="utf-8")
    try:
        png = save_comparison_png(comparison, out / "comparison.png")
    except ImportError:
        console.print("[red]matplotlib is required: pip install matplotlib[/red]")
        raise typer.Exit(1)
    _write_comparison_markdown(comparison, out)
    table = Table(title="Model comparison — overall %")
    table.add_column("Model", style="cyan")
    table.add_column("Overall %", justify="right")
    table.add_column("Pass rate %", justify="right")
    for m in comparison["model_order"]:
        s = comparison["models"][m]
        table.add_row(m, f"{s['overall_pct']:.1f}", f"{s['pass_rate']:.1f}")
    console.print(table)
    console.print(f"[green]Comparison saved to {out}/ (comparison.png)[/green]")
    _ = png
