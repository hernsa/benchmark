# agent-benchmark

A small benchmark harness for AI agents. Point it at a folder of YAML tasks,
run them through an adapter (a real model, a directory of saved outputs, or
the built-in echo adapter), and get percentage scores with an aggregate
dashboard — by category and by difficulty.

Task design borrows from the benchmarks that work: **HumanEval/MBPP** (hidden
pytest suites for code), **GSM8K** (`#### <answer>` final-answer extraction),
**BFCL** (tool-call name + argument matching), and plain structured-output
checks.

## Quickstart

```bash
pip install -e .

# See the built-in task packs
benchmark list

# Smoke-test the pipeline with canned answers (should score 100%)
benchmark run --adapter echo

# Score saved model outputs from a directory (one <task_id>.txt per task)
benchmark run --adapter file --opt dir=outputs

# Score a live OpenAI-compatible endpoint
benchmark run --adapter openai-compat \
  --opt model=gpt-4o-mini --opt base-url=https://api.openai.com/v1 \
  --opt api-key-env=OPENAI_API_KEY
```

Reports are written to `results/`: `results.json` (includes raw model
outputs), `REPORT.md`, and `results.csv`. Use `--out-dir` to change the
location and `--tag nightly` to nest a run in a subdirectory.

Precedence: CLI flags > config file > built-in defaults. See
`examples/demo-config.yaml` for a config template and
`examples/demo-results/` for a sample echo run.

## CLI options (`benchmark run`)

| Option | Default | Meaning |
| --- | --- | --- |
| `tasks...` | `tasks` | Task YAML files or directories |
| `--adapter` | `echo` | `echo`, `file`, or `openai-compat` |
| `--opt k=v` | — | Adapter option, repeatable |
| `--threshold` | `70.0` | Per-task pass threshold (0–100) |
| `--out-dir` | `results` | Report output directory |
| `--tag` | — | Subdirectory under `--out-dir` for this run |
| `--fail-under` | — | Exit code 1 if the overall score is below this |
| `--config` | — | YAML config file |

Exit codes: `0` = ran fine (and passed `--fail-under` if given), `1` = no
tasks found, missing pytest for pytest-eval tasks, or overall score below
`--fail-under`.

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
evaluators you list run, and `weight` (default 1.0) controls the weighted
total. Unknown evaluator names are skipped with a warning; missing required
keys fail loudly at load time.

- **`pytest`** — extracts the last ```python block from the output, writes it
  as `solution.py`, runs hidden `test_code` against it. Score = passed tests /
  total tests × 100, so partially correct solutions earn partial credit.
  Optional per-task `timeout` (seconds, default 60); timeouts raise an error
  recorded per task instead of silently scoring 0.
- **`final_answer`** — extracts the answer with `regex` (default `####\s*(.+)`,
  falls back to the last non-empty line), then compares via `mode: exact`
  (normalized text) or `mode: numeric`. Numeric mode pulls the last number out
  of the text (`#### 80 km/h` → 80) and supports `tolerance` (absolute,
  default 1e-6) or `rel_tolerance` (relative band).
- **`function_call`** — parses the last JSON value in the output (fenced
  blocks tried last-first, then every `{`/`[` position, so prose-wrapped calls
  still parse). Single call: `function` + `args`. Parallel calls: `calls:`
  list (scored by index, averaged); a `{"calls": [...]}` wrapper is unwrapped
  automatically. Wrong tool name = 0; otherwise 40 (name) + 60 × (matched
  expected args / total). `strict: true` penalizes extra arguments.
- **`json_match`** — parses the first JSON value and deep-compares against
  `expected`: nested dicts are scored leaf-by-leaf over the union of paths.
- **`exact_match`** — `target` compared against the whole output
  (`source: demo`) or the last non-empty line (default), normalized.
- **`code_quality`** — the extracted code must compile as Python; length
  penalty applies.

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

`.yml` and `.yaml` files both load; files starting with `_` are skipped; a
YAML file may contain a single task or a list of tasks; duplicate ids keep
the first occurrence with a warning.

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
| `echo` | Returns canned correct answers for the 16 built-in tasks — verifies the harness itself. Demo-only: unknown task ids get `echo:<id>` and score ~0 (a warning is logged). |
| `file` | Reads `<task_id>.txt` from a directory (`--opt dir=...`) — score outputs you saved elsewhere. Missing files score 0 with a warning. |
| `openai-compat` | Calls any OpenAI-compatible chat completions endpoint (OpenAI, vLLM, Ollama, ...). |

`openai-compat` options:

| Option | Default | Meaning |
| --- | --- | --- |
| `model` | `gpt-4o-mini` | Model name sent to the endpoint |
| `base-url` | `https://api.openai.com/v1` | API root; non-HTTPS is refused unless `insecure=true` |
| `api-key-env` | `OPENAI_API_KEY` | Env var holding the bearer token |
| `timeout` | `120` | Request timeout (seconds) |
| `temperature` | `0` | Sampling temperature |
| `insecure` | `false` | Allow non-HTTPS `base-url` (e.g. localhost) |
| `max-retries` | `3` | Retries on network errors, 429, and 5xx |
| `backoff` | `1.0` | Base seconds for exponential retry backoff |

Malformed API responses (missing `choices`, null content, invalid JSON) raise
a clear error instead of a raw traceback.

## Security notes

The `pytest` evaluator **executes model-generated code on your machine** —
it writes the model's code to a temp directory and runs it with your Python
interpreter. Mitigations included: obvious secret env vars (names containing
`API_KEY`, `TOKEN`, `SECRET`, `PASSWORD`, `CREDENTIAL`) are stripped from the
subprocess environment, execution happens in an isolated temp directory with
a per-task timeout. But there is no sandbox: **only run this against models
you trust, or inside a CI container / throwaway VM.** Never point it at
untrusted model outputs on a machine with access to anything you care about.

## Adding your own tasks

Drop YAML files into any directory and pass it: `benchmark run my-tasks/`.
Files starting with `_` are skipped; a YAML file may contain a single task or
a list of tasks.

## Development

```bash
pip install -e '.[test]'
ruff check .    # lint (config in pyproject.toml)
python -m pytest
```

## License

MIT
