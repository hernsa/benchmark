import os

import httpx

from ..models import Task


class OpenAICompatAdapter:
    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key_env: str = "OPENAI_API_KEY",
    ):
        self.name = f"openai-compat:{model}"
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env

    def generate(self, task: Task) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"Missing env var {self.api_key_env}")
        r = httpx.post(
            f"{self.base_url}/chat/completions",
            headers={"Authorization": f"Bearer {key}"},
            json={
                "model": self.model,
                "messages": [{"role": "user", "content": task.prompt}],
                "temperature": 0,
            },
            timeout=120,
        )
        r.raise_for_status()
        return r.json()["choices"][0]["message"]["content"]
