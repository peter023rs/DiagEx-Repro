"""Adaptive zoom-in pass for dangling / unsnapped P&ID edges.

Spec §5.5 extension. After the first deterministic `reconcile()`, this module
re-examines every line endpoint that landed on a tile boundary without a
counterpart (`unstitched_line_endpoint` conflicts) and every edge whose
endpoints could not be snapped to a node (`snap_note` containing
"unsnappable", or empty `from_node`/`to_node`). For each target it runs a
focused ReAct sub-loop over the existing `ReactRuntime`, with a
`_FocusedViewProvider` that exposes only a small page region, and a
constrained tool subset (`get_overview`, `get_region`, `annotate`,
`list_annotations`, `finish`). The agent traces the line, emits one or more
extension annotations, and the caller re-runs reconcile() so the new
geometry can stitch and snap.

Cost: per page ≤ `max_edge_resolves_per_page` targets, each capped at
`max_steps_per_edge` LLM steps. Spend is tagged `tile_id="edge_resolve"` in
cost.json so it is distinguishable from the main walk.

Audit log: `runs/<run_id>/edge_resolve.jsonl` — one record per target.
"""

from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from PIL import Image

from diagex.agent.runtime import ReactRuntime, RunConfig
from diagex.agent.state import AgentState
from diagex.agent.tools import TOOL_SCHEMAS
from diagex.llm.prompts.edge_resolve import build_edge_resolve_system_prompt
from diagex.ui.progress import NullReporter
from diagex.vision.models import Annotation, BBox, DiagramPage
from diagex.vision.views import ViewInfo, ViewProvider


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class EdgeResolveConfig:
    max_edge_resolves_per_page: int = 15
    focus_window_px: int = 400          # half-size of the page-coord crop centred on the endpoint
    max_steps_per_edge: int = 5
    overview_max_dim: int = 1400        # downsample cap for the focused overview
    include_unsnapped_edges: bool = True  # also resolve edges with snap_note containing "unsnappable"
    dedup_target_radius_px: int = 50    # collapse near-coincident targets on the same page
    anchor_tol_px: int = 60             # max distance from a new annotation's endpoint to the target
    max_tokens_per_step: int = 4000


# ---------------------------------------------------------------------------
# Audit record
# ---------------------------------------------------------------------------


@dataclass
class EdgeResolveRecord:
    target_index: int
    page_index: int
    endpoint_xy: tuple[int, int]
    source_kind: str               # "unstitched_conflict" | "unsnapped_edge"
    source_ref: str                # opaque pointer back to the originating conflict / edge
    verdict: str                   # "continued" | "terminates" | "uncertain" | "skipped" | "error"
    steps: int = 0
    new_annotation_ids: list[str] = field(default_factory=list)
    detail: str = ""


# ---------------------------------------------------------------------------
# Tools subset for the focused pass
# ---------------------------------------------------------------------------


_ALLOWED_TOOLS = {"get_overview", "get_region", "annotate", "list_annotations", "finish"}


