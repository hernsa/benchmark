"""Summarize TaskResults into report structures."""


def _group(results, key: str) -> dict:
    buckets: dict[str, dict] = {}
    for r in results:
        name = getattr(r, key)
        b = buckets.setdefault(name, {"scores": [], "passed": 0, "total": 0})
        b["scores"].append(r.total)
        b["passed"] += 1 if r.passed else 0
        b["total"] += 1
    out = {}
    for name, b in buckets.items():
        avg = round(sum(b["scores"]) / len(b["scores"]), 1) if b["scores"] else 0.0
        out[name] = {"pct": avg or 0.0, "passed": b["passed"], "total": b["total"]}
    return dict(sorted(out.items()))


def summarize(results) -> dict:
    totals = [r.total for r in results]
    passed = sum(1 for r in results if r.passed)
    total = len(results)
    return {
        "overall_pct": round(sum(totals) / total, 1) if total else 0.0,
        "total": total,
        "passed": passed,
        "pass_rate": round(passed / total * 100, 1) if total else 0.0,
        "by_category": _group(results, "category"),
        "by_difficulty": _group(results, "difficulty"),
        "results": [
            {
                "task_id": r.task_id,
                "category": r.category,
                "difficulty": r.difficulty,
                "output": r.output,
                "scores": r.scores,
                "total": r.total,
                "passed": r.passed,
                "error": r.error,
            }
            for r in results
        ],
    }
