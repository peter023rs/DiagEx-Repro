"""Spec §5.5 — deterministic reconciliation (NO LLM arbitration in Phase 1).

Responsibilities:
  1. Dedup in overlap zones: (kind, normalised label) exact match, then IoU >= 0.30.
  2. Line stitching: match on-view-edge endpoints across tile boundaries.
  3. Tag reconciliation: keep highest-confidence reading; rest -> alternate_readings.
  4. Graph assembly: edges snap endpoints to nearest node within 30 px.
  5. Cross-sheet OPC matching by normalised label equality.

`conflicts[]` is seeded with (a) IoU grey-zone [0.15, 0.30] and
(b) single-character OCR flips (O<->0, I<->1, 5<->S).
"""

from __future__ import annotations

import re
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any, Iterable

from diagex.vision.models import (
    Annotation,
    BBox,
    Confidence,
    Kind,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)

# ---------------------------------------------------------------------------
# Tunables (spec §5.5 — [DECISION] values)
# ---------------------------------------------------------------------------

DEDUP_IOU_STRONG = 0.30
IOU_GREY_ZONE = (0.15, 0.30)
LINE_STITCH_RADIUS_PX = 20
SNAP_RADIUS_PX = 30

_LINE_KINDS = {"line", "connection"}
_CONFIDENCE_ORDER: dict[Confidence, int] = {"low": 0, "medium": 1, "high": 2}

# OCR flips commonly seen in bubble OCR.
_OCR_FLIP_PAIRS = [("O", "0"), ("I", "1"), ("5", "S")]


# ---------------------------------------------------------------------------
# Label normalisation (spec §5.5 item 5)
# ---------------------------------------------------------------------------


_RE_NON_ALNUM = re.compile(r"[^A-Z0-9_\-]+")
# Run of digits preceded by non-digit (or start) — collapse leading zeros.
_RE_DIGIT_RUN = re.compile(r"(?<!\d)(0+)(\d+)")


def normalise_label(s: str) -> str:
    """Normalise a tag / OPC label per §5.5 item 5.

    Rules (in order):
      (a) uppercase,
      (b) strip non-alphanumeric except `-` and `_`,
      (c) collapse leading zeros in any digit run (OPC-0012 -> OPC-12,
          OPC0012 -> OPC12),
      (d) trim whitespace.

    Applied AFTER non-alnum stripping so letters adjacent to digits no longer
    block the leading-zero collapse (e.g. "OPC0012" -> "OPC12").
    """
    if s is None:
        return ""
    t = s.strip().upper()
    t = _RE_NON_ALNUM.sub("", t)
    # Collapse leading zeros in every digit run (keep trailing significant digits).
    t = _RE_DIGIT_RUN.sub(lambda m: m.group(2), t)
    return t.strip()


# ---------------------------------------------------------------------------
# Strategy (kept minimal — Phase 1 has only one)
# ---------------------------------------------------------------------------


@dataclass
class ReconcileStrategy:
    dedup_iou: float = DEDUP_IOU_STRONG
    iou_grey_zone: tuple[float, float] = IOU_GREY_ZONE
    line_stitch_radius_px: int = LINE_STITCH_RADIUS_PX
    snap_radius_px: int = SNAP_RADIUS_PX
    # Line endpoints rarely land on the target equipment's bbox — the LLM
    # traces pipes to the nearest pipe-run, not the flange. Effective radius
    # is max(snap_radius_px, snap_radius_equipment_mult * median_equipment_dim)
    # so a drawing at any scale snaps with roughly one-equipment-width slack.
    snap_radius_equipment_mult: float = 1.5
    # Second-pass loose radius for endpoints the first pass left unsnapped.
    # Uses the same equipment-dimension scaling; only applied to edges with
    # at least one endpoint already snapped, so a wild standalone polyline
    # isn't absorbed by an unrelated node across the drawing.
    snap_loose_equipment_mult: float = 3.0
    arbitrate: bool = False  # Phase 1: LLM arbitration disabled (spec §5.5).


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _confidence_rank(c: Confidence | str) -> int:
    return _CONFIDENCE_ORDER.get(c, 0)  # type: ignore[arg-type]


