"""Provider preferences survive the UI, transport and cache boundaries."""

import json
from types import SimpleNamespace

import anthropic
import httpx
import pytest

from diagex.config import Config, LLMConfig
from diagex.llm.client import LLMClient
from diagex.web.model_profiles import VISION_MODELS
from diagex.web.server import Workbench, WorkbenchError


@pytest.mark.parametrize("preset", VISION_MODELS)
def test_presets_and_routing_reach_messages_api(tmp_path, monkeypatch, preset):
    requests = []

    def handle(request):
        requests.append(json.loads(request.content))
        message = {"id": "test", "type": "message", "role": "assistant",
                   "content": [], "model": VISION_MODELS[preset], "stop_reason": None,
                   "stop_sequence": None, "usage": {"input_tokens": 1, "output_tokens": 0}}
        events = [
            {"type": "message_start", "message": message},
            {"type": "message_delta", "delta": {"stop_reason": "end_turn", "stop_sequence": None},
             "usage": {"output_tokens": 1}},
            {"type": "message_stop"},
        ]
        return httpx.Response(200, headers={"content-type": "text/event-stream"}, content="".join(
            f"event: {event['type']}\ndata: {json.dumps(event)}\n\n" for event in events
        ))

    workbench = Workbench(Config(runs_dir=tmp_path, llm=LLMConfig(openrouter_api_key="test")))
    config, settings = workbench._config_for_request({
        "model_policy": preset, "openrouter_provider_order": ["xiaomi"],
        "openrouter_provider_ignore": ["deepinfra"], "openrouter_allow_fallbacks": False,
    })
    sdk = anthropic.Anthropic(api_key="test", base_url="https://test.invalid",
                             http_client=httpx.Client(transport=httpx.MockTransport(handle)))
    monkeypatch.setattr(LLMClient, "_build_client", staticmethod(lambda config: sdk))
    try:
        client = LLMClient(config.llm)
        client.messages_create(system="test", messages=[{"role": "user", "content": "test"}],
                               max_tokens=100, reasoning_mode_override="disabled",
                               output_config={"effort": "medium"})
        assert requests[0]["model"] == VISION_MODELS[preset]
        assert requests[0]["provider"] == {
            "order": ["xiaomi"], "ignore": ["deepinfra"], "allow_fallbacks": False,
        }
        assert settings["openrouter_provider_ignore"] == ["deepinfra"]
        assert "api_key" not in settings
        if preset == "glm":
            assert requests[0]["thinking"] == {"type": "adaptive"}
            assert requests[0]["output_config"] == {"effort": "high"}
        elif preset == "qwen_vl":
            assert "thinking" not in requests[0] and "output_config" not in requests[0]
        else:
            assert requests[0]["thinking"] == {"type": "disabled"}
    finally:
        sdk.close()
        workbench.close()


@pytest.mark.parametrize("routing", [
    {"openrouter_provider_ignore": "deepinfra"},
    {"openrouter_provider_order": [None]},
    {"openrouter_provider_order": ["xiaomi"], "openrouter_provider_ignore": ["xiaomi"]},
    {"openrouter_allow_fallbacks": "false"},
    {"openrouter_allow_fallbacks": False},
])
def test_invalid_routing_fails_before_starting_job(tmp_path, routing):
    workbench = Workbench(Config(runs_dir=tmp_path, llm=LLMConfig(openrouter_api_key="test")))
    with pytest.raises(WorkbenchError):
        workbench._config_for_request({"model_policy": "mimo", **routing})
    workbench.close()


def test_routing_keeps_verified_price_and_provider_restrictions(monkeypatch):
    captured = []

    class Stream:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def get_final_message(self):
            return SimpleNamespace(content=[], usage=None)

    def stream(**kwargs):
        captured.append(kwargs)
        return Stream()

    monkeypatch.setattr(LLMClient, "_build_client", staticmethod(
        lambda config: SimpleNamespace(messages=SimpleNamespace(stream=stream))))
    client = LLMClient(LLMConfig(transport="openrouter", model="test",
                               openrouter_provider_ignore=["deepinfra"]))
    client.spending = SimpleNamespace(prices={"test": {"provider_tags": ["verified"],
        "input_per_token": 0.000001, "output_per_token": 0.000002}}, reserve=lambda *args: None)
    client.messages_create(system="test", messages=[], max_tokens=100)
    assert captured[0]["extra_body"]["provider"] == {
        "ignore": ["deepinfra"], "only": ["verified"], "require_parameters": True,
        "max_price": {"prompt": 1, "completion": 2},
    }