def _filter_tool_schemas(base: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [t for t in base if t.get("name") in _ALLOWED_TOOLS]


# ---------------------------------------------------------------------------
# Internal target representation
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class _Target:
    page_index: int
    x: int
    y: int
    line_type: Optional[str]
    source_kind: str               # "unstitched_conflict" | "unsnapped_edge"
    source_ref: str                # conflict index / edge id, for audit


def _collect_targets(graph: Any, cfg: EdgeResolveConfig) -> list[_Target]:
    """Walk graph.conflicts and graph.edges to seed the resolve queue.

    Targets are deduplicated within `dedup_target_radius_px` on the same page
    so a single ambiguous junction does not chew through the per-page budget,
    and the per-page cap is applied last so highest-priority (conflict-typed)
    targets win when budget is tight.
    """
    raw: list[_Target] = []
    nodes_by_id = {n.id: n for n in graph.nodes}

    # (1) unstitched_line_endpoint conflicts — the strongest signal: the
    #     reconciler already determined the endpoint has no neighbour.
    for ci, c in enumerate(graph.conflicts or []):
        if str(c.get("type", "")) != "unstitched_line_endpoint":
            continue
        try:
            page_idx = int(c.get("page_index", -1))
            x = int(c.get("x", 0))
            y = int(c.get("y", 0))
        except (TypeError, ValueError):
            continue
        if page_idx < 0:
            continue
        line_type = c.get("line_type")
        raw.append(
            _Target(
                page_index=page_idx,
                x=x,
                y=y,
                line_type=str(line_type) if line_type else None,
                source_kind="unstitched_conflict",
                source_ref=f"c{ci}:{c.get('annotation_id', '')}",
            )
        )

    # (2) unsnapped / dangling edges — endpoint failed to find any node within
    #     the snap radius. Less precise (the polyline endpoint may already be
    #     close to the right node) but still worth a focused look.
    if cfg.include_unsnapped_edges:
        for e in graph.edges:
            note = str(e.attributes.get("snap_note", "") or "")
            unsnapped = "unsnappable" in note
            dangling = (not e.from_node) or (not e.to_node)
            if not (unsnapped or dangling):
                continue
            if not e.polyline_global:
                continue
            page_idx = _edge_page_index(e, nodes_by_id)
            if page_idx < 0:
                continue
            head = e.polyline_global[0]
            tail = e.polyline_global[-1]
            ends: list[tuple[int, int]] = []
            if not e.from_node:
                ends.append((int(head[0]), int(head[1])))
            if not e.to_node:
                ends.append((int(tail[0]), int(tail[1])))
            if not ends and unsnapped:
                # Both endpoints recorded as unsnappable but somehow nodes are set.
                # Fall back to both ends; the dedup pass will merge near-coincidents.
                ends = [(int(head[0]), int(head[1])), (int(tail[0]), int(tail[1]))]
            for x, y in ends:
                raw.append(
                    _Target(
                        page_index=page_idx,
                        x=x,
                        y=y,
                        line_type=e.line_type,
                        source_kind="unsnapped_edge",
                        source_ref=f"e:{e.id}",
                    )
                )

    # (3) Dedup near-coincident targets on the same page.
    deduped: list[_Target] = []
    r2 = cfg.dedup_target_radius_px * cfg.dedup_target_radius_px
    for t in raw:
        skip = False
        for d in deduped:
            if d.page_index != t.page_index:
                continue
            dx = d.x - t.x
            dy = d.y - t.y
            if dx * dx + dy * dy <= r2:
                skip = True
                break
        if not skip:
            deduped.append(t)

    # (4) Per-page budget. Conflicts come before edge-derived targets so they
    #     win when budget is tight.
    counts: dict[int, int] = defaultdict(int)
    capped: list[_Target] = []
    for t in deduped:
        if counts[t.page_index] >= cfg.max_edge_resolves_per_page:
            continue
        capped.append(t)
        counts[t.page_index] += 1
    return capped


def _edge_page_index(edge: Any, nodes_by_id: dict[str, Any]) -> int:
    for nid in (edge.from_node, edge.to_node):
        n = nodes_by_id.get(nid)
        if n is not None:
            return int(n.page_index)
    return -1


# ---------------------------------------------------------------------------
# Focused view provider
# ---------------------------------------------------------------------------


class _FocusedViewProvider(ViewProvider):
    """ViewProvider whose `get_overview` returns a small region centred on the target.

    `get_region` falls through to the parent (full-page crop), so the agent
    can still zoom in further via page-coordinate bboxes — the prompt steers
    it to stay within the focused area. `get_tile` / `list_tiles` are
    deliberately disabled (the runtime never offers them in `tools_override`).
    """

    def __init__(
        self,
        page: DiagramPage,
        focus_xy: tuple[int, int],
        window_px: int,
        overview_max_dim: int,
    ) -> None:
        super().__init__(page, tiles=[])
        self.focus_xy = focus_xy
        self.window_px = int(window_px)
        self.overview_max_dim = int(overview_max_dim)
        self._focused_overview_cache: tuple[Image.Image, ViewInfo] | None = None

    def get_overview(self, max_dim: int = 2000) -> tuple[Image.Image, ViewInfo]:
        if self._focused_overview_cache is not None:
            return self._focused_overview_cache
        if self.page.image is None:
            raise ValueError("DiagramPage.image is None; cannot produce focused overview")

        cx, cy = self.focus_xy
        x0 = max(0, cx - self.window_px)
        y0 = max(0, cy - self.window_px)
        x1 = min(self.page.width, cx + self.window_px)
        y1 = min(self.page.height, cy + self.window_px)
        if x1 <= x0 or y1 <= y0:
            raise ValueError(
                f"Empty focused window for ({cx},{cy}) on page {self.page.width}x{self.page.height}"
            )

        crop = self.page.image.crop((x0, y0, x1, y1))
        crop_w, crop_h = crop.size

        target_dim = min(self.overview_max_dim, int(max_dim))
        long_side = max(crop_w, crop_h)
        if long_side > target_dim:
            scale = target_dim / long_side
            new_size = (max(1, int(crop_w * scale)), max(1, int(crop_h * scale)))
            view_img = crop.resize(new_size, Image.BILINEAR)
        else:
            view_img = crop

        view_w, view_h = view_img.size
        info = ViewInfo(
            source_view="overview",
            origin=(x0, y0),
            scale_x=view_w / max(1, crop_w),
            scale_y=view_h / max(1, crop_h),
            view_size=(view_w, view_h),
            page_bbox=BBox(x=x0, y=y0, w=crop_w, h=crop_h),
        )
        self._focused_overview_cache = (view_img, info)
        return view_img, info

    def get_tile(self, tile_id: str) -> tuple[Image.Image, ViewInfo]:  # type: ignore[override]
        raise KeyError(
            f"get_tile is disabled in the focused edge-resolve view (requested {tile_id!r})"
        )

    def list_tiles(self) -> list[dict[str, Any]]:  # type: ignore[override]
        return []


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def resolve_dangling_edges(
    *,
    graph: Any,
    pages_by_index: dict[int, DiagramPage],
    runtime: ReactRuntime,
    config: Optional[EdgeResolveConfig] = None,
    log_path: Optional[Path] = None,
) -> tuple[list[Annotation], list[EdgeResolveRecord]]:
    """Run a focused ReAct sub-loop per dangling endpoint.

    Returns a list of new line/connection annotations the agent emitted (each
    tagged with `attributes["origin"] = "edge_resolve"` and a back-pointer to
    the originating target via `attributes["resolves_target"]`), plus a list
    of audit records. The caller is expected to append the new annotations to
    the master annotation list and re-run `reconcile()` so the geometry can
    re-stitch and re-snap.

    Mutates `runtime.system_blocks`, `runtime.tools_override`, and
    `runtime.reporter` for the duration of the call, restoring them on exit.
    """
    cfg = config or EdgeResolveConfig()

    targets = _collect_targets(graph, cfg)
    if not targets:
        return [], []

    saved_system_blocks = runtime.system_blocks
    saved_tools_override = runtime.tools_override
    saved_reporter = runtime.reporter

    base_tools = saved_tools_override if saved_tools_override is not None else TOOL_SCHEMAS
    runtime.tools_override = _filter_tool_schemas(base_tools)
    runtime.reporter = NullReporter()

    new_annotations: list[Annotation] = []
    records: list[EdgeResolveRecord] = []

    try:
        for tgt_idx, target in enumerate(targets):
            page = pages_by_index.get(target.page_index)
            if page is None or page.image is None:
                records.append(
                    EdgeResolveRecord(
                        target_index=tgt_idx,
                        page_index=target.page_index,
                        endpoint_xy=(target.x, target.y),
                        source_kind=target.source_kind,
                        source_ref=target.source_ref,
                        verdict="skipped",
                        detail="no_page_image",
                    )
                )
                continue

            fvp = _FocusedViewProvider(
                page=page,
                focus_xy=(target.x, target.y),
                window_px=cfg.focus_window_px,
                overview_max_dim=cfg.overview_max_dim,
            )

            runtime.system_blocks = build_edge_resolve_system_prompt(
                line_type=target.line_type,
                endpoint_xy=(target.x, target.y),
                focus_window_px=cfg.focus_window_px,
            )

            state = AgentState(
                question=(
                    f"Trace the dangling {target.line_type or 'line'} endpoint at "
                    f"page-pixel ({target.x}, {target.y}) to its real terminator, "
                    "or call finish if it truly terminates here."
                ),
                page=page,
            )

            try:
                runtime.run(
                    state=state,
                    view_provider=fvp,
                    run_cfg=RunConfig(
                        effort="medium",
                        max_steps=cfg.max_steps_per_edge,
                        max_tokens=cfg.max_tokens_per_step,
                    ),
                )
            except Exception as exc:  # noqa: BLE001 - per-target isolation
                records.append(
                    EdgeResolveRecord(
                        target_index=tgt_idx,
                        page_index=target.page_index,
                        endpoint_xy=(target.x, target.y),
                        source_kind=target.source_kind,
                        source_ref=target.source_ref,
                        verdict="error",
                        steps=state.steps,
                        detail=repr(exc),
                    )
                )
                continue

            verdict = _normalise_verdict(state.final_answer)
            target_new = [a for a in state.annotations.all() if a.kind in ("line", "connection")]
            for a in target_new:
                a.attributes["origin"] = "edge_resolve"
                a.attributes["resolves_target"] = target.source_ref
                _mark_anchor_endpoint_on_edge(a, (target.x, target.y), cfg.anchor_tol_px)
                new_annotations.append(a)

            records.append(
                EdgeResolveRecord(
                    target_index=tgt_idx,
                    page_index=target.page_index,
                    endpoint_xy=(target.x, target.y),
                    source_kind=target.source_kind,
                    source_ref=target.source_ref,
                    verdict=verdict,
                    steps=state.steps,
                    new_annotation_ids=[a.id for a in target_new],
                )
            )
    finally:
        runtime.system_blocks = saved_system_blocks
        runtime.tools_override = saved_tools_override
        runtime.reporter = saved_reporter

    if log_path is not None and records:
        _append_log(log_path, records)

    return new_annotations, records


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_VERDICT_ALIASES = {
    "continued": "continued",
    "continues": "continued",
    "extended": "continued",
    "terminates": "terminates",
    "terminate": "terminates",
    "terminated": "terminates",
    "uncertain": "uncertain",
    "unsure": "uncertain",
    "unknown": "uncertain",
    "done": "uncertain",  # generic finish without a verdict
}


def _normalise_verdict(answer: str | None) -> str:
    if not answer:
        return "uncertain"
    head = answer.strip().split()[0].lower().strip(".,;:!?")
    return _VERDICT_ALIASES.get(head, "uncertain")


def _mark_anchor_endpoint_on_edge(
    anno: Annotation,
    anchor_xy: tuple[int, int],
    tol_px: int,
) -> None:
    """Force `on_view_edge=True` on whichever terminal endpoint sits closest to
    the original dangling point, so `_stitch_lines` will pair the new
    annotation back into the original line during re-reconciliation.

    Falls back silently when the new polyline does not actually reach the
    anchor — that target's verdict stays `continued` but the geometry will
    not stitch, which is reflected in the post-resolve graph state.
    """
    if not anno.endpoints:
        return
    ax, ay = anchor_xy
    head = anno.endpoints[0]
    tail = anno.endpoints[-1]
    d_head = ((head.x_global - ax) ** 2 + (head.y_global - ay) ** 2) ** 0.5
    d_tail = ((tail.x_global - ax) ** 2 + (tail.y_global - ay) ** 2) ** 0.5
    if d_head <= d_tail:
        chosen, dist = head, d_head
    else:
        chosen, dist = tail, d_tail
    if dist <= tol_px:
        chosen.on_view_edge = True


def _append_log(log_path: Path, records: list[EdgeResolveRecord]) -> None:
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with log_path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(
                json.dumps(
                    {
                        "target_index": r.target_index,
                        "page_index": r.page_index,
                        "endpoint_xy": list(r.endpoint_xy),
                        "source_kind": r.source_kind,
                        "source_ref": r.source_ref,
                        "verdict": r.verdict,
                        "steps": r.steps,
                        "new_annotation_ids": r.new_annotation_ids,
                        "detail": r.detail,
                    }
                )
                + "\n"
            )
