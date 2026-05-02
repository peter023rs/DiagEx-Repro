"""Phase 1 (ad-hoc NL query) system prompt.

Spec ref: §15 (starter system prompt) + §6.2 (caching). Returned as a list of
content blocks so the LLMClient can apply `cache_control` to the stable portion
while the volatile per-question framing stays outside the cache.
"""

from __future__ import annotations

from typing import Any

from diagex.config import EFFORT_PROFILES, EffortLevel

# Spec §15 verbatim, with minor typographical clean-up only (straight quotes,
# consistent list indentation). No behavioural changes — this is the cache key.
STARTER_SYSTEM_PROMPT = """\
You are a domain expert reading piping and instrumentation diagrams (P&IDs) and
related industrial-automation schematics. You have tools to view the drawing at
different scales and to record annotations.

Your approach:
1. ALWAYS start by calling get_overview to understand the overall layout.
2. Identify the drawing type, title-block information, and any legend.
3. For detailed reading, call list_tiles and inspect tiles that plausibly contain
   information relevant to the user's question. Do not inspect tiles that cannot
   possibly contain the answer.
4. When you identify an entity that is relevant to the answer, call annotate with
   precise coordinates and a confidence level. Prefer "low" confidence over
   guessing -- unknown readings are far better than wrong readings.
5. If a tag or connection is ambiguous, use get_region to zoom in further before
   committing.
6. When you have enough information, call finish with a structured answer.

Conventions you should assume unless the drawing indicates otherwise:
- ISA-5.1 instrument bubble notation.
- Solid lines = process piping; dashed lines vary by drawing -- check the legend.
- Tag format: <Function-Letters>-<Loop-Number><Suffix>, e.g. FIC-101A.
- Flow direction follows arrow markers; where absent, infer from context.

Never invent tag numbers, equipment that is not visible, or connections you
cannot see. It is always acceptable to answer "cannot determine from the
drawing" with an explanation.\
"""


def build_system_prompt(question: str, effort: EffortLevel) -> list[dict[str, Any]]:
    """Return system-prompt blocks: [stable starter, volatile per-question framing].

    The first block is identical across every Phase 1 run and carries the
    `cache_control` marker the transport layer will stamp. The second block
    holds the user's specific question framing and effort-level reminder; it
    changes per call and therefore sits *after* the cache breakpoint.
    """
    profile = EFFORT_PROFILES[effort]

    stable_block: dict[str, Any] = {
        "type": "text",
        "text": STARTER_SYSTEM_PROMPT,
        "cache_control": {"type": "ephemeral"},
    }

    # Per-question framing: tells the agent the effort budget so it can self-
    # moderate step count without us passing a hard cap into every tool call.
    volatile_block: dict[str, Any] = {
        "type": "text",
        "text": (
            f"You have up to {profile.max_steps} tool-use steps for this query. "
            f"Prefer to answer early when the evidence is sufficient.\n\n"
            f"User question:\n{question.strip()}"
        ),
    }

    return [stable_block, volatile_block]
