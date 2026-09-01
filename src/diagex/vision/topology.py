"""Deterministic line topology for evidence-v2.

The model detects symbols; this module owns line geometry and connectivity.
Only connectable engineering nodes can become edge endpoints.  Text evidence,
notes, frames, and title blocks are never candidates for snapping.
"""

from __future__ import annotations

import hashlib
import heapq
import math
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from statistics import median
from typing import Any

from pydantic import BaseModel, Field

from diagex.vision.evidence import (
    PageEvidence,
    PathEvidence,
    VisualLineStyle,
    classify_pdf_dash_pattern,
    stable_evidence_id,
)
from diagex.vision.models import BBox, LineType, ReconciledEdge, ReconciledNode

_CONNECTABLE_KINDS = {"equipment", "instrument", "opc"}


class LineStyleEvidence(BaseModel):
    """Derived appearance evidence for a vector line run.

    The style says what the marks look like, not what the line means. The page
    solver combines this with the drawing legend to assign an engineering
    ``LineType``.
    """

    id: str
    page_index: int
    visual_style: VisualLineStyle
    confidence: float
    source: str
    bbox: BBox
    points: list[tuple[int, int]]
    source_path_ids: list[str] = Field(default_factory=list)
    dash_lengths: list[float] = Field(default_factory=list)
    gap_lengths: list[float] = Field(default_factory=list)


class TopologyResult(BaseModel):
    page_index: int
    edges: list[ReconciledEdge] = Field(default_factory=list)
    candidate_path_ids: list[str] = Field(default_factory=list)
    used_path_ids: list[str] = Field(default_factory=list)
    unattached_node_ids: list[str] = Field(default_factory=list)
    ambiguities: list[dict[str, Any]] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    raster_fallback_used: bool = False
    line_style_evidence: list[LineStyleEvidence] = Field(default_factory=list)


@dataclass(frozen=True)
class _Segment:
    a: tuple[float, float]
    b: tuple[float, float]
    path_id: str
    line_type: LineType
    origin: str
    visual_style: VisualLineStyle = "unknown"
    style_confidence: float = 0.0
    source_path_ids: tuple[str, ...] = ()

    @property
    def length(self) -> float:
        return math.dist(self.a, self.b)


@dataclass
class _GraphArc:
    target: int
    length: float
    path_id: str
    line_type: LineType
    visual_style: VisualLineStyle
    style_confidence: float
    source_path_ids: tuple[str, ...]


@dataclass
class _UnionFind:
    parent: list[int] = field(default_factory=list)
    rank: list[int] = field(default_factory=list)

    def add(self) -> int:
        idx = len(self.parent)
        self.parent.append(idx)
        self.rank.append(0)
        return idx

    def find(self, value: int) -> int:
        while self.parent[value] != value:
            self.parent[value] = self.parent[self.parent[value]]
            value = self.parent[value]
        return value

    def union(self, left: int, right: int) -> None:
        a = self.find(left)
        b = self.find(right)
        if a == b:
            return
        if self.rank[a] < self.rank[b]:
            a, b = b, a
        self.parent[b] = a
        if self.rank[a] == self.rank[b]:
            self.rank[a] += 1


