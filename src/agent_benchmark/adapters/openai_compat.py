"""OpenAI-compatible chat-completions adapter with retries and shape validation."""

import os
import time

import httpx


class OpenAICompatAdapter:
    def __init__(
        self,
        model: str,
        base_url: str = "https://api.openai.com/v1",
        api_key_env: str = "OPENAI_API_KEY",
        timeout: float = 120.0,
        temperature: float = 0.0,
        insecure: bool = False,
        max_retries: int = 3,
        backoff: float = 1.0,
    ):
        if not base_url.startswith("https://") and not insecure:
            raise ValueError(
                f"Refusing non-HTTPS base_url {base_url!r} (pass insecure=true to override)"
            )
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.api_key_env = api_key_env
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max(1, max_retries)
        self.backoff = backoff
        self.name = f"openai-compat:{model}"

    def generate(self, task) -> str:
        key = os.environ.get(self.api_key_env, "")
        if not key:
            raise RuntimeError(f"Missing env var {self.api_key_env!r}")
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": task.prompt}],
            "temperature": self.temperature,
        }
        headers = {"Authorization": f"Bearer {key}"}
        url = f"{self.base_url}/chat/completions"
        last_exc: Exception | None = None
        for attempt in range(self.max_retries):
            try:
                r = httpx.post(url, headers=headers, json=payload, timeout=self.timeout)
                r.raise_for_status()
            except httpx.TransportError as exc:
                last_exc = exc
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code if exc.response is not None else None
                if status is None or status not in (429, *range(500, 600)):
                    raise
                last_exc = exc
            else:
                break
            if attempt < self.max_retries - 1:
                time.sleep(self.backoff * (2 ** attempt))
        else:
            raise RuntimeError(
                f"OpenAI-compatible API failed after {self.max_retries} attempts: {last_exc}"
            )
        try:
            data = r.json()
        except ValueError as exc:
            raise RuntimeError(f"Invalid JSON from API: {r.text[:200]}") from exc
        try:
            content = data["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise RuntimeError(f"Unexpected API response shape: {str(data)[:200]}") from exc
        if not isinstance(content, str):
            raise RuntimeError("Model returned null/non-string content")
        return content
