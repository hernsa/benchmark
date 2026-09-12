import httpx
import pytest

from agent_benchmark.adapters.openai_compat import OpenAICompatAdapter
from agent_benchmark.models import Task


class FakeResponse:
    def __init__(self, payload=None, status_code=200, json_error=None):
        self._payload = payload or {}
        self.status_code = status_code
        self._json_error = json_error
        self.text = "fake"

    def raise_for_status(self):
        if self.status_code >= 400:
            raise httpx.HTTPStatusError("err", request=None, response=None)

    def json(self):
        if self._json_error:
            raise self._json_error
        return self._payload


GOOD = {"choices": [{"message": {"content": "hi there"}}]}


def _task():
    return Task(id="t-1", title="t", category="coding", prompt="hi")


def _make(monkeypatch, responses, sleeps=None):
    calls = []

    def fake_post(url, **kwargs):
        calls.append(kwargs)
        r = responses.pop(0)
        if isinstance(r, Exception):
            raise r
        return r

    monkeypatch.setattr("agent_benchmark.adapters.openai_compat.httpx.post", fake_post)
    if sleeps is not None:
        monkeypatch.setattr(
            "agent_benchmark.adapters.openai_compat.time.sleep", lambda s: sleeps.append(s)
        )
    return calls


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    with pytest.raises(RuntimeError, match="OPENAI_API_KEY"):
        OpenAICompatAdapter("m").generate(_task())


def test_non_https_refused(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    with pytest.raises(ValueError, match="non-HTTPS"):
        OpenAICompatAdapter("m", base_url="http://localhost:8000/v1").generate(_task())


def test_non_https_insecure_allowed(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    calls = _make(monkeypatch, [FakeResponse(GOOD)])
    out = OpenAICompatAdapter("m", base_url="http://localhost:8000/v1", insecure=True).generate(_task())
    assert out == "hi there"
    assert len(calls) == 1


def test_missing_choices_raises(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _make(monkeypatch, [FakeResponse({"error": "nope"})])
    with pytest.raises(RuntimeError, match="shape"):
        OpenAICompatAdapter("m").generate(_task())


def test_null_content_raises(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _make(monkeypatch, [FakeResponse({"choices": [{"message": {"content": None}}]})])
    with pytest.raises(RuntimeError, match="null"):
        OpenAICompatAdapter("m").generate(_task())


def test_invalid_json_raises(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    _make(monkeypatch, [FakeResponse(json_error=ValueError("bad json"))])
    with pytest.raises(RuntimeError, match="Invalid JSON"):
        OpenAICompatAdapter("m").generate(_task())


def test_retries_on_transport_error(monkeypatch):
    monkeypatch.setenv("OPENAI_API_KEY", "k")
    sleeps = []
    calls = _make(monkeypatch, [httpx.ConnectError("boom"), FakeResponse(GOOD)], sleeps)
    out = OpenAICompatAdapter("m", backoff=0.0).generate(_task())
    assert out == "hi there"
    assert len(calls) == 2
    assert sleeps