def build_page_topology(
    *,
    page: PageEvidence,
    nodes: list[ReconciledNode],
    raster_image: Any | None = None,
) -> TopologyResult:
    paths = list(page.paths)
    warnings: list[str] = []
    raster_used = False
    native_line_count = sum(path.primitive == "line" for path in paths)
    if page.is_scanned or native_line_count < 5:
        raster_paths, raster_warning = extract_raster_paths(page=page, image=raster_image)
        if raster_paths:
            paths.extend(raster_paths)
            raster_used = True
        if raster_warning:
            warnings.append(raster_warning)

    segments, style_evidence = _candidate_segments(page, paths)
    result = TopologyResult(
        page_index=page.page_index,
        candidate_path_ids=sorted({segment.path_id for segment in segments}),
        warnings=warnings,
        raster_fallback_used=raster_used,
        line_style_evidence=style_evidence,
    )
    if not segments:
        result.warnings.append("no usable line primitives were found")
        result.unattached_node_ids = sorted(
            node.id for node in nodes if node.kind in _CONNECTABLE_KINDS
        )
        return result

    connectable = [
        node
        for node in nodes
        if node.page_index == page.page_index and node.kind in _CONNECTABLE_KINDS
    ]
    graph = _build_graph(page=page, segments=segments, nodes=connectable)

    vertex_points, adjacency, attachments, path_origins = graph
    attached_ids = {node_id for values in attachments.values() for node_id in values}
    result.unattached_node_ids = sorted(
        node.id for node in connectable if node.id not in attached_ids
    )

    node_by_id = {node.id: node for node in connectable}
    used_paths: set[str] = set()
    for vertices in _connected_components(adjacency):
        terminals: dict[str, int] = {}
        for vertex in vertices:
            for node_id in attachments.get(vertex, []):
                terminals.setdefault(node_id, vertex)
        if len(terminals) < 2:
            continue

        pair_paths: list[tuple[float, str, str, list[int], list[_GraphArc]]] = []
        terminal_items = sorted(terminals.items())
        for index, (left_id, left_vertex) in enumerate(terminal_items):
            distances, predecessors = _dijkstra(left_vertex, adjacency, vertices)
            for right_id, right_vertex in terminal_items[index + 1 :]:
                if right_vertex not in distances:
                    continue
                vertex_path, arcs = _restore_path(
                    left_vertex, right_vertex, predecessors, adjacency
                )
                if vertex_path:
                    pair_paths.append(
                        (distances[right_vertex], left_id, right_id, vertex_path, arcs)
                    )

        # More than two entities can share a pipe network through tees.  A
        # minimum spanning tree preserves reachability without fabricating the
        # all-pairs triangle that a naive component-to-edge conversion creates.
        terminal_uf = _UnionFind()
        terminal_index = {node_id: terminal_uf.add() for node_id in terminals}
        for _, left_id, right_id, vertex_path, arcs in sorted(pair_paths, key=lambda row: row[0]):
            left_root = terminal_uf.find(terminal_index[left_id])
            right_root = terminal_uf.find(terminal_index[right_id])
            if left_root == right_root:
                continue
            terminal_uf.union(left_root, right_root)
            if left_id == right_id:
                continue
            path_ids = [arc.path_id for arc in arcs]
            used_paths.update(path_ids)
            line_type = _majority_line_type(arcs)
            visual_style = _majority_visual_style(arcs)
            style_confidence = _route_style_confidence(arcs, visual_style)
            source_path_ids = sorted(
                {source_id for arc in arcs for source_id in (arc.source_path_ids or (arc.path_id,))}
            )
            style_evidence_ids = sorted(
                {arc.path_id for arc in arcs if arc.path_id.startswith("sty-")}
            )
            polyline = [
                (int(round(vertex_points[vertex][0])), int(round(vertex_points[vertex][1])))
                for vertex in vertex_path
            ]
            confidence = (
                "high"
                if all(path_origins.get(pid) == "pdf_vector" for pid in path_ids)
                else "medium"
            )
            score = 0.9 if confidence == "high" else 0.7
            edge_id = _stable_edge_id(page.page_index, left_id, right_id, polyline, line_type)
            result.edges.append(
                ReconciledEdge(
                    id=edge_id,
                    from_node=left_id,
                    to_node=right_id,
                    line_type=line_type,
                    polyline_global=polyline,
                    cross_sheet=False,
                    confidence=confidence,
                    source_evidence_ids=source_path_ids,
                    system_confidence=score,
                    system_confidence_level=confidence,
                    attributes={
                        "topology_source": "deterministic_vector"
                        if confidence == "high"
                        else "deterministic_raster",
                        "endpoint_labels": [
                            node_by_id[left_id].label,
                            node_by_id[right_id].label,
                        ],
                        "visual_style": visual_style,
                        "visual_style_confidence": round(style_confidence, 3),
                        "style_evidence_ids": style_evidence_ids,
                    },
                )
            )

    result.used_path_ids = sorted(used_paths)
    used_segments = [segment for segment in segments if segment.path_id in used_paths]
    result.ambiguities.extend(_crossing_candidates(page, used_segments, nodes=connectable))
    return result


