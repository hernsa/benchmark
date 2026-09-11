from ..models import Task


class EchoAdapter:
    name = "echo"

    def generate(self, task: Task) -> str:
        if task.id == "coding-reverse-string":
            return "olleh"
        if task.id == "coding-debug-offbyone":
            return "fixed"
        return f"echo:{task.id}"
