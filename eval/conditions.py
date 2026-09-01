"""Named conditions for the diagex eval harness.

A *condition* is a frozen tuple of kwargs the harness applies on top of the
default extractor configuration before invoking ``run_query`` /
``run_pid_extract``. Most paper-shape rows are ``baseline``; the minimal
ablation in plan §5.4 / §7.1 contributes ``ablation-no-tile`` (and optionally
``ablation-no-legend``).

The legacy-condition set (``overlap``/``effort``/``cache`` knobs) is kept
defined-but-unused, so the journal version can revive a fuller grid without
re-plumbing.

Per-condition kwargs map onto two shapes:

* ``query_kwargs``     — overrides for ``diagex.extractors.query.run_query``
* ``pid_kwargs``       — overrides for ``diagex.extractors.pid.run_pid_extract``
* ``config_overrides`` — overrides applied to ``Config`` before the call
                         (mutates ``cfg.tiling``, ``cfg.pid``, etc.)

The harness owns merging; conditions just declare intent.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Condition:
    name: str
    description: str
    query_kwargs: dict[str, Any] = field(default_factory=dict)
    pid_kwargs: dict[str, Any] = field(default_factory=dict)
    config_overrides: dict[str, Any] = field(default_factory=dict)
    # Skip Phase 2 for this condition even when --phase=both. Used by the
    # GPT-4.1 anchor (single-shot, Phase 1 only — no DEXPI extraction).
    phase1_only: bool = False


# diagex paper conditions ------------------------------------------------

BASELINE = Condition(
    name="baseline",
    description="All defaults from spec §7.1 / §7.2 (effort=high for Phase 1, "
                "medium for Phase 2; tiling on; legend on; arbitration on).",
)

ABLATION_NO_TILE = Condition(
    name="ablation-no-tile",
    description="Disable tiling — feed the agent the entire page downscaled "
                "to the model's image cap (3.75 MP). Same Opus 4.7, no other "
                "changes. Plan §5.4.",
    config_overrides={
        # AspectAwareStrategy hits the per-tile token cap; for "no tile" we
        # bump the cap so the strategy emits a single oversized tile.
        "tiling.max_tokens_per_tile": 100_000,
        "tiling.overlap_frac": 0.0,
        # Clamp the local render so the long side is ~sqrt(3.75 MP) ≈ 1936 px
        # (round to 2000). Without this, a landscape page rendered at the
        # default 6000-px long side is ~24 MP — Anthropic would server-side
        # downscale it anyway, but we'd burn time and base64 bytes shipping
        # a 10 MB PNG per call. With max_page_dim_px=2000, "no tile" really
        # is "one image at the model's per-image cap" and the cost is
        # comparable to a single overview call.
        "tiling.max_page_dim_px": 2000,
    },
)

ABLATION_NO_LEGEND = Condition(
    name="ablation-no-legend",
    description="Skip legend detection; rely on the built-in symbol library. "
                "Plan §5.4 — only added if baseline shows legend-driven errors.",
    pid_kwargs={"no_legend": True},
)

EVIDENCE_V2 = Condition(
    name="evidence-v2",
    description="Opt-in evidence-first Phase 2 engine for A/B comparison with "
                "the paper-compatible legacy baseline.",
    pid_kwargs={"engine": "evidence-v2"},
)


# Cross-model anchor (plan §6, item 2) ---------------------------------------
#
# Phase 1 only, single-shot per query: one Azure OpenAI chat-completions call
# with the page overview image + the question. No tools, no ReAct loop, no
# tile drilldown. Lives outside the Claude/Anthropic transport entirely
# (separate SDK + wire format), so it does not share the harness's normal
# Config plumbing — the dispatch lives in `eval/gpt_singleshot.py` and is
# selected via the `backend` marker below.

GPT41_SINGLESHOT = Condition(
    name="gpt41-singleshot",
    description="Azure OpenAI GPT-4.1, single-shot per Phase 1 query. "
                "Page overview image + question + answer-format suffix; no "
                "tools. Phase 2 is N/A for this condition. Plan §6 item 2.",
    query_kwargs={"backend": "gpt41-singleshot"},
    phase1_only=True,
)


# Legacy condition stubs (declared but not part of the default run) --------

LEGACY_OVERLAP_HIGH = Condition(
    name="legacy-overlap-high",
    description="Reserved (journal version). Bumps tiling overlap_frac to 0.40.",
    config_overrides={"tiling.overlap_frac": 0.40},
)

LEGACY_EFFORT_LOW = Condition(
    name="legacy-effort-low",
    description="Reserved (journal version). Phase 1 at effort=low.",
    query_kwargs={"effort": "low"},
)

LEGACY_NO_CACHE = Condition(
    name="legacy-no-cache",
    description="Reserved (journal version). Disables prompt caching.",
    config_overrides={"llm.cache_enabled": False},
)


ALL_CONDITIONS: dict[str, Condition] = {
    c.name: c
    for c in (
        BASELINE,
        ABLATION_NO_TILE,
        ABLATION_NO_LEGEND,
        EVIDENCE_V2,
        GPT41_SINGLESHOT,
        LEGACY_OVERLAP_HIGH,
        LEGACY_EFFORT_LOW,
        LEGACY_NO_CACHE,
    )
}


# Conditions enabled by the driver's default --conditions list. Legacy ones
# above appear in CLI help but require explicit opt-in by the user.
DEFAULT_CONDITIONS = (BASELINE.name, ABLATION_NO_TILE.name)


def resolve_conditions(names: list[str]) -> list[Condition]:
    out: list[Condition] = []
    for n in names:
        n = n.strip()
        if not n:
            continue
        if n not in ALL_CONDITIONS:
            raise ValueError(
                f"unknown condition {n!r}; known: {sorted(ALL_CONDITIONS)}"
            )
        out.append(ALL_CONDITIONS[n])
    if not out:
        raise ValueError("no conditions resolved")
    return out


def apply_config_overrides(config: Any, overrides: dict[str, Any]) -> None:
    """Apply ``"a.b.c": value`` overrides in place on a ``Config`` object.

    Tolerates missing intermediate attributes silently (the legacy stubs
    target knobs that may not exist yet — running them would error out, but
    just *defining* the condition shouldn't blow up).
    """
    for dotted, value in overrides.items():
        parts = dotted.split(".")
        target: Any = config
        for p in parts[:-1]:
            target = getattr(target, p, None)
            if target is None:
                return
        setattr(target, parts[-1], value)
