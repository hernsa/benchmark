# Agent Benchmark

Simple plugin-based benchmark runner for AI coding / debugging / tool-use agents. Sends tasks, auto-scores outputs as percentages, and prints a simple aggregate dashboard.

## Quickstart

```bash
pip install -e .
benchmark tasks --adapter echo
benchmark tasks --adapter file --opt dir=outputs
benchmark tasks --adapter openai-compat --opt model=glm-4-flash --opt base-url=https://open.bigmodel.cn/api/paas/v4 --opt api-key-env=GLM_API_KEY
benchmark --help
```

## How scoring works

Each task defines weighted evaluators (`exact_match`, `pytest`, `code_quality`). Each evaluator returns 0-100. Task score = weighted mean. Run summary shows overall %, pass rate, and per-category %.

## Adapters

- `echo` — deterministic demo adapter (no API key, for smoke tests)
- `file` (`--opt dir=outputs`) — reads `<task_id>.txt` (paste any model's output, then score it)
- `openai-compat` (`--opt model=... --opt base-url=... --opt api-key-env=...`) — any OpenAI-compatible endpoint (OpenAI, local servers, GLM flash endpoints exposing a compatible API). Keys come from env vars only.

## Task format

```yaml
id: coding-reverse-string
title: Reverse a string function
category: coding
difficulty: easy
prompt: "Write a Python function ..."
eval:
  exact_match:
    weight: 1.0
    target: "olleh"
    source: demo
```

## Layout

- `src/benchmark/` — runner, loader, adapters, evaluators, report, CLI
- `tasks/` — built-in YAML task packs
- `examples/` — example configs (e.g. `benchmark --config examples/demo-config.yaml`)
- `results/` — generated JSON/CSV/Markdown (gitignored)
