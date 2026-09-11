from .models import TaskResult


def _group(results: list[TaskResult], key) -> dict[str, dict]:
    buckets: dict[str, dict] = {}
    for r in results:
        b = buckets.setdefault(key(r), {"scores": [], "passed": 0, "total": 0})
        b["scores"].append(r.total)
        b["total"] += 1
        b["passed"] += 1 if r.passed else 0
    return {
        name: {
            "pct": round(sum(v["scores"]) / len(v["scores"]), 1) if v["scores"] else 0.0,
            "passed": v["passed"],
            "total": v["total"],
        }
        for name, v in sorted(buckets.items())
    }


def summarize(results: list[TaskResult]) -> dict:
    total = len(results)
    passed = sum(1 for r in results if r.passed)
    overall = round(sum(r.total for r in results) / total, 1) if total else 0.0
    return {
        "overall_pct": overall,
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0.0,
        "by_category": _group(results, lambda r: r.category),
        "by_difficulty": _group(results, lambda r: r.difficulty),
        "results": [
            {
                "task_id": r.task_id,
                "category": r.category,
                "difficulty": r.difficulty,
                "total": r.total,
                "passed": r.passed,
                "scores": r.scores,
            }
            for r in results
        ],
    }
