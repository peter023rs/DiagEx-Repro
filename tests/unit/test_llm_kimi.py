"""Configuration and client-construction tests for the Kimi transport."""

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
        "DIAGEX_REASONING",
        "KIMI_MODEL",
        "KIMI_API_KEY",
        "KIMI_BASE_URL",
        "OPENROUTER_API_KEY",
        "ANTHROPIC_API_KEY",
        "AZURE_OPENAI_ENDPOINT",
        "AZURE_OPENAI_API_KEY",
        "AZURE_OPENAI_DEPLOYMENT_NAME",
    ):
        monkeypatch.delenv(name, raising=False)


def test_kimi_config_accepts_requested_environment(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("DIAGEX_LLM_PROVIDER", "kimi")
    monkeypatch.setenv("KIMI_API_KEY", "test-key")
    monkeypatch.setenv("KIMI_BASE_URL", "https://api.kimi.com/coding/v1")
    monkeypatch.setenv("DIAGEX_MODEL", "k3")

    config = LLMConfig.from_env()

    assert config.transport == "kimi"
    assert config.model == "k3"
    assert config.kimi_api_key == "test-key"
    assert config.kimi_base_url == "https://api.kimi.com/coding/v1"


def test_explicit_openrouter_wins_when_kimi_key_is_also_present(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _clear_provider_env(monkeypatch)
    monkeypatch.setenv("DIAGEX_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "openrouter-key")
    monkeypatch.setenv("KIMI_API_KEY", "kimi-key")
    monkeypatch.setenv("DIAGEX_MODEL", "vendor/vision-model")

    assert LLMConfig.from_env().transport == "openrouter"


def test_kimi_client_normalizes_openai_style_base_for_anthropic_sdk(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    captured: dict[str, Any] = {}

    def fake_anthropic(**kwargs: Any) -> SimpleNamespace:
        captured.update(kwargs)
        return SimpleNamespace()

    monkeypatch.setattr("diagex.llm.client.anthropic.Anthropic", fake_anthropic)

    LLMClient(
        LLMConfig(
            transport="kimi",
            model="k3",
            kimi_api_key="test-key",
            kimi_base_url="https://api.kimi.com/coding/v1",
        )
    )

    assert captured == {
        "base_url": "https://api.kimi.com/coding",
        "api_key": "test-key",
        "max_retries": 0,
    }


def test_kimi_preserves_images_and_tools_but_removes_thinking_display(
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

    monkeypatch.setattr(
        LLMClient,
        "_build_client",
        staticmethod(lambda _config: SimpleNamespace(messages=FakeMessages())),
    )
    client = LLMClient(
        LLMConfig(transport="kimi", model="k3", kimi_api_key="test-key")
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
    assert captured["model"] == "k3"
    assert captured["messages"][0]["content"][0] is image
    assert captured["tools"][0]["name"] == "get_overview"
    assert captured["thinking"] == {"type": "adaptive"}
    assert captured["output_config"] == {"effort": "medium"}


def test_messages_create_forwards_reasoning_and_text_stream_deltas(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    expected = SimpleNamespace(content=[], usage=None, stop_reason="end_turn")
    received: list[tuple[str, str]] = []

    class FakeStream:
        def __enter__(self) -> FakeStream:
            return self

        def __exit__(self, *args: Any) -> None:
            return None

        def __iter__(self) -> Any:
            return iter(
                [
                    SimpleNamespace(
                        type="content_block_delta",
                        delta=SimpleNamespace(
                            type="thinking_delta", thinking="inspect symbols"
                        ),
                    ),
                    {
                        "type": "content_block_delta",
                        "delta": {"type": "text_delta", "text": "calling tool"},
                    },
                ]
            )

        def get_final_message(self) -> SimpleNamespace:
            return expected

    class FakeMessages:
        def stream(self, **kwargs: Any) -> FakeStream:
            return FakeStream()

    monkeypatch.setattr(
        LLMClient,
        "_build_client",
        staticmethod(lambda _config: SimpleNamespace(messages=FakeMessages())),
    )
    client = LLMClient(
        LLMConfig(transport="kimi", model="k3", kimi_api_key="test-key")
    )

    result = client.messages_create(
        system="system",
        messages=[],
        max_tokens=32,
        on_stream_delta=lambda kind, text: received.append((kind, text)),
    )

    assert result is expected
    assert received == [
        ("thinking", "inspect symbols"),
        ("text", "calling tool"),
    ]
