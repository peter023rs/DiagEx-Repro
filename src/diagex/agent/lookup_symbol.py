"""lookup_symbol tool (Phase 2) -- retrieves legend entries demoted out of
the cached few-shot block (spec §6.2, §7.2.2).

Kept separate from the Phase 1 `tools.py` so the Phase 1 tool set stays
untouched. The runtime registers this schema only when the merged legend
overflows the cached few-shot budget.
"""

from __future__ import annotations

from typing import Any

from diagex.agent.state import AgentState
from diagex.agent.tools import ToolResult
from diagex.vision.legend_models import LegendEntry

LOOKUP_SYMBOL_SCHEMA: dict[str, Any] = {
    "name": "lookup_symbol",
    "description": (
        "Look up a symbol in the full legend (entries demoted from the cached "
        "few-shot block to save tokens). Returns {label, symbol_class, "
        "description, image} or a miss."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "query": {
                "type": "string",
                "description": (
                    "Partial label, description substring, or class token "
                    "(case-insensitive)."
                ),
            },
            "max_results": {
                "type": "integer",
                "minimum": 1,
                "maximum": 5,
                "default": 3,
            },
        },
        "required": ["query"],
        "additionalProperties": False,
    },
}


def dispatch_lookup_symbol(raw_input: dict[str, Any], state: AgentState) -> ToolResult:
    """Route a lookup_symbol tool_use to the legend pack on AgentState."""
    pack = getattr(state, "lookup_legend", None)
    if pack is None:
        return ToolResult(
            content=[{
                "type": "text",
                "text": (
                    "lookup_symbol not available: all legend entries are in "
                    "the cached few-shot block."
                ),
            }],
            is_error=True,
        )

    query = (raw_input.get("query") or "").strip()
    if not query:
        return ToolResult(
            content=[{"type": "text", "text": "lookup_symbol: empty query."}],
            is_error=True,
        )
    max_results = int(raw_input.get("max_results", 3))
    max_results = max(1, min(5, max_results))

    q = query.lower()
    matches: list[LegendEntry] = []
    for e in pack.entries:
        hay = " ".join([
            (e.label or "").lower(),
            (e.description or "").lower(),
            (e.symbol_class or "").lower(),
        ])
        if q in hay:
            matches.append(e)
        if len(matches) >= max_results:
            break

    if not matches:
        return ToolResult(
            content=[{"type": "text", "text": f"lookup_symbol: no match for {query!r}."}],
        )

    lines = [f"{len(matches)} matches:"]
    for e in matches:
        desc = (e.description or "").strip() or "(no description)"
        std = e.standard or "unknown"
        lines.append(
            f"  {e.label} (symbol_class={e.symbol_class}, kind={e.kind}, "
            f"standard={std}): {desc}"
        )
    content: list[dict[str, Any]] = [{"type": "text", "text": "\n".join(lines)}]

    # Cap image returns at one -- attach the biggest (first) match that carries
    # an image payload. Keeps response token cost bounded.
    for e in matches:
        if e.image_b64:
            content.append({
                "type": "image",
                "source": {
                    "type": "base64",
                    "media_type": "image/png",
                    "data": e.image_b64,
                },
            })
            break

    return ToolResult(content=content)
