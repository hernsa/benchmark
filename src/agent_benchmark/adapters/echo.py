"""Echo adapter: returns canned demo outputs for the 28 built-in tasks so the
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
        "First leg 120 km at 60 km/h takes 2 h. Second leg 60 km at 120 km/h takes 0.5 h. Total 180 km in 2.5 h gives 72 km/h.\n\n#### 72"
    ),
    "reasoning-002-discount": (
        "20 percent off 250 is 200. 10 percent tax adds 20 for 220. Plus 15 shipping is 235.\n\n#### 235"
    ),
    "reasoning-003-ages": (
        "Let Ben be b now. Anna is 3b. In 8 years Anna is 3b + 8 and Ben is b + 8 -> 3b + 8 = 2b + 16 -> b = 8.\n\n#### 8"
    ),
    "instruction-001-format-json": '{"status": "ok", "count": 3}',
    "instruction-002-schema-json": '{"alpha": 1, "beta": 2, "gamma": 3}',
    "coding-006-email-validate": (
        "```python\ndef is_valid_email(s):\n    if not isinstance(s, str):\n        return False\n    if not s or s.count(\"@\") != 1:\n        return False\n    local, domain = s.split(\"@\")\n    if len(local) not in range(1, 65):\n        return False\n    ok_local = set(\"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789._-+\")\n    if any(c not in ok_local for c in local):\n        return False\n    if \"..\" in s:\n        return False\n    if \".\" not in domain:\n        return False\n    labels = domain.split(\".\")\n    ok_label = set(\"abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-\")\n    for lab in labels:\n        if len(lab) not in range(1, 64):\n            return False\n        if lab.startswith(\"-\") or lab.endswith(\"-\"):\n            return False\n        if any(c not in ok_label for c in lab):\n            return False\n    if len(labels[-1]) not in range(2, 64):\n        return False\n    return True\n```"
    ),
    "coding-007-matrix-multiply": (
        "```python\ndef matmul(a, b=None):\n    if b is None:\n        return []\n    if not a or not b:\n        return []\n    if not a[0] or not b[0]:\n        return []\n    m = len(a)\n    n = len(a[0])\n    p = len(b[0])\n    if n != len(b):\n        return None\n    out = []\n    for i in range(m):\n        row = []\n        for j in range(p):\n            cell = 0\n            for k in range(n):\n                cell = cell + a[i][k] * b[k][j]\n            row.append(cell)\n        out.append(row)\n    return out\n```"
    ),
    "coding-008-roman-numerals": (
        "```python\ndef add_roman(a, b):\n    vals = {\"I\": 1, \"V\": 5, \"X\": 10, \"L\": 50, \"C\": 100, \"D\": 500, \"M\": 1000}\n    table = [(1000, \"M\"), (900, \"CM\"), (500, \"D\"), (400, \"CD\"), (100, \"C\"), (90, \"XC\"), (50, \"L\"), (40, \"XL\"), (10, \"X\"), (9, \"IX\"), (5, \"V\"), (4, \"IV\"), (1, \"I\")]\n    def to_int(s):\n        if s == \"\":\n            return 0\n        total = 0\n        prev = 0\n        for ch in reversed(s):\n            if ch not in vals:\n                raise ValueError(\"invalid roman\")\n            v = vals[ch]\n            if min(v, prev) == v and v != prev:\n                total = total - v\n            else:\n                total = total + v\n                prev = v\n        return total\n    def to_roman(n):\n        if n == 0:\n            return \"\"\n        out = \"\"\n        for v, sym in table:\n            q = n // v\n            out = out + sym * q\n            n = n - q * v\n        return out\n    for s in (a, b):\n        if s != \"\" and to_roman(to_int(s)) != s:\n            raise ValueError(\"invalid roman\")\n    return to_roman(to_int(a) + to_int(b))\n```"
    ),
    "coding-009-password-strength": (
        "```python\ndef password_strength(s):\n    import string\n    from collections import Counter\n    score = 0.0\n    n = len(s)\n    if n in range(20, 10000):\n        score = score + 100\n    elif n in range(15, 20):\n        score = score + 60\n    elif n in range(12, 15):\n        score = score + 40\n    elif n in range(9, 12):\n        score = score + 20\n    low = any(c.islower() for c in s)\n    upp = any(c.isupper() for c in s)\n    if low:\n        score = score + 10\n    if upp:\n        score = score + 15\n    if any(c.isdigit() for c in s):\n        score = score + 15\n    if any(c in string.punctuation for c in s):\n        score = score + 20\n    if not any(v not in range(0, 3) for v in Counter(s).values()):\n        score = score + 10\n    if low and upp:\n        score = score + 10\n    uniq = len(set(s))\n    score = score + min(0.1 * (uniq ** 1.5), 15)\n    return float(min(score, 100.0))\n```"
    ),
    "debugging-004-pipeline-order": (
        "```python\ndef get_sorted_items():\n    items = [{\"name\": \"low\", \"priority\": 5}, {\"name\": \"urgent\", \"priority\": 1}, {\"name\": \"normal\", \"priority\": 3}]\n    return sorted(items, key=lambda d: d[\"priority\"])\n```"
    ),
    "debugging-005-race-condition": (
        "```python\nimport threading\ncounter = 0\n_lock = threading.Lock()\ndef set_counter(n):\n    global counter\n    with _lock:\n        counter = n\ndef get_counter():\n    with _lock:\n        return counter\ndef increment_counter():\n    global counter\n    with _lock:\n        counter = counter + 1\n        return counter\n```"
    ),
    "debugging-006-deepcopy-bug": (
        "```python\nimport copy\ndef clone_config(cfg):\n    return copy.deepcopy(cfg)\n```"
    ),
    "instruction-003-nested-config": (
        '{"server": {"host": "localhost", "port": 3000, "ssl": true}, "logging": {"level": "info", "outputs": ["/var/log/app.log"]}, "features": ["caching", "monitoring"], "version": "1.0.0"}'
    ),
    "reasoning-004-logic-puzzle": (
        "Alice is not red, so Alice is green or blue. Carol is blue, so Alice is not blue. Alice is green and owns the bird. Bob owns the cat. The dog belongs to Carol.\n\n#### Carol"
    ),
    "reasoning-005-optimization": (
        "Corners give 1200 and 2000. Intersection of 2a+b=100 and a+3b=120 gives a=36, b=28, profit 36*40+28*30=1440+840=2280.\n\n#### 2280"
    ),
    "reasoning-006-clock-math": (
        "Relative speed is 5.5 degrees per minute. 180/5.5 is 32 minutes 44 seconds after 3.\n\n#### 15:32:44"
    ),
    "agentic-001-multi-step": (
        '{"total_errors": 5, "total_warnings": 4, "by_file": {"app.log": 4, "error.log": 4, "debug.log": 3}, "time_range": {"start": "2024-01-15 08:30:00", "end": "2024-01-15 14:22:00"}}'
    ),
}


class EchoAdapter:
    """Returns a canned correct answer for known task ids (for demos/tests)."""

    name = "echo"

    def generate(self, task) -> str:
        return DEMO_OUTPUTS.get(task.id, f"echo:{task.id}")