def _candidate_segments(
    page: PageEvidence,
    paths: list[PathEvidence],
) -> tuple[list[_Segment], list[LineStyleEvidence]]:
    minimum = max(8.0, min(page.width, page.height) * 0.0015)
    border_margin = max(8, int(min(page.width, page.height) * 0.004))
    derived_paths, style_evidence, consumed_path_ids = _infer_fragmented_vector_styles(
        page,
        paths,
    )
    out: list[_Segment] = []
    for path in [*paths, *derived_paths]:
        if path.id in consumed_path_ids:
            continue
        if path.closed or path.primitive in {"rect", "quad"}:
            continue
        if path.primitive not in {"line", "curve", "raster_line"}:
            continue
        for first, second in zip(path.points, path.points[1:], strict=False):
            segment = _Segment(
                a=(float(first[0]), float(first[1])),
                b=(float(second[0]), float(second[1])),
                path_id=path.id,
                line_type=_line_type_for_path(path),
                origin=path.origin,
                visual_style=_path_visual_style(path),
                style_confidence=_path_style_confidence(path),
                source_path_ids=tuple(path.source_path_ids or [path.id]),
            )
            if segment.length < minimum:
                continue
            if _is_page_frame(segment, page, border_margin):
                continue
            out.append(segment)
    return out, style_evidence


def _line_type_for_path(path: PathEvidence) -> LineType:
    # Appearance is not semantics. Keep styled vector routes neutral until the
    # page solver maps them through the document's legend.
    if _path_visual_style(path) in {"dashed", "dotted", "dash_dot"}:
        return "other"
    return "process"


def _path_visual_style(path: PathEvidence) -> VisualLineStyle:
    if path.visual_style != "unknown":
        return path.visual_style
    if path.origin == "pdf_vector":
        style, _, _ = classify_pdf_dash_pattern(
            path.dashes,
            stroke_width=path.stroke_width,
        )
        return style
    return "unknown"


def _path_style_confidence(path: PathEvidence) -> float:
    if path.style_confidence is not None:
        return float(path.style_confidence)
    if path.origin == "pdf_vector":
        _, confidence, _ = classify_pdf_dash_pattern(
            path.dashes,
            stroke_width=path.stroke_width,
        )
        return confidence
    return 0.0


@dataclass(frozen=True)
class _AxisFragment:
    path: PathEvidence
    orientation: str
    coordinate: float
    start: float
    end: float

    @property
    def length(self) -> float:
        return self.end - self.start


def _infer_fragmented_vector_styles(
    page: PageEvidence,
    paths: list[PathEvidence],
) -> tuple[list[PathEvidence], list[LineStyleEvidence], set[str]]:
    """Recover visible dashed runs exported as separate solid PDF strokes.

    The first implementation is intentionally conservative and limited to the
    horizontal/vertical runs used by the great majority of P&IDs. A run must
    contain at least three non-touching collinear marks with regular gaps.
    Ordinary broken pipes, text strokes, and symbol outlines therefore remain
    as their original source primitives instead of being guessed as signals.
    """
    axis_tolerance = max(1.5, min(page.width, page.height) * 0.00045)
    max_gap = max(24.0, min(page.width, page.height) * 0.012)
    groups: dict[tuple[Any, ...], list[_AxisFragment]] = defaultdict(list)

    for path in paths:
        if (
            path.origin != "pdf_vector"
            or path.primitive != "line"
            or path.closed
            or len(path.points) != 2
            or _path_visual_style(path) != "solid"
        ):
            continue
        (x1, y1), (x2, y2) = path.points
        if abs(y2 - y1) <= axis_tolerance:
            orientation = "h"
            coordinate = (y1 + y2) / 2.0
            start, end = sorted((float(x1), float(x2)))
        elif abs(x2 - x1) <= axis_tolerance:
            orientation = "v"
            coordinate = (x1 + x2) / 2.0
            start, end = sorted((float(y1), float(y2)))
        else:
            continue
        if end - start < max(4.0, path.stroke_width * 2.0):
            continue
        color_key = tuple(round(float(value), 2) for value in (path.stroke_color or []))
        key = (
            orientation,
            round(coordinate / axis_tolerance),
            round(path.stroke_width * 2.0) / 2.0,
            color_key,
        )
        groups[key].append(
            _AxisFragment(
                path=path,
                orientation=orientation,
                coordinate=coordinate,
                start=start,
                end=end,
            )
        )

    derived: list[PathEvidence] = []
    evidence: list[LineStyleEvidence] = []
    consumed: set[str] = set()
    for fragments in groups.values():
        unique = _deduplicate_fragments(fragments, tolerance=axis_tolerance)
        if len(unique) < 3:
            continue
        run: list[_AxisFragment] = []
        for fragment in unique:
            if not run:
                run = [fragment]
                continue
            minimum_gap = max(
                2.5,
                1.35 * median([item.path.stroke_width for item in run]),
            )
            gap = fragment.start - run[-1].end
            if minimum_gap <= gap <= max_gap:
                run.append(fragment)
            else:
                _append_fragment_run(page, run, derived, evidence, consumed)
                run = [fragment]
        _append_fragment_run(page, run, derived, evidence, consumed)
    return derived, evidence, consumed


