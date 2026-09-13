"""Leaderboard-style PNG charts for multi-model comparisons.

Four panels, like other benchmark leaderboards:
1. Overall score per model (bar)
2. Score by category per model (grouped bar)
3. Score by difficulty per model (grouped bar)
4. Pass rate per model (bar)
"""

from pathlib import Path


def save_comparison_png(comparison: dict, path: str | Path) -> Path:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    order = comparison.get("model_order") or list(comparison["models"])
    models = comparison["models"]
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    overall = [models[m]["overall_pct"] for m in order]
    pass_rate = [models[m]["pass_rate"] for m in order]
    categories = sorted({c for m in order for c in models[m].get("by_category", {})})
    difficulties = sorted({d for m in order for d in models[m].get("by_difficulty", {})})

    fig, axes = plt.subplots(2, 2, figsize=(14, 9))
    fig.suptitle("Agent Benchmark — model comparison", fontsize=14, fontweight="bold")
    x = range(len(order))
    short = [m.split("/", 1)[-1][:22] for m in order]

    ax = axes[0, 0]
    bars = ax.bar(list(x), overall)
    ax.set_title("Overall score %")
    ax.set_xticks(list(x), short, rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 100)
    for b, v in zip(bars, overall):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{v:.1f}",
                ha="center", fontsize=8)

    ax = axes[0, 1]
    n = max(len(categories), 1)
    w = min(0.8 / n, 0.35)
    for i, cat in enumerate(categories):
        vals = [models[m].get("by_category", {}).get(cat, {}).get("pct", 0.0) for m in order]
        pos = [p + (i - (n - 1) / 2) * w for p in x]
        ax.bar(pos, vals, width=w, label=cat[:18])
    ax.set_title("Score by category %")
    ax.set_xticks(list(x), short, rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=7, ncol=2)

    ax = axes[1, 0]
    n = max(len(difficulties), 1)
    w = min(0.8 / n, 0.35)
    for i, diff in enumerate(difficulties):
        vals = [models[m].get("by_difficulty", {}).get(diff, {}).get("pct", 0.0)
                for m in order]
        pos = [p + (i - (n - 1) / 2) * w for p in x]
        ax.bar(pos, vals, width=w, label=diff)
    ax.set_title("Score by difficulty %")
    ax.set_xticks(list(x), short, rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 100)
    ax.legend(fontsize=8)

    ax = axes[1, 1]
    bars = ax.bar(list(x), pass_rate, color="seagreen")
    ax.set_title("Pass rate %")
    ax.set_xticks(list(x), short, rotation=20, ha="right", fontsize=8)
    ax.set_ylim(0, 100)
    for b, v in zip(bars, pass_rate):
        ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 1, f"{v:.1f}",
                ha="center", fontsize=8)

    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return path
