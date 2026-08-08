"""Tool schemas and dispatchers for the Phase 1 ReAct loop.

The tool contract shown here maps 1:1 to spec §6.2. Each dispatcher:
  - validates structured input (pydantic) and raises ToolInputError on bad shapes,
  - fetches a view through ViewProvider or records an Annotation,
  - returns a `ToolResult` the runtime turns into an Anthropic `tool_result` block.

The `annotate` tool is where the agent does structured output (spec §5.4). We keep
the schema narrow: the agent emits local coords against the *last view* it fetched;
the runtime projects to global coords via the ViewInfo stored in AgentState.views.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Any

from PIL import Image
from pydantic import BaseModel, Field, ValidationError

from diagex.agent.state import AgentState, RegionFetch
from diagex.dexpi_schema import (
    render_equipment_slash_list,
    render_instrument_class_slash_list,
    render_instrument_slash_list,
    render_valve_slash_list,
)
from diagex.vision.annotations import make_annotation
from diagex.vision.encode import encode_image_block
from diagex.vision.models import Annotation, BBox, Kind, Point
from diagex.vision.reconcile import LINE_STITCH_RADIUS_PX
from diagex.vision.views import ViewInfo, ViewProvider


class ToolInputError(Exception):
    """Raised when the agent's tool_use input fails validation."""


@dataclass
class ToolResult:
    """Result of a tool dispatch returned to the agent as a `tool_result` block."""

    content: list[dict[str, Any]]       # Anthropic content blocks: text / image
    is_error: bool = False


# ---------------------------------------------------------------------------
# Tool input schemas
# ---------------------------------------------------------------------------


class _GetOverviewIn(BaseModel):
    max_dim: int = Field(default=2000, ge=256, le=4000)


class _GetTileIn(BaseModel):
    tile_id: str


class _GetRegionIn(BaseModel):
    x: int
    y: int
    w: int = Field(gt=0)
    h: int = Field(gt=0)


class _ListTilesIn(BaseModel):
    pass


class _BBoxIn(BaseModel):
    x: int
    y: int
    w: int = Field(ge=0)
    h: int = Field(ge=0)


class _PointIn(BaseModel):
    x: float
    y: float


class _AnnotateIn(BaseModel):
    view_tag: str | None = None          # defaults to most recently fetched view
    kind: Kind
    label: str
    bbox: _BBoxIn
    confidence: str = "medium"
    line_type: str | None = None
    endpoints: list[_PointIn] = Field(default_factory=list)
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_quote: str | None = None


class _ListAnnotationsIn(BaseModel):
    kind: str | None = None