def _deduplicate_fragments(
    fragments: list[_AxisFragment],
    *,
    tolerance: float,
) -> list[_AxisFragment]:
    unique: list[_AxisFragment] = []
    for fragment in sorted(fragments, key=lambda value: (value.start, value.end, value.path.id)):
        duplicate = next(
            (
                prior
                for prior in reversed(unique[-4:])
                if abs(fragment.start - prior.start) <= tolerance
                and abs(fragment.end - prior.end) <= tolerance
            ),
            None,
        )
        if duplicate is None:
            unique.append(fragment)
    return unique


def _append_fragment_run(
    page: PageEvidence,
    run: list[_AxisFragment],
    derived: list[PathEvidence],
    evidence: list[LineStyleEvidence],
    consumed: set[str],
) -> None:
    if len(run) < 3:
        return
    dash_lengths = [item.length for item in run]
    gap_lengths = [right.start - left.end for left, right in zip(run, run[1:], strict=False)]
    span = run[-1].end - run[0].start
    minimum_span = max(80.0, min(page.width, page.height) * 0.018)
    if span < minimum_span or not gap_lengths:
        return
    gap_mean = sum(gap_lengths) / len(gap_lengths)
    gap_variance = sum((value - gap_mean) ** 2 for value in gap_lengths) / len(gap_lengths)
    gap_cv = math.sqrt(gap_variance) / gap_mean if gap_mean else float("inf")
    gap_ratio = sum(gap_lengths) / span if span else 0.0
    ink_median = median(dash_lengths)
    stroke_width = median([item.path.stroke_width for item in run])
    if gap_cv > 0.52 or not 0.08 <= gap_ratio <= 0.72 or ink_median < max(5.0, stroke_width * 2.5):
        return

    short = min(dash_lengths)
    long_marks = [value for value in dash_lengths if value >= max(short * 2.6, short + 12.0)]
    short_marks = [value for value in dash_lengths if value <= short * 1.55]
    if len(long_marks) >= 2 and len(short_marks) >= 2:
        style: VisualLineStyle = "dash_dot"
    elif ink_median <= max(8.0, stroke_width * 4.0):
        style = "dotted"
    else:
        style = "dashed"

    coordinate = median([item.coordinate for item in run])
    if run[0].orientation == "h":
        points = [
            (int(round(run[0].start)), int(round(coordinate))),
            (int(round(run[-1].end)), int(round(coordinate))),
        ]
    else:
        points = [
            (int(round(coordinate)), int(round(run[0].start))),
            (int(round(coordinate)), int(round(run[-1].end))),
        ]
    source_ids = [item.path.id for item in run]
    evidence_id = stable_evidence_id(
        "sty",
        page.page_index,
        style,
        points,
        source_ids,
    )
    confidence = max(
        0.65,
        min(0.98, 0.77 + min(0.14, (len(run) - 3) * 0.025) - min(0.12, gap_cv * 0.12)),
    )
    xs = [point[0] for point in points]
    ys = [point[1] for point in points]
    bbox = BBox(
        x=min(xs),
        y=min(ys),
        w=max(1, max(xs) - min(xs)),
        h=max(1, max(ys) - min(ys)),
    )
    color = run[0].path.stroke_color
    derived.append(
        PathEvidence(
            id=evidence_id,
            page_index=page.page_index,
            points=points,
            bbox=bbox,
            origin="pdf_vector",
            primitive="line",
            stroke_width=stroke_width,
            stroke_color=color,
            dashes="inferred_fragment_pattern",
            visual_style=style,
            style_confidence=confidence,
            style_source="vector_fragment_pattern",
            source_path_ids=source_ids,
        )
    )
    evidence.append(
        LineStyleEvidence(
            id=evidence_id,
            page_index=page.page_index,
            visual_style=style,
            confidence=confidence,
            source="vector_fragment_pattern",
            bbox=bbox,
            points=points,
            source_path_ids=source_ids,
            dash_lengths=[round(value, 3) for value in dash_lengths],
            gap_lengths=[round(value, 3) for value in gap_lengths],
        )
    )
    consumed.update(source_ids)


