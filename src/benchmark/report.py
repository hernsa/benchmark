from .models import TaskResult


def summarize(results: list[TaskResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    overall = round(sum(r.total for r in results) / total, 1) if total else 0.0
    by_category: dict[str, dict] = {}
    for r in results:
        cat = by_category.setdefault(r.category, {"scores": [], "passed": 0, "total": 0})
        cat["scores"].append(r.total)
        cat["total"] += 1
        cat["passed"] += 1 if r.passed else 0
    cats = {
        name: {
            "pct": round(sum(v["scores"]) / len(v["scores"]), 1) if v["scores"] else 0.0,
            "passed": v["passed"],
            "total": v["total"],
        }
        for name, v in sorted(by_category.items())
    }
    return {
        "overall_pct": overall,
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0.0,
        "by_category": cats,
        "results": [
            {
                "task_id": r.task_id,
                "category": r.category,
                "total": r.total,
                "passed": r.passed,
                "scores": r.scores,
            }
            for r in results
        ],
    }
