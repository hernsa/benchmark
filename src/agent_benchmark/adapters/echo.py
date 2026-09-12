"""Echo adapter: returns canned demo outputs for the 16 built-in tasks so the
pipeline can be tested end-to-end without any model.

Demo-only: unknown task ids get a literal "echo:<id>" placeholder and will
score ~0. Use the file or openai-compat adapter for real models."""


DEMO_OUTPUTS: dict[str, str] = {
    "coding-001-reverse-string": (
        "```python\n"
        "def reverse_string(s: str) -> str:\n"
        "    return s[::-1]\n"
        "```"
    ),
    "coding-002-fizzbuzz": (
        "```python\n"
        "def fizzbuzz(n: int) -> list[str]:\n"
        "    out = []\n"
        "    for i in range(1, n + 1):\n"
        "        if i % 15 == 0:\n"
        "            out.append(\"FizzBuzz\")\n"
        "        elif i % 3 == 0:\n"
        "            out.append(\"Fizz\")\n"
        "        elif i % 5 == 0:\n"
        "            out.append(\"Buzz\")\n"
        "        else:\n"
        "            out.append(str(i))\n"
        "    return out\n"
        "```"
    ),
    "coding-003-valid-parentheses": (
        "```python\n"
        "def is_valid(s: str) -> bool:\n"
        "    pairs = {\")\": \"(\", \"]\": \"[\", \"}\": \"{\"}\n"
        "    stack = []\n"
        "    for ch in s:\n"
        "        if ch in \"([{\":\n"
        "            stack.append(ch)\n"
        "        elif ch in pairs:\n"
        "            if not stack or stack.pop() != pairs[ch]:\n"
        "                return False\n"
        "    return not stack\n"
        "```"
    ),
    "coding-004-binary-search": (
        "```python\n"
        "def binary_search(arr: list[int], target: int) -> int:\n"
        "    lo, hi = 0, len(arr) - 1\n"
        "    while lo <= hi:\n"
        "        mid = (lo + hi) // 2\n"
        "        if arr[mid] == target:\n"
        "            return mid\n"
        "        elif arr[mid] < target:\n"
        "            lo = mid + 1\n"
        "        else:\n"
        "            hi = mid - 1\n"
        "    return -1\n"
        "```"
    ),
    "coding-005-group-anagrams": (
        "```python\n"
        "def group_anagrams(words: list[str]) -> list[list[str]]:\n"
        "    buckets = {}\n"
        "    for w in words:\n"
        "        key = \"\".join(sorted(w))\n"
        "        buckets.setdefault(key, []).append(w)\n"
        "    groups = [sorted(g) for g in buckets.values()]\n"
        "    return sorted(groups, key=lambda g: g[0])\n"
        "```"
    ),
    "debugging-001-offbyone": (
        "```python\n"
        "def total(n: int) -> int:\n"
        "    return sum(range(n + 1))\n"
        "```"
    ),
    "debugging-002-mutable-default": (
        "```python\n"
        "def append_to(item, lst=None):\n"
        "    if lst is None:\n"
        "        lst = []\n"
        "    lst.append(item)\n"
        "    return lst\n"
        "```"
    ),
    "debugging-003-swallowed-exception": (
        "```python\n"
        "def parse_int(s):\n"
        "    return int(s)\n"
        "```"
    ),
    "tooluse-001-simple-call": (
        '{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}'
    ),
    "tooluse-002-parallel-calls": (
        '[{"name": "get_weather", "arguments": {"city": "Paris", "unit": "celsius"}}, '
        '{"name": "get_weather", "arguments": {"city": "Tokyo", "unit": "celsius"}}]'
    ),
    "tooluse-003-nested-args": (
        '{"name": "create_user", "arguments": {"name": "Ada Lovelace", '
        '"address": {"street": "1 Main St", "city": "London"}, "tags": ["admin"]}}'
    ),
    "reasoning-001-train-speed": (
        "Speed = distance / time = 120 / 1.5 = 80 km/h.\n\n#### 80"
    ),
    "reasoning-002-discount": (
        "Sale price: 250 * 0.8 = 200. With 10% tax: 200 * 1.1 = 220.\n\n#### 220"
    ),
    "reasoning-003-ages": (
        "Let Ben be b: 3b + 8 = 2(b + 8) -> 3b + 8 = 2b + 16 -> b = 8.\n\n#### 8"
    ),
    "instruction-001-format-json": '{"status": "ok", "count": 3}',
    "instruction-002-schema-json": '{"alpha": 1, "beta": 2, "gamma": 3}',
}


class EchoAdapter:
    """Returns a canned correct answer for known task ids (for demos/tests)."""

    name = "echo"

    def generate(self, task) -> str:
        return DEMO_OUTPUTS.get(task.id, f"echo:{task.id}")