def _is_page_frame(segment: _Segment, page: PageEvidence, margin: int) -> bool:
    horizontal = abs(segment.a[1] - segment.b[1]) <= 1.5
    vertical = abs(segment.a[0] - segment.b[0]) <= 1.5
    if horizontal and segment.length > page.width * 0.65:
        return (
            min(segment.a[1], segment.b[1]) <= margin
            or max(segment.a[1], segment.b[1]) >= page.height - margin
        )
    if vertical and segment.length > page.height * 0.65:
        return (
            min(segment.a[0], segment.b[0]) <= margin
            or max(segment.a[0], segment.b[0]) >= page.width - margin
        )
    return False


def _build_graph(
    *,
    page: PageEvidence,
    segments: list[_Segment],
    nodes: list[ReconciledNode],
) -> tuple[
    dict[int, tuple[float, float]],
    dict[int, list[_GraphArc]],
    dict[int, list[str]],
    dict[str, str],
]:
    joint_radius = max(3.0, min(page.width, page.height) * 0.0008)
    attach_radius = max(12.0, min(page.width, page.height) * 0.004)
    split_marks: list[list[float]] = [[0.0, 1.0] for _ in segments]

    endpoint_grid: dict[tuple[int, int], list[tuple[int, float, tuple[float, float]]]] = (
        defaultdict(list)
    )
    cell = max(joint_radius * 2.0, 6.0)
    for index, segment in enumerate(segments):
        for t, point in ((0.0, segment.a), (1.0, segment.b)):
            endpoint_grid[_grid_key(point, cell)].append((index, t, point))

    # Split a line where another line terminates on its interior (tees).
    for index, segment in enumerate(segments):
        min_x = min(segment.a[0], segment.b[0]) - joint_radius
        max_x = max(segment.a[0], segment.b[0]) + joint_radius
        min_y = min(segment.a[1], segment.b[1]) - joint_radius
        max_y = max(segment.a[1], segment.b[1]) + joint_radius
        for key in _grid_keys_for_bbox(min_x, min_y, max_x, max_y, cell):
            for other_index, _, point in endpoint_grid.get(key, []):
                if other_index == index:
                    continue
                t, distance = _project_point_to_segment(point, segment)
                if joint_radius >= distance and 1e-4 < t < 1 - 1e-4:
                    split_marks[index].append(t)

    node_marks: dict[str, list[tuple[int, float]]] = {}
    for node in nodes:
        candidates: list[tuple[float, float, float, int, float]] = []
        center = (
            node.bbox_global.x + node.bbox_global.w / 2,
            node.bbox_global.y + node.bbox_global.h / 2,
        )
        for index, segment in enumerate(segments):
            t, _ = _project_point_to_segment(center, segment)
            projected = _point_at(segment, t)
            distance = _distance_point_to_bbox(projected, node.bbox_global)
            if distance > attach_radius:
                continue
            if not _segment_reaches_outside_bbox(
                segment, node.bbox_global, padding=max(2.0, joint_radius)
            ):
                continue
            center_distance = math.dist(projected, center)
            # Prefer long strokes among equally close candidates.  Short
            # internal symbol strokes often sit inside an instrument/equipment
            # bbox but are not a pipe or signal entering the object.
            candidates.append((distance, -min(segment.length, 2000.0), center_distance, index, t))

        selected: list[tuple[int, float]] = []
        selected_points: list[tuple[float, float]] = []
        for _, _, _, segment_index, t in sorted(candidates):
            point = _point_at(segments[segment_index], t)
            if any(math.dist(point, prior) <= joint_radius * 2 for prior in selected_points):
                continue
            selected.append((segment_index, t))
            selected_points.append(point)
            split_marks[segment_index].append(t)
            if len(selected) >= 8:
                break
        if selected:
            node_marks[node.id] = selected

    raw_points: list[tuple[float, float]] = []
    raw_arcs: list[tuple[int, int, _Segment]] = []
    mark_point_index: dict[tuple[int, int], int] = {}
    for segment_index, segment in enumerate(segments):
        values = sorted(set(round(max(0.0, min(1.0, t)), 6) for t in split_marks[segment_index]))
        indexes: list[int] = []
        for t in values:
            idx = len(raw_points)
            raw_points.append(_point_at(segment, t))
            indexes.append(idx)
            mark_point_index[(segment_index, int(round(t * 1_000_000)))] = idx
        for left, right in zip(indexes, indexes[1:], strict=False):
            if math.dist(raw_points[left], raw_points[right]) > 0.5:
                raw_arcs.append((left, right, segment))

    uf = _cluster_points(raw_points, joint_radius)
    members: dict[int, list[int]] = defaultdict(list)
    for index in range(len(raw_points)):
        members[uf.find(index)].append(index)
    root_to_vertex = {root: index for index, root in enumerate(sorted(members))}
    vertex_points = {
        root_to_vertex[root]: (
            sum(raw_points[index][0] for index in values) / len(values),
            sum(raw_points[index][1] for index in values) / len(values),
        )
        for root, values in members.items()
    }
    raw_to_vertex = {index: root_to_vertex[uf.find(index)] for index in range(len(raw_points))}

    adjacency: dict[int, list[_GraphArc]] = defaultdict(list)
    path_origins: dict[str, str] = {}
    for left, right, segment in raw_arcs:
        a = raw_to_vertex[left]
        b = raw_to_vertex[right]
        if a == b:
            continue
        length = math.dist(vertex_points[a], vertex_points[b])
        arc_values = (
            length,
            segment.path_id,
            segment.line_type,
            segment.visual_style,
            segment.style_confidence,
            segment.source_path_ids,
        )
        adjacency[a].append(_GraphArc(b, *arc_values))
        adjacency[b].append(_GraphArc(a, *arc_values))
        path_origins[segment.path_id] = segment.origin

    attachments: dict[int, list[str]] = defaultdict(list)
    for node_id, marks in node_marks.items():
        for segment_index, t in marks:
            raw_index = mark_point_index.get((segment_index, int(round(round(t, 6) * 1_000_000))))
            if raw_index is not None:
                attachments[raw_to_vertex[raw_index]].append(node_id)

    return vertex_points, adjacency, attachments, path_origins