def _best_confidence(items: Iterable[Confidence]) -> Confidence:
    best: Confidence = "low"
    for c in items:
        if _confidence_rank(c) > _confidence_rank(best):
            best = c  # type: ignore[assignment]
    return best


def _new_entity_id(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def _endpoint_page_xy(ep: Any) -> tuple[float, float]:
    return float(ep.x_global), float(ep.y_global)


def _dist(p: tuple[float, float], q: tuple[float, float]) -> float:
    dx = p[0] - q[0]
    dy = p[1] - q[1]
    return (dx * dx + dy * dy) ** 0.5


def _ocr_flip_distance_one(a: str, b: str) -> bool:
    """True iff `a` and `b` differ by exactly one single-char OCR flip pair."""
    if len(a) != len(b) or a == b:
        return False
    diffs = [(x, y) for x, y in zip(a, b) if x != y]
    if len(diffs) != 1:
        return False
    x, y = diffs[0]
    for p, q in _OCR_FLIP_PAIRS:
        if {x, y} == {p, q}:
            return True
    return False


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


@dataclass
class _NodeCluster:
    kind: Kind
    label: str
    norm_label: str
    bbox_global: BBox
    page_index: int
    attributes: dict[str, Any] = field(default_factory=dict)
    confidence: Confidence = "low"
    alternate_readings: list[str] = field(default_factory=list)
    source_annotation_ids: list[str] = field(default_factory=list)


def reconcile(
    annotations: list[Annotation],
    strategy: ReconcileStrategy | None = None,
    source_path: str = "",
) -> ReconciledGraph:
    strat = strategy or ReconcileStrategy()

    # Split up-front: point-like (nodes) vs line-like (edges).
    node_annos = [a for a in annotations if a.kind not in _LINE_KINDS]
    line_annos = [a for a in annotations if a.kind in _LINE_KINDS]

    # Per-page reconciliation of point-like entities.
    conflicts: list[dict[str, Any]] = []
    clusters_by_page: dict[int, list[_NodeCluster]] = defaultdict(list)
    for a in node_annos:
        _merge_into_page(a, clusters_by_page[a.page_index], strat, conflicts)

    # Tag-reconciliation pass (§5.5 item 3): OCR-flip-near-duplicates on same page.
    for page_idx, clusters in clusters_by_page.items():
        _flag_ocr_flips(clusters, conflicts, page_idx)

    # Emit ReconciledNodes.
    nodes: list[ReconciledNode] = []
    node_index_by_page: dict[int, list[ReconciledNode]] = defaultdict(list)
    for page_idx, clusters in clusters_by_page.items():
        for cl in clusters:
            node = ReconciledNode(
                id=_new_entity_id("n"),
                kind=cl.kind,
                label=cl.label,
                bbox_global=cl.bbox_global,
                page_index=page_idx,
                attributes=cl.attributes,
                confidence=cl.confidence,
                alternate_readings=cl.alternate_readings,
                source_annotation_ids=cl.source_annotation_ids,
            )
            nodes.append(node)
            node_index_by_page[page_idx].append(node)

    # Line-like reconciliation: stitch on-edge endpoints, then dedup.
    stitched_lines = _stitch_lines(line_annos, strat, conflicts)

    # Edge assembly with nearest-node snapping. Edges whose endpoints cannot
    # be resolved are dropped (recorded in `conflicts` by `_build_edge`).
    edges: list[ReconciledEdge] = []
    for grp in stitched_lines:
        edge = _build_edge(grp, node_index_by_page, strat, conflicts)
        if edge is not None:
            edges.append(edge)

    # Cross-sheet OPC reconciliation.
    dangling_opcs, cross_edges = _cross_sheet_opcs(nodes, conflicts)
    edges.extend(cross_edges)

    graph = ReconciledGraph(
        source_path=source_path,
        nodes=nodes,
        edges=edges,
        dangling_opcs=dangling_opcs,
        conflicts=conflicts,
    )
    return graph


# ---------------------------------------------------------------------------
# Per-page node merging
# ---------------------------------------------------------------------------


def _merge_into_page(
    anno: Annotation,
    clusters: list[_NodeCluster],
    strat: ReconcileStrategy,
    conflicts: list[dict[str, Any]],
) -> None:
    norm = normalise_label(anno.label)

    # Pass 1: (kind, normalised label) exact match.
    if norm:
        for cl in clusters:
            if cl.kind == anno.kind and cl.norm_label == norm:
                _absorb_into_cluster(cl, anno, reason="label_match")
                return

    # Pass 2: IoU-based.
    best_cl: _NodeCluster | None = None
    best_iou = 0.0
    for cl in clusters:
        if cl.kind != anno.kind:
            continue
        iou = cl.bbox_global.iou(anno.bbox_global)
        if iou > best_iou:
            best_iou = iou
            best_cl = cl

    if best_cl is not None and best_iou >= strat.dedup_iou:
        _absorb_into_cluster(best_cl, anno, reason="iou_match")
        return

    # Grey-zone: seed a conflict but still treat as a new cluster.
    if best_cl is not None and strat.iou_grey_zone[0] <= best_iou < strat.iou_grey_zone[1]:
        conflicts.append(
            {
                "type": "iou_grey_zone",
                "iou": round(best_iou, 3),
                "kind": anno.kind,
                "labels": [best_cl.label, anno.label],
                "page_index": anno.page_index,
                "annotation_ids": [*best_cl.source_annotation_ids, anno.id],
            }
        )

    clusters.append(
        _NodeCluster(
            kind=anno.kind,
            label=anno.label,
            norm_label=norm,
            bbox_global=anno.bbox_global,
            page_index=anno.page_index,
            attributes=dict(anno.attributes or {}),
            confidence=anno.confidence,
            alternate_readings=[],
            source_annotation_ids=[anno.id],
        )
    )


def _absorb_into_cluster(cl: _NodeCluster, anno: Annotation, *, reason: str) -> None:
    cl.source_annotation_ids.append(anno.id)
    # Keep highest-confidence reading as the canonical label (§5.5 item 3).
    if _confidence_rank(anno.confidence) > _confidence_rank(cl.confidence):
        if cl.label and cl.label != anno.label:
            cl.alternate_readings.append(cl.label)
        cl.label = anno.label
        cl.norm_label = normalise_label(anno.label)
        cl.confidence = anno.confidence
        cl.bbox_global = anno.bbox_global  # prefer the higher-confidence bbox
    elif anno.label and anno.label != cl.label and anno.label not in cl.alternate_readings:
        cl.alternate_readings.append(anno.label)
    # Merge attributes shallow; existing keys win.
    for k, v in (anno.attributes or {}).items():
        cl.attributes.setdefault(k, v)


def _flag_ocr_flips(
    clusters: list[_NodeCluster],
    conflicts: list[dict[str, Any]],
    page_idx: int,
) -> None:
    for i in range(len(clusters)):
        for j in range(i + 1, len(clusters)):
            a = clusters[i]
            b = clusters[j]
            if a.kind != b.kind:
                continue
            if not a.norm_label or not b.norm_label:
                continue
            if _ocr_flip_distance_one(a.norm_label, b.norm_label):
                conflicts.append(
                    {
                        "type": "ocr_flip_candidate",
                        "kind": a.kind,
                        "labels": [a.label, b.label],
                        "page_index": page_idx,
                        "annotation_ids": [*a.source_annotation_ids, *b.source_annotation_ids],
                    }
                )


# ---------------------------------------------------------------------------
# Line stitching
# ---------------------------------------------------------------------------


@dataclass
class _LineGroup:
    annotations: list[Annotation] = field(default_factory=list)
    page_index: int = 0

    def confidence(self) -> Confidence:
        return _best_confidence([a.confidence for a in self.annotations]) if self.annotations else "low"

    def line_type(self) -> str | None:
        for a in self.annotations:
            if a.line_type:
                return a.line_type
        return None

    def polyline(self) -> list[tuple[int, int]]:
        pts: list[tuple[int, int]] = []
        for a in self.annotations:
            for ep in a.endpoints:
                pts.append((int(round(ep.x_global)), int(round(ep.y_global))))
        return pts

    def source_ids(self) -> list[str]:
        return [a.id for a in self.annotations]

    def endpoints_free(self) -> list[tuple[float, float, Annotation]]:
        """Endpoints at indices 0 / -1 not flagged on_view_edge — the 'open' ends."""
        out: list[tuple[float, float, Annotation]] = []
        for a in self.annotations:
            if not a.endpoints:
                continue
            head = a.endpoints[0]
            tail = a.endpoints[-1]
            out.append((float(head.x_global), float(head.y_global), a))
            out.append((float(tail.x_global), float(tail.y_global), a))
        return out


def _stitch_lines(
    line_annos: list[Annotation],
    strat: ReconcileStrategy,
    conflicts: list[dict[str, Any]],
) -> list[_LineGroup]:
    """Union-find on tile-edge endpoints within `line_stitch_radius_px`."""
    groups: list[_LineGroup] = [
        _LineGroup(annotations=[a], page_index=a.page_index) for a in line_annos
    ]

    # Collect (page_index, edge_endpoint xy, group_idx, anno, line_type).
    edge_eps: list[tuple[int, float, float, int, Annotation]] = []
    for gi, g in enumerate(groups):
        a = g.annotations[0]
        for ep in a.endpoints:
            if ep.on_view_edge:
                edge_eps.append((a.page_index, float(ep.x_global), float(ep.y_global), gi, a))

    # Merge groups whose edge-endpoints are within radius and share a compatible line_type.
    parent = list(range(len(groups)))

    def find(x: int) -> int:
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    def union(x: int, y: int) -> None:
        rx, ry = find(x), find(y)
        if rx != ry:
            parent[ry] = rx

    for i in range(len(edge_eps)):
        pi, xi, yi, gi, ai = edge_eps[i]
        for j in range(i + 1, len(edge_eps)):
            pj, xj, yj, gj, aj = edge_eps[j]
            if pi != pj:
                continue
            if find(gi) == find(gj):
                continue
            if _dist((xi, yi), (xj, yj)) > strat.line_stitch_radius_px:
                continue
            if ai.line_type and aj.line_type and ai.line_type != aj.line_type:
                continue
            union(gi, gj)

    # Collect groups.
    merged: dict[int, _LineGroup] = {}
    for idx, g in enumerate(groups):
        root = find(idx)
        if root not in merged:
            merged[root] = _LineGroup(annotations=[], page_index=g.page_index)
        merged[root].annotations.extend(g.annotations)

    # Flag unpaired on-edge endpoints as stitch conflicts (§5.5 arbitration criteria).
    for root, g in merged.items():
        # Count on_edge endpoints whose counterpart lies in the SAME group (stitched).
        unstitched: list[tuple[float, float, Annotation]] = []
        for a in g.annotations:
            for ep in a.endpoints:
                if not ep.on_view_edge:
                    continue
                x = float(ep.x_global)
                y = float(ep.y_global)
                # Is there another endpoint in this group within radius that also sits on an edge?
                paired = False
                for b in g.annotations:
                    if b is a:
                        continue
                    for ep2 in b.endpoints:
                        if not ep2.on_view_edge:
                            continue
                        if _dist((x, y), (float(ep2.x_global), float(ep2.y_global))) <= strat.line_stitch_radius_px:
                            paired = True
                            break
                    if paired:
                        break
                if not paired:
                    unstitched.append((x, y, a))
        for x, y, a in unstitched:
            conflicts.append(
                {
                    "type": "unstitched_line_endpoint",
                    "page_index": a.page_index,
                    "x": int(round(x)),
                    "y": int(round(y)),
                    "annotation_id": a.id,
                    "line_type": a.line_type,
                }
            )

    return list(merged.values())


# ---------------------------------------------------------------------------
# Edge assembly with snap-to-node
# ---------------------------------------------------------------------------


def _nearest_node(
    point: tuple[float, float],
    nodes: list[ReconciledNode],
    radius: int,
) -> ReconciledNode | None:
    best: ReconciledNode | None = None
    best_d = float("inf")
    for n in nodes:
        # Distance from point to bbox (0 if inside).
        bb = n.bbox_global
        dx = 0.0
        if point[0] < bb.x:
            dx = bb.x - point[0]
        elif point[0] > bb.x2:
            dx = point[0] - bb.x2
        dy = 0.0
        if point[1] < bb.y:
            dy = bb.y - point[1]
        elif point[1] > bb.y2:
            dy = point[1] - bb.y2
        d = (dx * dx + dy * dy) ** 0.5
        if d < best_d:
            best_d = d
            best = n
    if best is None or best_d > radius:
        return None
    return best


def _effective_snap_radius(
    page_nodes: list[ReconciledNode],
    strat: ReconcileStrategy,
    *,
    mult: float | None = None,
) -> int:
    """Pick a snap radius that scales with how big equipment is drawn on this page.

    A hardcoded 30 px is fine for A4 sketches but far too tight for an A0/A2
    drawing where equipment boxes are routinely 150-300 px wide. Using the
    median equipment dimension as the scale lets the agent's endpoint land
    within about one equipment-width of the real nozzle and still snap.

    `mult` defaults to `snap_radius_equipment_mult`; callers pass
    `snap_loose_equipment_mult` for the second-stage pass.
    """
    equipment_dims: list[int] = []
    for n in page_nodes:
        if n.kind not in ("equipment", "instrument", "opc"):
            continue
        equipment_dims.append(max(n.bbox_global.w, n.bbox_global.h))
    if not equipment_dims:
        return strat.snap_radius_px
    equipment_dims.sort()
    median_dim = equipment_dims[len(equipment_dims) // 2]
    effective_mult = strat.snap_radius_equipment_mult if mult is None else mult
    return max(strat.snap_radius_px, int(round(effective_mult * median_dim)))


def _build_edge(
    grp: _LineGroup,
    nodes_by_page: dict[int, list[ReconciledNode]],
    strat: ReconcileStrategy,
    conflicts: list[dict[str, Any]],
) -> ReconciledEdge | None:
    ordering = _order_line_group(grp, strat, conflicts)
    poly = _ordered_polyline(ordering)
    page_idx = grp.page_index
    page_nodes = nodes_by_page.get(page_idx, [])
    effective_radius = _effective_snap_radius(page_nodes, strat)

    from_node_id = ""
    to_node_id = ""
    attributes: dict[str, Any] = {}

    # Carry line-tag attributes across from grouped annotations. The agent may
    # emit the same line over several tiles with slightly different readings;
    # highest-confidence wins and alternates ride along as `alternate_line_ids`.
    _absorb_line_attributes(grp.annotations, attributes)

    if poly:
        head = (float(poly[0][0]), float(poly[0][1]))
        tail = (float(poly[-1][0]), float(poly[-1][1]))
        fn = _nearest_node(head, page_nodes, effective_radius)
        tn = _nearest_node(tail, page_nodes, effective_radius)
        # Second-stage loose snap: only for edges that already have one known
        # endpoint (so a standalone polyline can't be absorbed by an unrelated
        # node across the drawing). Tags the edge as "inferred" for audit.
        if (fn is None) ^ (tn is None):
            loose_radius = _effective_snap_radius(
                page_nodes, strat, mult=strat.snap_loose_equipment_mult
            )
            if fn is None:
                loose = _nearest_node(head, page_nodes, loose_radius)
                if loose is not None and (tn is None or loose.id != tn.id):
                    fn = loose
                    attributes["snap_note"] = "inferred_loose_from"
            if tn is None:
                loose = _nearest_node(tail, page_nodes, loose_radius)
                if loose is not None and (fn is None or loose.id != fn.id):
                    tn = loose
                    attributes["snap_note"] = "inferred_loose_to"
        if fn is not None:
            from_node_id = fn.id
        if tn is not None:
            to_node_id = tn.id

    # Drop edges whose endpoints could not be resolved to nodes. Persisting
    # them with empty `from_node` / `to_node` pollutes the graph and trips
    # the gt-lint referential-integrity check (bug: empty-string endpoints
    # were previously emitted instead of being recorded as conflicts).
    if not from_node_id or not to_node_id:
        conflicts.append(
            {
                "type": "dropped_edge_unsnappable",
                "page_index": page_idx,
                "line_type": grp.line_type(),
                "polyline": poly,
                "snap_radius_px": effective_radius,
                "has_from": bool(from_node_id),
                "has_to": bool(to_node_id),
                "source_annotation_ids": grp.source_ids(),
            }
        )
        return None

    lt = grp.line_type()
    return ReconciledEdge(
        id=_new_entity_id("e"),
        from_node=from_node_id,
        to_node=to_node_id,
        line_type=lt,  # type: ignore[arg-type]
        polyline_global=poly,
        cross_sheet=False,
        confidence=grp.confidence(),
        source_annotation_ids=grp.source_ids(),
        attributes=attributes,
    )


def _absorb_line_attributes(
    annotations: list[Annotation],
    attributes: dict[str, Any],
) -> None:
    """Merge line-tag attributes from grouped annotations onto the edge.

    Highest-confidence reading wins for `line_id` and the verbatim `label`;
    distinct competing `line_id` readings land in `alternate_line_ids`.
    `nominal_diameter` and `service_code` take the first non-empty value.
    """
    best_line_id: str | None = None
    best_line_id_conf: Confidence = "low"
    alternates: list[str] = []

    best_label: str | None = None
    best_label_conf: Confidence = "low"

    best_nd: str | None = None
    best_sc: str | None = None

    for a in annotations:
        attrs = a.attributes or {}
        lid = str(attrs.get("line_id", "") or "").strip()
        if lid:
            if best_line_id is None:
                best_line_id = lid
                best_line_id_conf = a.confidence
            elif _confidence_rank(a.confidence) > _confidence_rank(best_line_id_conf):
                if best_line_id != lid:
                    alternates.append(best_line_id)
                best_line_id = lid
                best_line_id_conf = a.confidence
            elif lid != best_line_id and lid not in alternates:
                alternates.append(lid)

        label = (a.label or "").strip()
        if label and (
            best_label is None
            or _confidence_rank(a.confidence) > _confidence_rank(best_label_conf)
        ):
            best_label = label
            best_label_conf = a.confidence

        nd = str(attrs.get("nominal_diameter", "") or "").strip()
        if nd and not best_nd:
            best_nd = nd
        sc = str(attrs.get("service_code", "") or "").strip()
        if sc and not best_sc:
            best_sc = sc

    if best_line_id:
        attributes["line_id"] = best_line_id
    if alternates:
        attributes["alternate_line_ids"] = alternates
    if best_label:
        attributes["label"] = best_label
    if best_nd:
        attributes["nominal_diameter"] = best_nd
    if best_sc:
        attributes["service_code"] = best_sc


def _order_line_group(
    group: _LineGroup,
    strat: ReconcileStrategy,
    conflicts: list[dict[str, Any]],
) -> list[tuple[Annotation, bool]]:
    """Chain stitched segments end-to-end so poly[0]=source, poly[-1]=target.

    Each returned tuple is (annotation, reversed); when reversed is True the
    caller should emit that annotation's endpoints in reverse order so the
    polyline flows continuously from the free-head terminus to the other end.

    Strategy: find a "free" head (no other segment's endpoint within stitch
    radius), greedy-walk the chain from there, reversing segments as needed.
    If no free head exists but a free tail does, walk from the tail and flip
    the chain so the output still reads source→target. Truly unresolvable
    groups (loops, multi-branch) are appended as-is with a conflict record.
    """
    valid = [a for a in group.annotations if len(a.endpoints) >= 2]
    if len(valid) <= 1:
        return [(a, False) for a in valid]

    radius = strat.line_stitch_radius_px

    def head(a: Annotation) -> tuple[float, float]:
        return float(a.endpoints[0].x_global), float(a.endpoints[0].y_global)

    def tail(a: Annotation) -> tuple[float, float]:
        return float(a.endpoints[-1].x_global), float(a.endpoints[-1].y_global)

    def is_free(target: Annotation, which: str) -> bool:
        pt = head(target) if which == "H" else tail(target)
        for other in valid:
            if other is target:
                continue
            if _dist(pt, head(other)) <= radius or _dist(pt, tail(other)) <= radius:
                return False
        return True

    start: Annotation | None = None
    start_from_head = True
    for a in valid:
        if is_free(a, "H"):
            start = a
            start_from_head = True
            break
    if start is None:
        for a in valid:
            if is_free(a, "T"):
                start = a
                start_from_head = False
                break
    if start is None:
        # No free endpoint — the group is a loop or has crossed-direction
        # inconsistencies. Preserve the agent's order and record a conflict.
        conflicts.append(
            {
                "type": "line_orientation_unresolved",
                "page_index": group.page_index,
                "annotation_ids": [a.id for a in valid],
            }
        )
        return [(a, False) for a in valid]

    chain: list[tuple[Annotation, bool]] = [(start, False)]
    used: set[int] = {id(start)}
    current_end = tail(start) if start_from_head else head(start)

    while len(used) < len(valid):
        best: Annotation | None = None
        best_reverse = False
        best_dist = float("inf")
        for cand in valid:
            if id(cand) in used:
                continue
            d_straight = _dist(current_end, head(cand))
            d_reversed = _dist(current_end, tail(cand))
            if d_straight <= radius and d_straight < best_dist:
                best, best_reverse, best_dist = cand, False, d_straight
            if d_reversed <= radius and d_reversed < best_dist:
                best, best_reverse, best_dist = cand, True, d_reversed
        if best is None:
            remaining = [a for a in valid if id(a) not in used]
            conflicts.append(
                {
                    "type": "line_orientation_break",
                    "page_index": group.page_index,
                    "annotation_ids": [a.id for a in remaining],
                }
            )
            for a in remaining:
                chain.append((a, False))
                used.add(id(a))
            break
        chain.append((best, best_reverse))
        used.add(id(best))
        current_end = head(best) if best_reverse else tail(best)

    if not start_from_head:
        # Walk went target→source. Reverse the chain so the polyline reads
        # source→target, and flip each segment's reversal flag accordingly.
        chain = [(a, not r) for a, r in reversed(chain)]

    return chain


def _ordered_polyline(
    ordering: list[tuple[Annotation, bool]],
) -> list[tuple[int, int]]:
    pts: list[tuple[int, int]] = []
    for a, reverse in ordering:
        eps = list(reversed(a.endpoints)) if reverse else a.endpoints
        for ep in eps:
            pts.append((int(round(ep.x_global)), int(round(ep.y_global))))
    return pts


# ---------------------------------------------------------------------------
# Cross-sheet OPC stitching (spec §5.5 item 5)
# ---------------------------------------------------------------------------


def _cross_sheet_opcs(
    nodes: list[ReconciledNode],
    conflicts: list[dict[str, Any]],
) -> tuple[list[dict[str, Any]], list[ReconciledEdge]]:
    opcs = [n for n in nodes if n.kind == "opc"]
    buckets: dict[str, list[ReconciledNode]] = defaultdict(list)
    for n in opcs:
        key = normalise_label(n.label)
        if not key:
            continue
        buckets[key].append(n)

    edges: list[ReconciledEdge] = []
    dangling: list[dict[str, Any]] = []

    for key, group in buckets.items():
        if len(group) == 1:
            dangling.append(
                {
                    "opc_label": group[0].label,
                    "normalised": key,
                    "node_id": group[0].id,
                    "page_index": group[0].page_index,
                }
            )
            continue
        if len(group) > 2:
            conflicts.append(
                {
                    "type": "ambiguous_opc",
                    "normalised": key,
                    "node_ids": [n.id for n in group],
                    "page_indices": sorted({n.page_index for n in group}),
                }
            )
            continue
        # Exactly two matches -> stitch cross-sheet edge.
        a, b = group
        edges.append(
            ReconciledEdge(
                id=_new_entity_id("x"),
                from_node=a.id,
                to_node=b.id,
                line_type=None,
                polyline_global=[],
                cross_sheet=True,
                confidence=_best_confidence([a.confidence, b.confidence]),
                source_annotation_ids=[*a.source_annotation_ids, *b.source_annotation_ids],
            )
        )

    # Also surface OPCs that had no normalisation key as dangling.
    for n in opcs:
        if not normalise_label(n.label):
            dangling.append(
                {
                    "opc_label": n.label,
                    "normalised": "",
                    "node_id": n.id,
                    "page_index": n.page_index,
                    "reason": "empty_after_normalisation",
                }
            )

    return dangling, edges
