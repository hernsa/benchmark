import json
import pytest
from agent_benchmark.adapters.opencode import (
    OpencodeAdapter,
    list_opencode_models,
    load_opencode_providers,
)

CFG = {
    "provider": {
        "xpiki": {
            "options": {"baseURL": "https://api.xpiki.com/v1", "apiKey": "k1"},
            "models": {"claude-sonnet-5": {"name": "Sonnet 5"}},
        },
        "vyceai": {
            "options": {"baseURL": "https://vyceai.com/v1", "apiKey": "k2"},
            "models": {"deepseek-v4-flash": {"name": "Flash"}},
        },
    }
}


@pytest.fixture()
def cfg_path(tmp_path):
    p = tmp_path / "opencode.jsonc"
    p.write_text(json.dumps(CFG), encoding="utf-8")
    return str(p)


def test_list_models_sorted(cfg_path):
    assert list_opencode_models(cfg_path) == [
        "vyceai/deepseek-v4-flash",
        "xpiki/claude-sonnet-5",
    ]


def test_adapter_resolves_provider_fields(cfg_path):
    a = OpencodeAdapter("xpiki/claude-sonnet-5", config_path=cfg_path)
    assert a.base_url == "https://api.xpiki.com/v1"
    assert a.model == "claude-sonnet-5"
    assert a.name == "xpiki/claude-sonnet-5"


def test_bad_ref_shape(cfg_path):
    with pytest.raises(ValueError):
        OpencodeAdapter("no-slash-here", config_path=cfg_path)


def test_unknown_provider(cfg_path):
    with pytest.raises(ValueError):
        OpencodeAdapter("nope/claude-sonnet-5", config_path=cfg_path)


def test_unknown_model(cfg_path):
    with pytest.raises(ValueError):
        OpencodeAdapter("xpiki/nope", config_path=cfg_path)


def test_no_providers(tmp_path):
    p = tmp_path / "empty.jsonc"
    p.write_text("{}", encoding="utf-8")
    with pytest.raises(ValueError):
        load_opencode_providers(str(p))
