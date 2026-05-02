"""LLM transport layer: wraps Anthropic SDK (direct or Azure AI Foundry).

Spec refs: §4 (stack), §6.2 (prompt caching), §6.3 (budgets), §6.4 (resilience: retry),
§10 (cost).

Two transports are supported:
  - "anthropic": direct api.anthropic.com via anthropic.Anthropic().
  - "azure":    Azure AI Foundry's Anthropic-compatible endpoint, driven via
                anthropic.Anthropic(base_url=..., default_headers={"api-key": ...}).

The SDK's own retry machinery is deliberately bypassed — this module enforces the
spec's backoff policy (base 2s, factor 2, max 60s, 6 attempts) from RuntimeBudgets so
the behaviour is configurable and re-projectable from config.
"""

from __future__ import annotations

import random
import sys
import time
from typing import Any

import anthropic

from diagex.config import LLMConfig, RuntimeBudgets


class LLMClient:
    """Thin wrapper around the Anthropic SDK with caching-aware messages_create()."""

    def __init__(self, config: LLMConfig, budgets: RuntimeBudgets | None = None) -> None:
        self.config = config
        self.budgets = budgets or RuntimeBudgets()
        self._client = self._build_client(config)
        # Cumulative retry count: every backoff attempt increments this. The
        # extractor snapshots it before/after a run so the per-extractor row
        # in results.csv carries the retries that actually ate wall-clock.
        self.retries_total: int = 0

    def reset_retry_counter(self) -> None:
        self.retries_total = 0

    @staticmethod
    def _build_client(config: LLMConfig) -> anthropic.Anthropic:
        """Construct the underlying Anthropic SDK client.

        Azure AI Foundry exposes an Anthropic-compatible endpoint; the Python SDK
        talks to it when pointed at the right base_url with the `api-key` header
        (Azure) set alongside the SDK's usual `x-api-key` (which Azure ignores but
        the SDK insists on populating).
        """
        if config.transport == "azure":
            if not (config.azure_endpoint and config.azure_api_key):
                raise ValueError(
                    "Azure transport requires azure_endpoint and azure_api_key; "
                    "check .env for AZURE_OPENAI_ENDPOINT / AZURE_OPENAI_API_KEY."
                )
            # Azure appends ?api-version=... to every call; the SDK does not know about
            # that query param, so stamp it into default_query to avoid surgery per-call.
            default_query: dict[str, str] = {}
            if config.azure_api_version:
                default_query["api-version"] = config.azure_api_version
            return anthropic.Anthropic(
                base_url=config.azure_endpoint,
                api_key=config.azure_api_key,  # satisfies SDK; ignored by Azure
                default_headers={"api-key": config.azure_api_key},
                default_query=default_query or None,
                max_retries=0,  # we own retry policy
            )

        # Direct Anthropic transport.
        if not config.anthropic_api_key:
            raise ValueError(
                "Anthropic transport requires anthropic_api_key; set ANTHROPIC_API_KEY."
            )
        return anthropic.Anthropic(
            api_key=config.anthropic_api_key,
            max_retries=0,  # we own retry policy
        )

    # ---- internals --------------------------------------------------------

    def _sleep_for_attempt(self, attempt: int) -> float:
        """Exponential backoff with jitter, clamped to retry_max_s."""
        base = self.budgets.retry_base_s
        factor = self.budgets.retry_factor
        cap = self.budgets.retry_max_s
        delay = min(cap, base * (factor ** attempt))
        # Full jitter: sample in [0, delay] so coincident clients decorrelate.
        return random.uniform(0, delay)

    @staticmethod
    def _stamp_cache(blocks: list[dict[str, Any]] | None) -> list[dict[str, Any]] | None:
        """Attach cache_control={type:ephemeral} to the final block of a list.

        Used for the system prompt and the tools list so a stable prefix is cached.
        We mutate the *last* element so callers can compose prefix chunks freely.
        """
        if not blocks:
            return blocks
        # Shallow copy so we don't mutate caller data structures.
        out = [dict(b) for b in blocks]
        out[-1] = {**out[-1], "cache_control": {"type": "ephemeral"}}
        return out

    # ---- public API -------------------------------------------------------

    def messages_create(
        self,
        *,
        system: str | list[dict[str, Any]],
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]] | None = None,
        max_tokens: int,
        thinking: dict[str, Any] | None = None,
        output_config: dict[str, Any] | None = None,
        extra_cache_breakpoints: list[dict[str, Any]] | None = None,
    ) -> Any:
        """Send a Messages request with caching + spec-compliant retry.

        `system` may be a plain string (treated as one text block, caching applied)
        or a pre-built list of system blocks where the caller has already placed
        cache_control markers. In the latter case we leave placement alone.

        `thinking` on Opus 4.7 must be `{"type": "adaptive"}` or `{"type": "disabled"}`
        — the legacy `{"type": "enabled", "budget_tokens": N}` shape is rejected.
        `output_config={"effort": "low|medium|high|xhigh|max"}` controls thinking depth.

        Opus 4.7 also rejects `temperature` / `top_p` / `top_k`, so we never send them.
        """
        # Normalize system → list form, stamp cache_control on the last block if the
        # caller passed a bare string or a list without its own markers.
        if isinstance(system, str):
            system_blocks: list[dict[str, Any]] = [{"type": "text", "text": system}]
            system_blocks = self._stamp_cache(system_blocks)  # type: ignore[assignment]
        else:
            # Respect caller-supplied cache_control if any block already has one.
            has_marker = any("cache_control" in b for b in system)
            system_blocks = system if has_marker else (self._stamp_cache(list(system)) or [])

        # Tools render at position 0; a breakpoint on the last tool caches the whole
        # tool list. Only stamp if the caller did not pre-place markers.
        tools_payload: list[dict[str, Any]] | None = None
        if tools:
            has_marker = any("cache_control" in t for t in tools)
            tools_payload = tools if has_marker else (self._stamp_cache(list(tools)) or [])

        # `extra_cache_breakpoints` are opaque structured blocks — e.g. a cached
        # overview image appended to the first user turn — that the caller has
        # already wired into `messages`. Kept in the signature as a hook so the
        # runtime can pass breakpoint metadata for logging/debugging without
        # modifying messages here.
        _ = extra_cache_breakpoints

        kwargs: dict[str, Any] = {
            "model": self.config.model,
            "max_tokens": max_tokens,
            "system": system_blocks,
            "messages": messages,
        }
        if tools_payload is not None:
            kwargs["tools"] = tools_payload
        if thinking is not None:
            kwargs["thinking"] = thinking
        if output_config is not None:
            kwargs["output_config"] = output_config

        # Stream for long outputs. High `max_tokens` + adaptive thinking can exceed the
        # SDK's 10-minute non-streaming timeout; `.stream(...).get_final_message()` returns
        # the same Message object but keeps the connection alive via chunked transfer.
        last_exc: Exception | None = None
        for attempt in range(self.budgets.retry_attempts):
            try:
                with self._client.messages.stream(**kwargs) as stream:
                    return stream.get_final_message()
            except anthropic.APIStatusError as exc:
                status = getattr(exc, "status_code", None)
                # 4xx (except 429) = validation/auth/policy → surface immediately.
                if status is not None and 400 <= status < 500 and status != 429:
                    raise
                last_exc = exc
            except anthropic.APIConnectionError as exc:
                # Transient network fault; same backoff ladder as 5xx.
                last_exc = exc

            if attempt == self.budgets.retry_attempts - 1:
                break

            self.retries_total += 1
            delay = self._sleep_for_attempt(attempt)
            print(
                f"[diagex.llm] transient failure ({type(last_exc).__name__}); "
                f"retry {attempt + 1}/{self.budgets.retry_attempts} in {delay:.1f}s",
                file=sys.stderr,
            )
            time.sleep(delay)

        # Exhausted — re-raise the last observed error.
        assert last_exc is not None
        raise last_exc