def _cluster_points(points: list[tuple[float, float]], radius: float) -> _UnionFind:
    uf = _UnionFind()
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    cell = max(radius, 1.0)
    for index, point in enumerate(points):
        uf.add()
        key = _grid_key(point, cell)
        for x in range(key[0] - 1, key[0] + 2):
            for y in range(key[1] - 1, key[1] + 2):
                for other in grid.get((x, y), []):
                    if math.dist(point, points[other]) <= radius:
                        uf.union(index, other)
        grid[key].append(index)
    return uf


def _grid_key(point: tuple[float, float], cell: float) -> tuple[int, int]:
    return int(math.floor(point[0] / cell)), int(math.floor(point[1] / cell))


def _grid_keys_for_bbox(
    x0: float, y0: float, x1: float, y1: float, cell: float
) -> list[tuple[int, int]]:
    left = int(math.floor(x0 / cell))
    right = int(math.floor(x1 / cell))
    top = int(math.floor(y0 / cell))
    bottom = int(math.floor(y1 / cell))
    return [(x, y) for x in range(left, right + 1) for y in range(top, bottom + 1)]


def _point_at(segment: _Segment, t: float) -> tuple[float, float]:
    return (
        segment.a[0] + (segment.b[0] - segment.a[0]) * t,
        segment.a[1] + (segment.b[1] - segment.a[1]) * t,
    )


def _project_point_to_segment(point: tuple[float, float], segment: _Segment) -> tuple[float, float]:
    dx = segment.b[0] - segment.a[0]
    dy = segment.b[1] - segment.a[1]
    denom = dx * dx + dy * dy
    if denom <= 1e-12:
        return 0.0, math.dist(point, segment.a)
    t = ((point[0] - segment.a[0]) * dx + (point[1] - segment.a[1]) * dy) / denom
    t = max(0.0, min(1.0, t))
    return t, math.dist(point, _point_at(segment, t))


def _distance_point_to_bbox(point: tuple[float, float], bbox: BBox) -> float:
    dx = max(bbox.x - point[0], 0.0, point[0] - bbox.x2)
    dy = max(bbox.y - point[1], 0.0, point[1] - bbox.y2)
    return math.hypot(dx, dy)


