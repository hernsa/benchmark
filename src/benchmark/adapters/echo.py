from ..models import Task


class EchoAdapter:
    """Deterministic stub adapter: returns canned output per task id.

    Ships with passing demo answers for the built-in task pack so
    ``benchmark run --adapter echo`` shows a green dashboard instantly.
    """

    name = "echo"

    DEMO_OUTPUTS = {
        "coding-002-fizzbuzz": (
            "```python\n"
            "def fizzbuzz(n):\n"
            "    out = []\n"
            "    for i in range(1, n + 1):\n"
            "        s = ''\n"
            "        if i % 3 == 0:\n"
            "            s += 'Fizz'\n"
            "        if i % 5 == 0:\n"
            "            s += 'Buzz'\n"
            "        out.append(s or str(i))\n"
            "    return out\n"
            "```"
        ),
        "debugging-001-offbyone": (
            "```python\n"
            "def total(items):\n"
            "    s = 0\n"
            "    for i in range(len(items)):\n"
            "        s += items[i]\n"
            "    return s\n"
            "```"
        ),
        "tooluse-001-format-json": '{"status": "ok", "count": 3}',
    }

    def __init__(self, outputs: dict | None = None) -> None:
        merged = dict(self.DEMO_OUTPUTS)
        if outputs:
            merged.update(outputs)
        self._outputs = merged

    def generate(self, task: Task) -> str:
        if task.id in self._outputs:
            return self._outputs[task.id]
        if task.id == "coding-reverse-string":
            return "olleh"
        if task.id == "coding-debug-offbyone":
            return "fixed"
        return f"echo:{task.id}"