class _FinishIn(BaseModel):
    answer: str
    confidence: str = "medium"
    supporting_bboxes: list[_BBoxIn] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Tool schemas for the Anthropic API (JSONSchema-flavoured)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_overview",
        "description": (
            "Return a downsampled image of the whole page. Always call this first so you "
            "understand the page layout before zooming in."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "max_dim": {"type": "integer", "minimum": 256, "maximum": 4000, "default": 2000}
            },
            "additionalProperties": False,
        },
    },
    {
        "name": "list_tiles",
        "description": (
            "Return tile metadata (id + page-coordinate bbox) for the page. No images are "
            "returned — use this to plan which tiles to fetch."
        ),
        "input_schema": {"type": "object", "properties": {}, "additionalProperties": False},
    },
    {
        "name": "get_tile",
        "description": "Return one tile at native resolution. Identify tiles with ids from list_tiles.",
        "input_schema": {
            "type": "object",
            "properties": {"tile_id": {"type": "string"}},
            "required": ["tile_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_region",
        "description": (
            "Return an arbitrary crop of the page in page-coordinate pixels. Use this when "
            "you want to zoom into a specific area seen in the overview."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "x": {"type": "integer"},
                "y": {"type": "integer"},
                "w": {"type": "integer", "exclusiveMinimum": 0},
                "h": {"type": "integer", "exclusiveMinimum": 0},
            },
            "required": ["x", "y", "w", "h"],
            "additionalProperties": False,
        },
    },
    {
        "name": "annotate",
        "description": (
            "Record one finding. `bbox` and `endpoints` are in pixels of the *most recently "
            "fetched view* (overview, tile, or region); the runtime projects them to page "
            "coordinates. Use `confidence: low` rather than guessing. "
            "For kind='line' or kind='connection' you MUST populate `endpoints` with >= 2 "
            "points tracing the line's path (source first, target last, plus every visible "
            "bend); without endpoints the reconciler has no geometry to stitch or snap."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "view_tag": {
                    "type": "string",
                    "description": "Identifier of the view this finding was seen in; omit to use the last fetched view.",
                },
                "kind": {
                    "type": "string",
                    "enum": ["equipment", "instrument", "line", "connection", "text", "note", "opc"],
                },
                "label": {"type": "string"},
                "bbox": {
                    "type": "object",
                    "properties": {
                        "x": {"type": "integer"},
                        "y": {"type": "integer"},
                        "w": {"type": "integer", "minimum": 0},
                        "h": {"type": "integer", "minimum": 0},
                    },
                    "required": ["x", "y", "w", "h"],
                    "additionalProperties": False,
                },
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "line_type": {
                    "type": "string",
                    "enum": [
                        "process",
                        "signal_electric",
                        "signal_pneumatic",
                        "instrument_capillary",
                        "electrical_power",
                        "other",
                    ],
                },
                "endpoints": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {"x": {"type": "number"}, "y": {"type": "number"}},
                        "required": ["x", "y"],
                    },
                },
                "attributes": {
                    "type": "object",
                    "description": (
                        "Structured extras keyed by role. Phase 2 keys the agent is "
                        "expected to emit (arbitrary strings; enums live in the prompt): "
                        f"equipment_class ({render_equipment_slash_list()}), "
                        f"valve_type ({render_valve_slash_list()}), "
                        f"instrument_function ({render_instrument_slash_list()}), "
                        f"instrument_class ({render_instrument_class_slash_list()}, "
                        "optional, upgrades DEXPI wrapper class), "
                        "measured_variable "
                        "(flow/pressure/level/temperature/analysis/hand/other), "
                        "loop_number (numeric suffix of the tag, as string), direction "
                        "(in/out, for kind=opc), target_sheet (string, for kind=opc)."
                    ),
                },
                "source_quote": {"type": "string"},
            },
            "required": ["kind", "label", "bbox", "confidence"],
            "additionalProperties": False,
        },
    },
    {
        "name": "list_annotations",
        "description": "Return the annotations recorded so far, optionally filtered by kind.",
        "input_schema": {
            "type": "object",
            "properties": {"kind": {"type": "string"}},
            "additionalProperties": False,
        },
    },
    {
        "name": "finish",
        "description": (
            "Conclude with a final answer to the user's question. Once called, the loop ends."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "answer": {"type": "string"},
                "confidence": {"type": "string", "enum": ["high", "medium", "low"]},
                "supporting_bboxes": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "x": {"type": "integer"},
                            "y": {"type": "integer"},
                            "w": {"type": "integer"},
                            "h": {"type": "integer"},
                        },
                    },
                },
            },
            "required": ["answer"],
            "additionalProperties": False,
        },
    },
]


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------


def _pil_to_image_block(img: Image.Image) -> dict[str, Any]:
    """Encode a PIL image as a size-safe Anthropic image content-block.

    Delegates to ``vision.encode.encode_image_block`` which guarantees the
    encoded bytes fit under Anthropic's 5 MiB inline-image cap (PNG → JPEG-90
    → progressively downscaled JPEG fallback).
    """
    return encode_image_block(img)


def _register_view(state: AgentState, tag: str, view_info: Any) -> None:
    state.views[tag] = view_info
    state.last_view_tag = tag