def _segment_reaches_outside_bbox(segment: _Segment, bbox: BBox, *, padding: float) -> bool:
    x0 = bbox.x - padding
    y0 = bbox.y - padding
    x1 = bbox.x2 + padding
    y1 = bbox.y2 + padding

    def outside(point: tuple[float, float]) -> bool:
        return point[0] < x0 or point[0] > x1 or point[1] < y0 or point[1] > y1

    return outside(segment.a) or outside(segment.b)


def _connected_components(adjacency: dict[int, list[_GraphArc]]) -> list[set[int]]:
    remaining = set(adjacency)
    out: list[set[int]] = []
    while remaining:
        start = min(remaining)
        stack = [start]
        component: set[int] = set()
        while stack:
            value = stack.pop()
            if value in component:
                continue
            component.add(value)
            stack.extend(arc.target for arc in adjacency.get(value, []))
        remaining.difference_update(component)
        out.append(component)
    return out


def _dijkstra(
    source: int,
    adjacency: dict[int, list[_GraphArc]],
    allowed: set[int],
) -> tuple[dict[int, float], dict[int, tuple[int, _GraphArc]]]:
    distances = {source: 0.0}
    previous: dict[int, tuple[int, _GraphArc]] = {}
    queue = [(0.0, source)]
    while queue:
        distance, vertex = heapq.heappop(queue)
        if distance != distances.get(vertex):
            continue
        for arc in adjacency.get(vertex, []):
            if arc.target not in allowed:
                continue
            candidate = distance + arc.length
            if candidate < distances.get(arc.target, float("inf")):
                distances[arc.target] = candidate
                previous[arc.target] = (vertex, arc)
                heapq.heappush(queue, (candidate, arc.target))
    return distances, previous


def _restore_path(
    source: int,
    target: int,
    previous: dict[int, tuple[int, _GraphArc]],
    adjacency: dict[int, list[_GraphArc]],
) -> tuple[list[int], list[_GraphArc]]:
    _ = adjacency
    vertices = [target]
    arcs: list[_GraphArc] = []
    current = target
    while current != source:
        row = previous.get(current)
        if row is None:
            return [], []
        parent, arc = row
        vertices.append(parent)
        arcs.append(arc)
        current = parent
    vertices.reverse()
    arcs.reverse()
    return vertices, arcs


def _majority_line_type(arcs: list[_GraphArc]) -> LineType:
    counts: Counter[str] = Counter()
    for arc in arcs:
        counts[arc.line_type] += max(1, int(round(arc.length)))
    return counts.most_common(1)[0][0] if counts else "process"  # type: ignore[return-value]


def _majority_visual_style(arcs: list[_GraphArc]) -> VisualLineStyle:
    counts: Counter[str] = Counter()
    for arc in arcs:
        counts[arc.visual_style] += max(1, int(round(arc.length)))
    return counts.most_common(1)[0][0] if counts else "unknown"  # type: ignore[return-value]


def _route_style_confidence(
    arcs: list[_GraphArc],
    visual_style: VisualLineStyle,
) -> float:
    weighted = [
        (max(1.0, arc.length), arc.style_confidence)
        for arc in arcs
        if arc.visual_style == visual_style and arc.style_confidence > 0
    ]
    if not weighted:
        return 0.0
    total = sum(weight for weight, _ in weighted)
    return sum(weight * confidence for weight, confidence in weighted) / total


def _stable_edge_id(
    page_index: int,
    left_id: str,
    right_id: str,
    polyline: list[tuple[int, int]],
    line_type: str,
) -> str:
    endpoints = sorted((left_id, right_id))
    payload = repr((page_index, endpoints, polyline, line_type)).encode("utf-8")
    return "e-" + hashlib.sha256(payload).hexdigest()[:16]


