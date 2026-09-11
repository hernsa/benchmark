# agent-benchmark

A small, plugin-based benchmark harness for AI agents. Point it at a folder of
YAML tasks, run them through an adapter (a real model, a file of saved outputs,
or the built-in echo adapter), and get percentage scores with an aggregate
dashboard — by category and by difficulty.

Task design borrows from the benchmarks that work: **HumanEval/MBPP** (hidden
pytest suites for code), **GSM8K** (`#### <answer>` final-answer extraction),
**BFCL** (tool-call name + argument matching), and plain structured-output
checks.

## Quickstart

```bash
pip install -e .

# Smoke-test the pipeline with canned answers (should score 100%)
benchmark tasks --adapter echo

# Score saved model outputs from a directory (one <task_id>.txt per task)
benchmark tasks --adapter file --opt dir=outputs

# Score a live OpenAI-compatible endpoint
benchmark tasks --adapter openai-compat \
  --opt model=gpt-4o-mini --opt base-url=https://api.openai.com/v1 \
  --opt api-key-env=OPENAI_API_KEY
```

Reports are written to `results/`: `results.json`, `REPORT.md`, `results.csv`.

## Output types (what gets scored)

| Output type | Evaluator | Inspired by |
| --- | --- | --- |
| Code completion | `pytest` (hidden tests, partial credit) | HumanEval, MBPP |
| Final answer | `final_answer` (`#### <answer>` extraction) | GSM8K |
| Tool calls | `function_call` (name + args, parallel, strict) | BFCL |
| Structured JSON | `json_match` (deep compare) | JSON-mode evals |
| Exact text | `exact_match` (whole output or last line) | MMLU-style |
| Code style | `code_quality` (compiles + length penalty) | — |

## Evaluator reference

All evaluators score 0–100. Configure them per task under `eval:`; only the
evaluators you list run, and `weight` (default 1.0) controls the weighted total.

- **`pytest`** — extracts the ```python block from the output, writes it as
  `solution.py`, runs hidden `test_code` against it. Score = passed tests /
  total tests × 100, so partially correct solutions earn partial credit.
- **`final_answer`** — extracts the answer with `regex` (default `####\s*(.+)`,
  falls back to the last non-empty line), then compares via `mode: exact`
  (normalized text) or `mode: numeric` (float compare, ignores `$`, `%`, commas).
- **`function_call`** — parses the first JSON object/array in the output.
  Single call: `function` + `args`. Parallel calls: `calls:` list (scored by
  index, averaged). Wrong tool name = 0; otherwise 40 (name) + 60 × (matched
  expected args / total). `strict: true` penalizes extra arguments.
- **`json_match`** — parses the first JSON value and deep-compares against
  `expected`. Dicts score by matched keys over the union of keys.
- **`exact_match`** — `target` compared against the whole output
  (`source: demo`) or the last non-empty line (default), normalized.
- **`code_quality`** — output must compile as Python; length penalty applies.

## Task format

```yaml
id: coding-003-valid-parentheses
title: "Valid parentheses"
category: coding          # any string; reported per category
difficulty: medium        # easy | medium | hard; reported per difficulty
prompt: |
  Write a Python function `is_valid(s: str) -> bool` ...
expected_output: ""       # optional fallback target
eval:
  pytest:
    weight: 1.0
    test_code: |
      from solution import is_valid

      def test_simple():
          assert is_valid("()") is True
```

## Built-in task packs (16 tasks)

| Pack | Tasks | Difficulty spread |
| --- | --- | --- |
| `tasks/coding` | 5 (reverse string, FizzBuzz, valid parentheses, binary search, group anagrams) | easy → hard |
| `tasks/debugging` | 3 (off-by-one, mutable default, swallowed exception) | easy → hard |
| `tasks/tool-use` | 3 (single call, parallel calls, nested args) | easy → hard |
| `tasks/reasoning` | 3 (train speed, discount+tax, age puzzle) | easy → hard |
| `tasks/instruction-following` | 2 (exact JSON, exact keys) | easy → medium |

## Adapters

| Adapter | What it does |
| --- | --- |
| `echo` | Returns canned correct answers for every built-in task — verifies the harness itself. |
| `file` | Reads `<task_id>.txt` from a directory — score outputs you saved elsewhere. |
| `openai-compat` | Calls any OpenAI-compatible chat completions endpoint (OpenAI, vLLM, Ollama, ...). |

## Adding your own tasks

Drop YAML files into any directory and pass it: `benchmark tasks my-tasks/`.
Files starting with `_` are skipped; a YAML file may contain a single task or
a list of tasks.

## Development

```bash
pip install -e .
python -m pytest
```

## License

MIT