def dispatch(
    name: str,
    raw_input: dict[str, Any],
    state: AgentState,
    view_provider: ViewProvider,
) -> ToolResult:
    """Route a single tool_use call to its handler and build a ToolResult."""
    try:
        if name == "get_overview":
            args = _GetOverviewIn.model_validate(raw_input)
            img, view_info = view_provider.get_overview(max_dim=args.max_dim)
            tag = "overview"
            _register_view(state, tag, view_info)
            return ToolResult(
                content=[
                    {"type": "text", "text": f"view_tag={tag}; view_size={view_info.view_size}; "
                                              f"page_bbox={view_info.page_bbox.model_dump()}"},
                    _pil_to_image_block(img),
                ]
            )

        if name == "list_tiles":
            _ListTilesIn.model_validate(raw_input)
            meta = view_provider.list_tiles()
            return ToolResult(content=[{"type": "text", "text": _render_tile_list(meta)}])

        if name == "get_tile":
            args = _GetTileIn.model_validate(raw_input)
            # Enforce per-tile image-fetch cap (spec §6.3).
            count = state.tile_fetch_counts.get(args.tile_id, 0)
            if count >= 3:
                return ToolResult(
                    content=[{"type": "text", "text": f"get_tile denied: tile {args.tile_id} already fetched {count} times."}],
                    is_error=True,
                )
            img, view_info = view_provider.get_tile(args.tile_id)
            state.tile_fetch_counts[args.tile_id] = count + 1
            tag = f"tile:{args.tile_id}"
            _register_view(state, tag, view_info)
            content: list[dict[str, Any]] = [
                {"type": "text", "text": f"view_tag={tag}; view_size={view_info.view_size}; "
                                          f"page_bbox={view_info.page_bbox.model_dump()}"},
            ]
            # Cross-tile stitch hints: surface previously-recorded line endpoints
            # that land on this tile's boundary so the agent can trace their
            # continuation instead of re-discovering them from pixels alone.
            hint_text = _render_stitch_hints(_compute_stitch_hints(state, view_info))
            if hint_text:
                content.append({"type": "text", "text": hint_text})
            content.append(_pil_to_image_block(img))
            return ToolResult(content=content)

        if name == "get_region":
            args = _GetRegionIn.model_validate(raw_input)
            img, view_info = view_provider.get_region(args.x, args.y, args.w, args.h)
            tag = f"region:{args.x},{args.y},{args.w},{args.h}"
            _register_view(state, tag, view_info)
            state.region_fetches.append(
                RegionFetch(x=args.x, y=args.y, w=args.w, h=args.h, image=img)
            )
            return ToolResult(
                content=[
                    {"type": "text", "text": f"view_tag={tag}; view_size={view_info.view_size}; "
                                              f"page_bbox={view_info.page_bbox.model_dump()}"},
                    _pil_to_image_block(img),
                ]
            )

        if name == "annotate":
            args = _AnnotateIn.model_validate(raw_input)
            tag = args.view_tag or state.last_view_tag
            if tag is None or tag not in state.views:
                return ToolResult(
                    content=[{"type": "text", "text": "annotate failed: no active view. Call get_overview / get_tile / get_region first."}],
                    is_error=True,
                )
            # Line / connection annotations without endpoints produce ghost edges —
            # the reconciler has no geometry to snap. Reject with a corrective note.
            if args.kind in ("line", "connection") and len(args.endpoints) < 2:
                return ToolResult(
                    content=[{
                        "type": "text",
                        "text": (
                            f"annotate rejected: kind='{args.kind}' requires >=2 endpoints "
                            "tracing the polyline (source first, target last). Re-emit with "
                            "endpoints=[{x,y}, ...] in view-pixel coordinates."
                        ),
                    }],
                    is_error=True,
                )
            view_info = state.views[tag]
            endpoints = [
                Point(x_local=p.x, y_local=p.y)
                for p in args.endpoints
            ]
            try:
                anno: Annotation = make_annotation(
                    page_index=state.page.page_index,
                    kind=args.kind,
                    label=args.label,
                    bbox_local=BBox(**args.bbox.model_dump()),
                    view=view_info,
                    confidence=args.confidence,
                    endpoints=endpoints,
                    line_type=args.line_type,
                    attributes=args.attributes,
                    source_quote=args.source_quote,
                )
            except Exception as exc:
                return ToolResult(
                    content=[{"type": "text", "text": f"annotate rejected: {exc}"}],
                    is_error=True,
                )
            state.annotations.add(anno)
            return ToolResult(
                content=[{"type": "text", "text": f"recorded annotation {anno.id[:8]} kind={anno.kind} label={anno.label!r}"}]
            )

        if name == "list_annotations":
            args = _ListAnnotationsIn.model_validate(raw_input)
            items = state.annotations.all() if args.kind is None else state.annotations.by_kind(args.kind)
            return ToolResult(content=[{"type": "text", "text": _render_annotation_list(items)}])

        if name == "finish":
            args = _FinishIn.model_validate(raw_input)
            required_tiles = state.required_tile_ids
            if required_tiles:
                visited_tiles = required_tiles.intersection(state.tile_fetch_counts)
                required_count = math.ceil(
                    len(required_tiles) * state.minimum_tile_coverage
                )
                if len(visited_tiles) < required_count:
                    missing = sorted(required_tiles - visited_tiles)
                    preview = ", ".join(missing[:8])
                    if len(missing) > 8:
                        preview += f", … (+{len(missing) - 8} more)"
                    return ToolResult(
                        content=[
                            {
                                "type": "text",
                                "text": (
                                    "finish rejected: tile coverage is "
                                    f"{len(visited_tiles)}/{len(required_tiles)}; "
                                    f"at least {required_count} tiles are required. "
                                    f"Fetch the missing tiles first: {preview}"
                                ),
                            }
                        ],
                        is_error=True,
                    )
            state.final_answer = args.answer
            state.final_confidence = args.confidence
            state.done = True
            state.completion_status = "complete"
            state.completion_reason = "finish"
            return ToolResult(content=[{"type": "text", "text": "finish acknowledged."}])

        if name == "lookup_symbol":
            # Imported lazily to avoid a circular import (lookup_symbol imports
            # ToolResult from this module).
            from diagex.agent.lookup_symbol import dispatch_lookup_symbol
            return dispatch_lookup_symbol(raw_input, state)

    except ValidationError as exc:
        return ToolResult(content=[{"type": "text", "text": f"invalid input: {exc}"}], is_error=True)

    return ToolResult(content=[{"type": "text", "text": f"unknown tool: {name}"}], is_error=True)