def _crossing_candidates(
    page: PageEvidence,
    segments: list[_Segment],
    *,
    nodes: list[ReconciledNode],
) -> list[dict[str, Any]]:
    """Return only source-supported crossings that can affect graph topology.

    Raw PDF paths contain text strokes, symbol internals, borders, and drawing
    tables.  Crossing every candidate path produced thousands of false human
    review tasks.  Callers now pass only paths actually used by an extracted
    network; this function additionally excludes symbol interiors, tiny
    strokes, same-path intersections, and spatial duplicates.
    """
    out: list[dict[str, Any]] = []
    cell = max(80.0, min(page.width, page.height) * 0.02)
    minimum_length = max(20.0, min(page.width, page.height) * 0.005)
    dedupe_radius = max(10.0, min(page.width, page.height) * 0.003)
    symbol_padding = max(8.0, min(page.width, page.height) * 0.002)
    grid: dict[tuple[int, int], list[int]] = defaultdict(list)
    checked: set[tuple[int, int]] = set()
    accepted_points: list[tuple[float, float]] = []
    for index, segment in enumerate(segments):
        if segment.length < minimum_length:
            continue
        keys = _grid_keys_for_bbox(
            min(segment.a[0], segment.b[0]),
            min(segment.a[1], segment.b[1]),
            max(segment.a[0], segment.b[0]),
            max(segment.a[1], segment.b[1]),
            cell,
        )
        for key in keys:
            for other_index in grid.get(key, []):
                pair = (min(index, other_index), max(index, other_index))
                if pair in checked:
                    continue
                checked.add(pair)
                other = segments[other_index]
                if other.length < minimum_length or other.path_id == segment.path_id:
                    continue
                point = _proper_intersection(segment, other)
                if point is None:
                    continue
                if any(
                    _point_inside_bbox(point, node.bbox_global, padding=symbol_padding)
                    for node in nodes
                ):
                    continue
                if any(math.dist(point, prior) <= dedupe_radius for prior in accepted_points):
                    continue
                accepted_points.append(point)
                out.append(
                    {
                        "type": "crossing_or_junction",
                        "page_index": page.page_index,
                        "x": int(round(point[0])),
                        "y": int(round(point[1])),
                        "path_ids": [segment.path_id, other.path_id],
                        "status": "unresolved",
                    }
                )
                if len(out) >= 100:
                    return out
            grid[key].append(index)
    return out


def _point_inside_bbox(point: tuple[float, float], bbox: BBox, *, padding: float) -> bool:
    return (
        bbox.x - padding <= point[0] <= bbox.x2 + padding
        and bbox.y - padding <= point[1] <= bbox.y2 + padding
    )


def _proper_intersection(left: _Segment, right: _Segment) -> tuple[float, float] | None:
    x1, y1 = left.a
    x2, y2 = left.b
    x3, y3 = right.a
    x4, y4 = right.b
    denominator = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denominator) < 1e-9:
        return None
    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denominator
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denominator
    if not (0.03 < t < 0.97 and 0.03 < u < 0.97):
        return None
    return x1 + t * (x2 - x1), y1 + t * (y2 - y1)


def extract_raster_paths(
    *, page: PageEvidence, image: Any | None
) -> tuple[list[PathEvidence], str | None]:
    if image is None:
        return [], "raster fallback requested but no rendered page image is available"
    try:
        import cv2  # type: ignore[import-not-found]
        import numpy as np
    except ImportError:
        return [], (
            "raster line extraction skipped; install the optional 'vision' extra "
            "for opencv-python-headless"
        )

    array = np.asarray(image.convert("L"))
    inverted = cv2.bitwise_not(array)
    _, binary = cv2.threshold(inverted, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    minimum = max(20, int(min(page.width, page.height) * 0.015))
    lines = cv2.HoughLinesP(
        binary,
        rho=1,
        theta=math.pi / 180,
        threshold=max(25, minimum // 2),
        minLineLength=minimum,
        maxLineGap=max(6, minimum // 4),
    )
    if lines is None:
        return [], "OpenCV raster fallback found no candidate lines"

    out: list[PathEvidence] = []
    for index, raw in enumerate(lines[:5000]):
        x1, y1, x2, y2 = (int(value) for value in raw[0])
        points = [(x1, y1), (x2, y2)]
        bbox = BBox(
            x=min(x1, x2),
            y=min(y1, y2),
            w=max(1, abs(x2 - x1)),
            h=max(1, abs(y2 - y1)),
        )
        out.append(
            PathEvidence(
                id=stable_evidence_id("ras", page.page_index, index, points),
                page_index=page.page_index,
                points=points,
                bbox=bbox,
                origin="raster_cv",
                primitive="raster_line",
                stroke_width=1.0,
            )
        )
    return out, None
