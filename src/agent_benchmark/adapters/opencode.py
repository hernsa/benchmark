"""Adapter that reads providers/models straight from opencode.jsonc.

opencode.jsonc model ids look like ``xpiki/claude-sonnet-5`` — the part
before the slash is the provider key under ``\"provider\"``, the rest is the
model id sent to that provider's OpenAI-compatible endpoint.
"""

import json
import os
import re
import time
from pathlib import Path

import httpx

DEFAULT_CONFIG = Path(os.environ.get(
    "OPENCODE_CONFIG",
    r"C:\Users\Admin\.config\opencode\opencode.jsonc",
))


def _strip_jsonc_comments(text: str) -> str:
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    text = re.sub(r"(^|[^:])//.*$", r"\1", text, flags=re.MULTILINE)
    return text


def load_opencode_providers(config_path: str | os.PathLike | None = None) -> dict:
    p = Path(config_path) if config_path else DEFAULT_CONFIG
    raw = Path(p).read_text(encoding="utf-8")
    data = json.loads(_strip_jsonc_comments(raw))
    providers = data.get("provider", {})
    if not providers:
        raise ValueError(f"No providers found in {p}")
    return providers


def list_opencode_models(config_path: str | os.PathLike | None = None) -> list[str]:
    providers = load_opencode_providers(config_path)
    out = []
    for prov_name, prov in providers.items():
        for model_id in (prov.get("models") or {}):
            out.append(f"{prov_name}/{model_id}")
    return sorted(out)


class OpencodeAdapter:
    """OpenAI-compatible adapter resolved from opencode.jsonc."""

    def __init__(
        self,
        model_ref: str,
        config_path: str | os.PathLike | None = None,
        timeout: float = 120.0,
        temperature: float = 0.0,
        max_retries: int = 3,
        backoff: float = 1.0,
    ):
        if "/" not in model_ref:
            raise ValueError(
                f"Model ref {model_ref!r} must look like 'provider/model-id' "
                "(e.g. 'xpiki/claude-sonnet-5')"
            )
        prov_name, model_id = model_ref.split("/", 1)
        providers = load_opencode_providers(config_path)
        if prov_name not in providers:
            raise ValueError(
                f"Unknown provider {prov_name!r} in opencode config "
                f"(have: {', '.join(sorted(providers))})"
            )
        prov = providers[prov_name]
        opts = prov.get("options", {})
        base_url = str(opts.get("baseURL", "")).rstrip("/")
        api_key = str(opts.get("apiKey", ""))
        if not base_url:
            raise ValueError(f"Provider {prov_name!r} has no baseURL in opencode config")
        if not api_key:
            raise ValueError(f"Provider {prov_name!r} has no apiKey in opencode config")
        models = prov.get("models") or {}
        if model_id not in models:
            raise ValueError(
                f"Unknown model {model_id!r} for provider {prov_name!r} "
                f"(have: {', '.join(sorted(models))})"
            )
        self.provider = prov_name
        self.model = model_id
        self.base_url = base_url
        self.api_key = api_key
        self.timeout = timeout
        self.temperature = temperature
        self.max_retries = max(1, max_retries)
        self.backoff = backoff
        self.name = f"{prov_name}/{model_id}"

    def generate(self, task) -> str:
        payload = {
            "model": self.model,
            "messages": [{"role": "user", "content": task.prompt}],
            "temperature": self.temperature,
        }
        headers = {"Authorization": f"Bearer {self.api_key}"}
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
                f"opencode provider {self.provider} failed after "
                f"{self.max_retries} attempts: {last_exc}"
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