def _render_tile_list(meta: list[dict[str, Any]]) -> str:
    lines = [f"{len(meta)} tiles:"]
    for m in meta:
        b = m.get("bbox")
        lines.append(f"  {m['id']}: bbox={b}")
    return "\n".join(lines)


def build_phase2_tools(*, with_lookup: bool) -> list[dict[str, Any]]:
    """Return the Phase 2 tool set: the 7 Phase 1 tools + optional lookup_symbol."""
    base = list(TOOL_SCHEMAS)
    if with_lookup:
        # Imported here to avoid a circular import at module load.
        from diagex.agent.lookup_symbol import LOOKUP_SYMBOL_SCHEMA
        base.append(LOOKUP_SYMBOL_SCHEMA)
    return base


def _render_annotation_list(items: list[Annotation]) -> str:
    if not items:
        return "no annotations yet."
    lines = [f"{len(items)} annotations:"]
    for a in items:
        lines.append(
            f"  {a.id[:8]} p{a.page_index} {a.kind} {a.label!r} "
            f"bbox_global={a.bbox_global.model_dump()} conf={a.confidence}"
        )
    return "\n".join(lines)


def _compute_stitch_hints(
    state: AgentState,
    view_info: ViewInfo,
    stitch_radius: int = LINE_STITCH_RADIUS_PX,
) -> list[dict[str, Any]]:
    """Collect line endpoints from prior tiles that land on this tile's boundary.

    Returns a list of view-local coordinate hints — one per pending continuation
    — so the agent can trace the line forward instead of re-discovering it.
    """
    tb = view_info.page_bbox
    ox, oy = view_info.origin
    incoming_tile_id = view_info.tile_id
    hints: list[dict[str, Any]] = []
    # De-dupe near-coincident endpoints (same crossing annotated twice in overlap).
    seen: set[tuple[int, int]] = set()

    x_min, y_min = tb.x, tb.y
    x_max, y_max = tb.x + tb.w, tb.y + tb.h

    def within_bbox(gx: float, gy: float) -> bool:
        # Tiles overlap, so the "shared boundary" of the previous tile lies well
        # inside the new tile. Any on_view_edge endpoint within this tile's
        # footprint is a pending continuation.
        return (
            x_min - stitch_radius <= gx <= x_max + stitch_radius
            and y_min - stitch_radius <= gy <= y_max + stitch_radius
        )

    for a in state.annotations.all():
        if a.kind not in ("line", "connection"):
            continue
        if a.tile_id == incoming_tile_id:
            continue
        if len(a.endpoints) < 2:
            continue
        # Only the terminal endpoints cross-stitch; intermediate bends are mid-line.
        for idx in (0, len(a.endpoints) - 1):
            ep = a.endpoints[idx]
            if not ep.on_view_edge:
                continue
            gx, gy = float(ep.x_global), float(ep.y_global)
            if not within_bbox(gx, gy):
                continue
            lx = int(round(gx - ox))
            ly = int(round(gy - oy))
            bucket = (lx // max(1, stitch_radius), ly // max(1, stitch_radius))
            if bucket in seen:
                continue
            seen.add(bucket)
            hints.append(
                {
                    "lx": lx,
                    "ly": ly,
                    "line_type": a.line_type or "line",
                    "line_id": str((a.attributes or {}).get("line_id", "") or ""),
                    "from_tile": a.tile_id or "?",
                }
            )
    return hints


def _render_stitch_hints(hints: list[dict[str, Any]]) -> str:
    if not hints:
        return ""
    header = (
        f"NOTE: {len(hints)} line(s) from neighbouring tiles enter this tile's "
        f"boundary. Trace each continuation to its destination (or to the next "
        f"boundary it crosses) and emit an annotate call whose FIRST endpoint "
        f"is at the listed view-pixel coordinate:"
    )
    lines = [header]
    for h in hints:
        tag = f" line_id={h['line_id']!r}" if h["line_id"] else ""
        lines.append(
            f"  - ({h['lx']}, {h['ly']}) [{h['line_type']}] "
            f"from {h['from_tile']}{tag}"
        )
    return "\n".join(lines)
