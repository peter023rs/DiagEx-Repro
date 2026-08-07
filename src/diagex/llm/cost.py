"""Cost + token accounting.

Spec refs: §6.3 (budgets), §10 (cost model), §7.1
(`cost.json` written to runs/<stem>/<run>/).

Usage figures come straight from `response.usage` on the Anthropic SDK Message
object. The field set is:
  - input_tokens
  - output_tokens
  - cache_creation_input_tokens  (tokens we just wrote to the cache)
  - cache_read_input_tokens      (tokens served from cache at ~0.1x)

Image tokens are not a separate field on the Messages API — they are folded into
input_tokens (for uncached image inputs) or cache_read/cache_creation for cached
ones. We expose a nominal `image_tokens` field in case a future SDK splits them
out; for now it defaults to 0 and can be populated by the caller if they did a
tile-level count.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from typing import Any

from diagex.config import PricingConfig


def format_tokens_millions(token_count: int) -> str:
    """Render token usage compactly and consistently for user-facing output."""
    return f"{max(0, int(token_count)) / 1_000_000:.3f}M"


def total_tokens_from_summary(summary: dict[str, Any]) -> int:
    """Read a total from new summaries or derive it from legacy summaries."""
    if summary.get("total_tokens") is not None:
        return int(summary["total_tokens"] or 0)
    return sum(
        int(summary.get(key, 0) or 0)
        for key in (
            "input_tokens",
            "output_tokens",
            "cache_read_tokens",
            "cache_write_tokens",
        )
    )


@dataclass
class StepUsage:
    """Token breakdown for one LLM call (= one ReAct step)."""

    step: int
    tile_id: str | None
    page_index: int | None
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    image_tokens: int = 0  # reserved; folded into input by current Anthropic SDK


@dataclass
class CostTracker:
    """Appends per-step usage and projects it to USD via PricingConfig.

    Kept intentionally dumb — this is the single place cost gets computed, so a
    pricing-table edit in PricingConfig re-projects every historical run without
    code changes (see spec §10, risk row: drift from Anthropic pricing).
    """

    pricing: PricingConfig = field(default_factory=PricingConfig)
    steps: list[StepUsage] = field(default_factory=list)

    # ---- recording --------------------------------------------------------

    def record(
        self,
        response: Any,
        *,
        step: int,
        tile_id: str | None = None,
        page_index: int | None = None,
    ) -> StepUsage:
        """Pull response.usage and append a StepUsage row.

        Accepts any object exposing `.usage` with the standard Anthropic SDK
        field names. Missing fields default to 0 — older SDK versions and the
        Azure-compatible surface do not always report cache fields.
        """
        usage = getattr(response, "usage", None)
        if usage is None:
            # Some error paths may construct a synthetic response; record zeros so
            # the step is still visible in cost.json.
            row = StepUsage(
                step=step,
                tile_id=tile_id,
                page_index=page_index,
                input_tokens=0,
                output_tokens=0,
                cache_read_tokens=0,
                cache_write_tokens=0,
            )
        else:
            row = StepUsage(
                step=step,
                tile_id=tile_id,
                page_index=page_index,
                input_tokens=int(getattr(usage, "input_tokens", 0) or 0),
                output_tokens=int(getattr(usage, "output_tokens", 0) or 0),
                cache_read_tokens=int(
                    getattr(usage, "cache_read_input_tokens", 0) or 0
                ),
                cache_write_tokens=int(
                    getattr(usage, "cache_creation_input_tokens", 0) or 0
                ),
            )
        self.steps.append(row)
        return row

    # ---- aggregation ------------------------------------------------------

    def total_usd(self) -> float:
        return sum(
            self.pricing.cost_usd(
                input_tokens=s.input_tokens,
                output_tokens=s.output_tokens,
                cache_read_tokens=s.cache_read_tokens,
                cache_write_tokens=s.cache_write_tokens,
            )
            for s in self.steps
        )

    def total_tokens(self) -> int:
        return sum(
            s.input_tokens
            + s.output_tokens
            + s.cache_read_tokens
            + s.cache_write_tokens
            for s in self.steps
        )

    def summary(self) -> dict[str, Any]:
        return {
            "total_usd": round(self.total_usd(), 6),
            "total_tokens": self.total_tokens(),
            "input_tokens": sum(s.input_tokens for s in self.steps),
            "output_tokens": sum(s.output_tokens for s in self.steps),
            "cache_read_tokens": sum(s.cache_read_tokens for s in self.steps),
            "cache_write_tokens": sum(s.cache_write_tokens for s in self.steps),
            "image_tokens": sum(s.image_tokens for s in self.steps),
            "steps": [asdict(s) for s in self.steps],
        }

    def to_json(self) -> str:
        """Pretty-printed JSON — the on-disk shape written to cost.json."""
        return json.dumps(self.summary(), indent=2, sort_keys=True)
