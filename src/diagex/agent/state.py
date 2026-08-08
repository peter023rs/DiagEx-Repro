"""AgentState — the scratchpad threaded through the ReAct loop.

Spec refs: §5.4 (annotations), §6 (runtime), §7.1 (run artefacts).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from diagex.vision.annotations import AnnotationStore
from diagex.vision.legend_models import LegendPack
from diagex.vision.models import DiagramPage


@dataclass
class TranscriptStep:
    """One step in the ReAct loop, serialised as a line of transcript.jsonl (§7.1)."""

    step: int
    kind: str                     # "thought" | "tool_use" | "tool_result"
    payload: dict[str, Any]


@dataclass
class RegionFetch:
    """A free-form region returned by the get_region tool — kept so debug
    artefacts can show exactly what the agent zoomed into."""

    x: int
    y: int
    w: int
    h: int
    image: Any                    # PIL.Image.Image — typed as Any to avoid import


@dataclass
class AgentState:
    """Per-run, per-page working state."""

    question: str
    page: DiagramPage
    annotations: AnnotationStore = field(default_factory=AnnotationStore)
    transcript: list[TranscriptStep] = field(default_factory=list)

    # ReAct accounting
    steps: int = 0
    done: bool = False
    final_answer: str | None = None
    final_confidence: str | None = None
    completion_status: str = "running"
    completion_reason: str | None = None

    # Optional completion guard installed by extraction runtimes that require
    # systematic tile coverage before accepting the finish tool.
    required_tile_ids: set[str] = field(default_factory=set)
    minimum_tile_coverage: float = 0.0

    # Per-tile image-fetch counter — enforces max_image_requests_per_tile (§6.3).
    tile_fetch_counts: dict[str, int] = field(default_factory=dict)

    # Free-form regions the agent fetched via get_region — written to tiles/
    # alongside fetched tiles so runs show every view the agent inspected.
    region_fetches: list[RegionFetch] = field(default_factory=list)

    # Active view registry: maps view-tag → ViewInfo so the agent can refer to a
    # previously fetched view when it emits annotations tied to that view.
    views: dict[str, Any] = field(default_factory=dict)
    last_view_tag: str | None = None

    # Phase 2 lookup_symbol backing store: the overflow LegendPack when entries
    # were demoted out of the cached few-shot block (spec §7.2.2). None when
    # everything fit in the cached prompt and lookup_symbol is not registered.
    lookup_legend: LegendPack | None = None

    def push_transcript(self, kind: str, payload: dict[str, Any]) -> None:
        self.transcript.append(TranscriptStep(step=self.steps, kind=kind, payload=payload))


def aggregate_tool_call_counts(states: list[AgentState]) -> dict[str, int]:
    """Count ``tool_use`` transcript entries across pages, keyed by tool name.

    Returned dict is sorted by tool name for diff-friendly JSON dumps.
    """
    counts: dict[str, int] = {}
    for st in states:
        for ts in st.transcript:
            if ts.kind != "tool_use":
                continue
            name = (ts.payload or {}).get("name") or "unknown"
            counts[name] = counts.get(name, 0) + 1
    return dict(sorted(counts.items()))
