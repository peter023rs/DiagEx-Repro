"""Configuration and client-construction tests for the OpenRouter transport."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import pytest

from diagex.config import LLMConfig
from diagex.llm.client import LLMClient


def _clear_provider_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "DIAGEX_LLM_PROVIDER",
        "DIAGEX_MODEL",
        "OPENROUTER_MODEL",
        "OPENROUTER_API_KEY",
        "OPENROUTER_BASE_URL",
        "OPENROUTER_HTTP_REFERER",
        "OPENROUTER_APP_TITLE",
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)


def test_openrouter_config_from_explicit_provider(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("DIAGEX_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("DIAGEX_MODEL", "vendor/vision-model")

    config = LLMConfig.from_env()

    assert config.transport == "openrouter"
    assert config.model == "vendor/vision-model"
    assert config.openrouter_api_key == "test-key"
    assert config.openrouter_base_url == "https://openrouter.ai/api"


def test_openrouter_is_auto_detected_when_it_is_the_only_key(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("OPENROUTER_MODEL", "vendor/vision-model")

    assert LLMConfig.from_env().transport == "openrouter"


def test_openrouter_requires_an_explicit_model(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("DIAGEX_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")

    with pytest.raises(ValueError, match="requires a model slug"):
        LLMConfig.from_env()


def test_openrouter_client_uses_messages_endpoint_and_bearer_auth(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_anthropic(**kwargs: Any) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr("diagex.llm.client.anthropic.Anthropic", fake_anthropic)

    LLMClient(
        LLMConfig(
            transport="openrouter",
            model="vendor/vision-model",
            openrouter_api_key="test-key",
            openrouter_http_referer="https://example.test/diagex",
            openrouter_app_title="DiagEx Test",
        )
    )

    # The Anthropic SDK appends /v1/messages to this base URL.
    assert captured["base_url"] == "https://openrouter.ai/api"
    assert captured["auth_token"] == "test-key"
    assert captured["default_headers"] == {
        "HTTP-Referer": "https://example.test/diagex",
        "X-OpenRouter-Title": "DiagEx Test",
    }
    assert captured["max_retries"] == 0


def test_openrouter_preserves_native_images_tools_and_thinking(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}
    expected = SimpleNamespace(content=[], usage=None, stop_reason="end_turn")

    class FakeStream:
        def __enter__(self) -> FakeStream:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def get_final_message(self) -> SimpleNamespace:
            return expected

    class FakeMessages:
        def stream(self, **kwargs: Any) -> FakeStream:
            captured.update(kwargs)
            return FakeStream()

    fake_client = SimpleNamespace(messages=FakeMessages())
    monkeypatch.setattr(
        LLMClient,
        "_build_client",
        staticmethod(lambda _config: fake_client),
    )
    client = LLMClient(
        LLMConfig(
            transport="openrouter",
            model="vendor/vision-model",
            openrouter_api_key="test-key",
        )
    )
    image = {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": "image/png",
            "data": "aW1hZ2U=",
        },
    }
    tool = {
        "name": "get_overview",
        "description": "View the page",
        "input_schema": {"type": "object", "properties": {}},
    }

    result = client.messages_create(
        system=[{"type": "text", "text": "system"}],
        messages=[{"role": "user", "content": [image]}],
        tools=[tool],
        max_tokens=2048,
        thinking={"type": "adaptive", "display": "summarized"},
        output_config={"effort": "medium"},
    )

    assert result is expected
    assert captured["model"] == "vendor/vision-model"
    assert captured["messages"][0]["content"][0] is image
    assert captured["tools"][0]["name"] == "get_overview"
    assert captured["thinking"] == {"type": "adaptive", "display": "summarized"}
    assert captured["output_config"] == {"effort": "medium"}
