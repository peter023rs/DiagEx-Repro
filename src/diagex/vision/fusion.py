"""Evidence fusion, stable IDs, OPC matching, and confidence for evidence-v2."""

from __future__ import annotations

import hashlib
import math
import re
import statistics
from collections import Counter
from dataclasses import dataclass, field
from functools import cache
from typing import Any

from pydantic import BaseModel, Field

from diagex.dexpi_schema import (
    EQUIPMENT_CLASS_KEYS,
    INSTRUMENT_CLASS_KEYS,
    INSTRUMENT_FUNCTION_KEYS,
    VALVE_TYPE_KEYS,
)
from diagex.vision.evidence import PageEvidence, TextEvidence
from diagex.vision.legend_models import LegendPack
from diagex.vision.models import (
    BBox,
    Confidence,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)
from diagex.vision.native_text import infer_tag_semantics
from diagex.vision.page_graph import PageGraphResult
from diagex.vision.perception import DetectionRecord
from diagex.vision.reconcile import normalise_label
from diagex.vision.topology import TopologyResult

_CONF_RANK: dict[str, int] = {"low": 0, "medium": 1, "high": 2}
_TAG_RE = re.compile(r"(?:[A-Z]{1,5}[- ]?\d{2,6}[A-Z]?|DN\s*\d+)", re.IGNORECASE)
_OPC_HINT_RE = re.compile(
    r"(?:off[- ]?page|continuation|to\s+sheet|from\s+sheet|\bDW\d{2}[- ]?\d{3,5}\b|去往|来自|接续)",
    re.IGNORECASE,
)
_EXPLICIT_OPC_REF_RE = re.compile(r"\bDW\d{2}[- ]?\d{3,5}\b", re.IGNORECASE)
_NON_CONNECTABLE_TEXT_RE = re.compile(
    r"^(?:"
    r"DN\s*\d+(?:\s*[x×/]\s*\d+)?|"
    r"\d+(?:\.\d+)?\s*(?:[\"”′]|mm|cm)|"
    r"(?:CSO|CSC|LO|LC)|"
    r"\d{1,4}[- ](?:GA|CWS|CWR|IA|PA|N2?|VT|DW|FG|FO|NG)[- ][A-Z0-9-]+"
    r")$",
    re.IGNORECASE,
)
_EQUIPMENT_ALIASES = {
    "exchanger": "heat_exchanger",
    "heat_exchanger_unit": "heat_exchanger",
    "drier": "dryer",
    "blower": "fan_blower",
    "fan": "fan_blower",
    "tower": "column",
    "drum": "vessel",
    "receiver": "vessel",
    "equipment": "unclassified_equipment",
}
_VALVE_ALIASES = {
    "gate_valve": "gate",
    "globe_valve": "globe",
    "check_valve": "check",
    "check_or_non_return": "check",
    "non_return": "check",
    "ball_valve": "ball",
    "butterfly_valve": "butterfly",
    "control_valve": "control",
    "regulating_valve": "control",
    "pressure_regulating_valve": "control",
    "safety_valve": "safety_relief",
    "relief_valve": "safety_relief",
    "psv": "safety_relief",
    "three_way_valve": "three_way",
    "needle_valve": "needle",
    "plug_valve": "plug",
    "manual": "other",
    "manual_valve": "other",
    "isolation": "other",
    "isolation_valve": "other",
    "general": "other",
    "general_valve": "other",
    "block": "other",
    "block_valve": "other",
    "drain": "other",
    "inlet": "other",
    "outlet": "other",
    "unknown": "other",
    "quick_acting": "other",
    "shutdown": "other",
    "fail_open": "other",
    "fail_closed": "other",
}


class FusionResult(BaseModel):
    graph: ReconciledGraph
    ambiguities: list[dict[str, Any]] = Field(default_factory=list)
    native_text_assignment_count: int = 0


@dataclass
class _Cluster:
    detections: list[DetectionRecord] = field(default_factory=list)


def fuse_objects(
    *,
    source_name: str,
    pages: list[PageEvidence],
    detections: list[DetectionRecord],
    per_page_status: dict[int, str],
    legend_pack: LegendPack | None = None,
) -> FusionResult:
    """Fuse overlapping object detections once, without constructing edges."""
    pages_by_index = {page.page_index: page for page in pages}
    accepted, rejected = _prepare_detections(
        detections, pages_by_index, legend_pack=legend_pack
    )
    clusters = _cluster_detections(accepted, pages_by_index)
    nodes: list[ReconciledNode] = []
    ambiguities: list[dict[str, Any]] = list(rejected)
    assigned_native_text = 0

    for cluster in clusters:
        node, node_ambiguities, assigned_count = _node_from_cluster(cluster, pages_by_index)
        nodes.append(node)
        ambiguities.extend(node_ambiguities)
        assigned_native_text += assigned_count

    graph = ReconciledGraph(
        schema_version="0.3.0",
        source_path=source_name,
        nodes=sorted(
            nodes,
            key=lambda node: (node.page_index, node.bbox_global.y, node.bbox_global.x, node.id),
        ),
        conflicts=ambiguities,
        per_page_status={
            int(page): _coerce_page_status(status) for page, status in per_page_status.items()
        },
    )
    return FusionResult(
        graph=graph,
        ambiguities=ambiguities,
        native_text_assignment_count=assigned_native_text,
    )


def assemble_graph(
    *,
    objects: FusionResult,
    pages: list[PageEvidence],
    topology: list[TopologyResult],
    page_graph_results: list[PageGraphResult],
    per_page_status: dict[int, str],
) -> FusionResult:
    """Assemble validated page decisions and deterministic cross-sheet matches."""
    pages_by_index = {page.page_index: page for page in pages}
    nodes = [node.model_copy(deep=True) for node in objects.graph.nodes]
    ambiguities = [dict(value) for value in objects.ambiguities]
    node_ids = {node.id for node in nodes}
    results_by_page = {result.page_index: result for result in page_graph_results}
    graph_edges: list[ReconciledEdge] = []

    for result in page_graph_results:
        ambiguities.extend(result.conflicts)
        ambiguities.extend(
            {
                "type": "rejected_page_graph_output",
                "page_index": result.page_index,
                "status": "resolved",
                "reason": detail,
            }
            for detail in result.diagnostics
        )
        for node in nodes:
            update = result.opc_updates.get(node.id)
            if update:
                node.attributes.update(update)

    for result in topology:
        ambiguities.extend(result.ambiguities)
        page_result = results_by_page.get(result.page_index)
        selected_edges = page_result.edges if page_result is not None else []
        if page_result is None:
            node_by_id = {node.id: node for node in nodes}
            for edge in result.edges:
                endpoints = (node_by_id.get(edge.from_node), node_by_id.get(edge.to_node))
                if all(node is not None and node.kind == "equipment" for node in endpoints):
                    selected_edges.append(edge)
                else:
                    ambiguities.append(
                        {
                            "type": "page_graph_missing",
                            "page_index": result.page_index,
                            "edge_id": edge.id,
                            "status": "unresolved",
                            "reason": "instrument/OPC topology requires a completed page-graph solve",
                        }
                    )
        for edge in selected_edges:
            if edge.from_node == edge.to_node:
                ambiguities.append(
                    {
                        "type": "rejected_self_loop",
                        "page_index": result.page_index,
                        "edge_id": edge.id,
                    }
                )
                continue
            if edge.from_node not in node_ids or edge.to_node not in node_ids:
                ambiguities.append(
                    {
                        "type": "rejected_dangling_edge",
                        "page_index": result.page_index,
                        "edge_id": edge.id,
                    }
                )
                continue
            graph_edges.append(edge)

    graph_edges = _deduplicate_edges(graph_edges)
    cross_edges, dangling_opcs, opc_ambiguities = _match_opcs(nodes, pages_by_index=pages_by_index)
    page_matched_opcs = {
        endpoint
        for edge in graph_edges
        if edge.cross_sheet
        for endpoint in (edge.from_node, edge.to_node)
    }
    if page_matched_opcs:
        dangling_opcs = [
            item for item in dangling_opcs if item.get("node_id") not in page_matched_opcs
        ]
        opc_ambiguities = [
            item
            for item in opc_ambiguities
            if not set(item.get("node_ids") or []).issubset(page_matched_opcs)
        ]
    ambiguities.extend(opc_ambiguities)
    edges = _deduplicate_edges([*graph_edges, *cross_edges])

    attached_nodes = {endpoint for edge in edges for endpoint in (edge.from_node, edge.to_node)}
    for node in nodes:
        if node.id in attached_nodes:
            score = min(1.0, float(node.system_confidence or 0.0) + 0.08)
            node.system_confidence = round(score, 3)
            node.system_confidence_level = _confidence_level(score)

    graph = ReconciledGraph(
        schema_version="0.3.0",
        source_path=objects.graph.source_path,
        nodes=sorted(
            nodes,
            key=lambda node: (node.page_index, node.bbox_global.y, node.bbox_global.x, node.id),
        ),
        edges=sorted(edges, key=lambda edge: edge.id),
        dangling_opcs=dangling_opcs,
        conflicts=ambiguities,
        per_page_status={
            int(page): _coerce_page_status(status) for page, status in per_page_status.items()
        },
    )
    return FusionResult(
        graph=graph,
        ambiguities=ambiguities,
        native_text_assignment_count=objects.native_text_assignment_count,
    )


def _prepare_detections(
    detections: list[DetectionRecord],
    pages_by_index: dict[int, PageEvidence],
    *,
    legend_pack: LegendPack | None = None,
) -> tuple[list[DetectionRecord], list[dict[str, Any]]]:
    accepted: list[DetectionRecord] = []
    rejected: list[dict[str, Any]] = []
    for detection in detections:
        item = detection.model_copy(deep=True)
        page = pages_by_index.get(item.page_index)
        if page is None:
            rejected.append(
                {
                    "type": "rejected_unknown_page_geometry",
                    "page_index": item.page_index,
                    "detection_id": item.id,
                    "status": "resolved",
                }
            )
            continue
        if (
            item.bbox.x < 0
            or item.bbox.y < 0
            or item.bbox.w <= 0
            or item.bbox.h <= 0
            or item.bbox.x2 > page.width
            or item.bbox.y2 > page.height
        ):
            rejected.append(
                {
                    "type": "rejected_out_of_page_geometry",
                    "page_index": item.page_index,
                    "detection_id": item.id,
                    "bbox": item.bbox.model_dump(),
                    "status": "resolved",
                }
            )
            continue
        retyped = _deterministic_tag_normalise(item, legend_pack=legend_pack)
        if retyped:
            rejected.append(retyped)
        if item.kind == "equipment" and _is_native_text_only_detection(item, page):
            rejected.append(
                {
                    "type": "rejected_non_connectable_text",
                    "page_index": item.page_index,
                    "detection_id": item.id,
                    "label": item.label,
                    "bbox": item.bbox.model_dump(),
                    "status": "resolved",
                    "reason": (
                        "printed value and text-like geometry identify a line, "
                        "dimension, or valve-state annotation rather than an engineering object"
                    ),
                }
            )
            continue
        item.attributes = _normalise_taxonomy(item.attributes, kind=item.kind)
        if item.kind == "opc" and not _opc_has_boundary_support(item, page):
            if _opc_has_explicit_reference(item):
                item.attributes["opc_context_required"] = True
                item.attributes["continuation_evidence"] = "explicit_drawing_reference"
            else:
                rejected.append(
                    {
                        "type": "rejected_opc_without_boundary_evidence",
                        "page_index": item.page_index,
                        "detection_id": item.id,
                        "label": item.label,
                        "bbox": item.bbox.model_dump(),
                        "status": "resolved",
                        "reason": "OPC lacked both drawing-boundary support and an explicit continuation reference",
                    }
                )
                continue
        accepted.append(item)
    return accepted, rejected


def _deterministic_tag_normalise(
    detection: DetectionRecord,
    *,
    legend_pack: LegendPack | None = None,
) -> dict[str, Any] | None:
    """Enrich or retype a node only when its printed tag is unambiguous."""
    semantics = infer_tag_semantics(detection.label or "", legend_pack)
    if semantics is None:
        return None
    attrs = detection.attributes
    original_kind = detection.kind
    can_retype_to_instrument = (
        original_kind == "equipment"
        and semantics.expected_kind == "instrument"
        and not attrs.get("valve_type")
        and attrs.get("equipment_class")
        in (None, "", "equipment", "unclassified_equipment")
    )
    compatible = original_kind == semantics.expected_kind or can_retype_to_instrument
    if not compatible:
        return {
            "type": "tag_kind_conflict",
            "page_index": detection.page_index,
            "detection_id": detection.id,
            "label": detection.label,
            "model_kind": original_kind,
            "expected_kind": semantics.expected_kind,
            "tag_semantics": semantics.model_dump(mode="json"),
            "status": "unresolved",
            "reason": "printed tag/legend semantics disagree with a specific detected object kind",
        }

    if can_retype_to_instrument:
        detection.kind = "instrument"
    detection.attributes = {
        **attrs,
        **{key: value for key, value in semantics.attributes.items() if value not in (None, "")},
        "tag_prefix": semantics.prefix,
        "tag_semantics_basis": semantics.basis,
        "tag_legend_labels": semantics.legend_labels,
    }
    if can_retype_to_instrument:
        detection.attributes.update(
            {
                "model_original_kind": original_kind,
                "deterministic_retype_basis": "unambiguous_tag_and_legend_semantics",
            }
        )
    if not can_retype_to_instrument:
        return None
    return {
        "type": "deterministic_kind_correction",
        "page_index": detection.page_index,
        "detection_id": detection.id,
        "label": detection.label,
        "from_kind": "equipment",
        "to_kind": detection.kind,
        "status": "resolved",
        "reason": "printed tag and project/standard legend semantics identify the node kind",
        "tag_semantics": semantics.model_dump(mode="json"),
    }


def _is_native_text_only_detection(
    detection: DetectionRecord,
    page: PageEvidence,
) -> bool:
    label = " ".join((detection.label or detection.raw_text or "").split()).strip()
    if not label or _NON_CONNECTABLE_TEXT_RE.fullmatch(label) is None:
        return False
    # Nominal sizes and dimensions are intrinsically document/line evidence,
    # never connectable graph entities.  Reject them even when the model bbox
    # is offset from the exact native-text box (a common crop-projection error).
    if re.fullmatch(
        r"(?:DN\s*\d+(?:\s*[x×/]\s*\d+)?|\d+(?:\.\d+)?\s*(?:[\"”′]|mm|cm))",
        label,
        re.IGNORECASE,
    ):
        return True
    normalised = normalise_label(label)
    for span in page.text_spans:
        if normalise_label(span.text) != normalised:
            continue
        center_x = span.bbox.x + span.bbox.w / 2
        center_y = span.bbox.y + span.bbox.h / 2
        if not (
            detection.bbox.x <= center_x <= detection.bbox.x2
            and detection.bbox.y <= center_y <= detection.bbox.y2
        ):
            continue
        # Err on the cautious side: reject only a tight text-shaped box. A
        # larger symbol box that happens to contain this annotation survives.
        if detection.bbox.h <= max(24, span.bbox.h * 2.75) and detection.bbox.w <= max(
            40, span.bbox.w * 2.25
        ):
            return True
    return False


def _opc_has_boundary_support(detection: DetectionRecord, page: PageEvidence) -> bool:
    margin = max(60.0, min(page.width, page.height) * 0.05)
    bbox = detection.bbox
    touches_boundary = (
        bbox.x <= margin
        or bbox.y <= margin
        or bbox.x2 >= page.width - margin
        or bbox.y2 >= page.height - margin
    )
    attrs = detection.attributes
    explicit = bool(
        attrs.get("direction") in {"in", "out"}
        or attrs.get("drawing_ref")
        or attrs.get("target_sheet")
        or attrs.get("line_id")
        or _OPC_HINT_RE.search(detection.label or detection.raw_text or "")
    )
    if touches_boundary and explicit:
        attrs["boundary_evidence"] = True
        return True
    return False


def _opc_has_explicit_reference(detection: DetectionRecord) -> bool:
    attrs = detection.attributes
    candidates = (
        detection.label,
        detection.raw_text,
        attrs.get("canonical_tag"),
        attrs.get("drawing_ref"),
        attrs.get("target_sheet"),
    )
    return any(_EXPLICIT_OPC_REF_RE.search(str(value or "")) for value in candidates)


def _nearest_tag_anchor(page: PageEvidence, bbox: BBox) -> str | None:
    candidates = _nearby_tag_text(page.text_spans, bbox)
    return candidates[0].id if candidates else None


def _cluster_detections(
    detections: list[DetectionRecord],
    pages_by_index: dict[int, PageEvidence],
) -> list[_Cluster]:
    clusters: list[_Cluster] = []
    anchors = {
        item.id: _nearest_tag_anchor(pages_by_index[item.page_index], item.bbox)
        for item in detections
    }
    ordered = sorted(
        detections,
        key=lambda item: (
            item.page_index,
            item.bbox.y,
            item.bbox.x,
            item.kind,
            item.tile_id,
            item.id,
        ),
    )
    for detection in ordered:
        best: _Cluster | None = None
        best_score = -1.0
        for cluster in clusters:
            for member in cluster.detections:
                if member.page_index != detection.page_index:
                    continue
                iou = member.bbox.iou(detection.bbox)
                member_label = normalise_label(member.label)
                detection_label = normalise_label(detection.label)
                same_label = bool(member_label and member_label == detection_label)
                shared_anchor = bool(
                    anchors.get(member.id) and anchors.get(member.id) == anchors.get(detection.id)
                )
                center_distance = _center_distance(member.bbox, detection.bbox)
                scale = max(
                    member.bbox.w,
                    member.bbox.h,
                    detection.bbox.w,
                    detection.bbox.h,
                    1,
                )
                geometry_factor = 0.35 if member.kind == detection.kind == "opc" else 0.65
                label_factor = 0.4 if member.kind == detection.kind == "opc" else 1.75
                same_kind_geometry = member.kind == detection.kind and (
                    iou >= 0.18 or center_distance <= scale * geometry_factor
                )
                label_geometry = same_label and center_distance <= scale * label_factor
                anchor_geometry = shared_anchor and center_distance <= scale * 2.25
                if not (same_kind_geometry or label_geometry or anchor_geometry):
                    continue
                if member.kind != detection.kind and not shared_anchor:
                    continue
                score = iou + (0.5 if same_label else 0.0) + (0.65 if shared_anchor else 0.0)
                if score > best_score:
                    best = cluster
                    best_score = score
        if best is None:
            clusters.append(_Cluster([detection]))
        else:
            best.detections.append(detection)
    return clusters


def _node_from_cluster(
    cluster: _Cluster,
    pages_by_index: dict[int, PageEvidence],
) -> tuple[ReconciledNode, list[dict[str, Any]], int]:
    kind_counts = Counter(item.kind for item in cluster.detections)
    selected_kind = max(
        kind_counts,
        key=lambda kind: (
            kind_counts[kind],
            max(_CONF_RANK[item.confidence] for item in cluster.detections if item.kind == kind),
            kind == "equipment",
        ),
    )
    ordered = sorted(
        cluster.detections,
        key=lambda item: (
            item.kind == selected_kind,
            _CONF_RANK[item.confidence],
            bool(item.label),
            item.id,
        ),
        reverse=True,
    )
    canonical = ordered[0]
    fused_bbox = _median_bbox(ordered)
    labels = _ordered_unique(item.label for item in ordered if item.label)
    raw_readings = _ordered_unique(item.raw_text for item in ordered if item.raw_text)
    source_tiles = sorted({item.tile_id for item in ordered})

    page = pages_by_index[canonical.page_index]
    native_candidates = _nearby_tag_text(page.text_spans, fused_bbox)
    label_conflict = len({normalise_label(label) for label in labels if normalise_label(label)}) > 1
    native_label_matches = [
        label
        for label in labels
        if any(normalise_label(span.text) == normalise_label(label) for span in native_candidates)
    ]
    selected_label = canonical.label or (raw_readings[0] if raw_readings else "unlabelled")
    native_resolved_label = (
        native_label_matches[0]
        if len({normalise_label(label) for label in native_label_matches}) == 1
        else None
    )
    if native_resolved_label:
        selected_label = native_resolved_label

    # A geometry cluster can contain two nearby printed identities (for
    # example an equipment tag and an adjacent valve/instrument tag).  Preserve
    # the conflict as evidence, but never let semantic attributes learned for
    # one identity silently contaminate the identity selected by native text.
    selected_key = normalise_label(selected_label)
    generic_keys = {"", "unlabelled", "unlabeled", "unknown", "none", "na"}
    identity_contributors = [
        item
        for item in ordered
        if item.kind == selected_kind
        and (
            normalise_label(item.label or "") == selected_key
            or normalise_label(item.label or "") in generic_keys
        )
    ]
    if not identity_contributors:
        identity_contributors = [canonical]
    identity_canonical = identity_contributors[0]
    text_ids = sorted(
        {value for item in identity_contributors for value in item.source_text_ids}
    )
    evidence_ids = sorted({item.id for item in ordered} | set(text_ids))

    attributes: dict[str, Any] = {}
    for item in identity_contributors:
        for key, value in item.attributes.items():
            if key not in attributes and value not in (None, "", [], {}):
                attributes[key] = value
    attributes["source_tiles"] = source_tiles
    attributes["model_confidence"] = identity_canonical.confidence
    attributes = _normalise_taxonomy(attributes, kind=selected_kind)
    for span in native_candidates:
        if span.id not in text_ids:
            text_ids.append(span.id)
            evidence_ids.append(span.id)
    text_ids.sort()
    evidence_ids = sorted(set(evidence_ids))
    if native_candidates:
        attributes["raw_text_candidates"] = [span.text for span in native_candidates]
        attributes["source_text_ids"] = text_ids

    native_agreement = native_resolved_label is not None
    score = {"high": 0.72, "medium": 0.54, "low": 0.34}[identity_canonical.confidence]
    score += min(0.14, max(0, len(ordered) - 1) * 0.07)
    score += 0.12 if native_agreement else 0.0
    score += 0.04 if raw_readings else 0.0
    score -= 0.18 if label_conflict and not native_resolved_label else 0.0
    if selected_kind == "opc" and attributes.get("opc_context_required"):
        score -= 0.14
    score = round(max(0.05, min(0.98, score)), 3)
    attributes["system_confidence"] = score
    attributes["system_confidence_evidence"] = {
        "overlapping_detections": len(ordered),
        "native_text_agreement": native_agreement,
        "label_conflict": label_conflict,
    }

    node_id = _stable_node_id(
        identity_canonical,
        selected_label,
        bbox=fused_bbox,
    )
    ambiguities: list[dict[str, Any]] = []
    if label_conflict:
        ambiguities.append(
            {
                "type": "evidence_label_conflict",
                "page_index": canonical.page_index,
                "node_id": node_id,
                "labels": labels,
                "bbox": fused_bbox.model_dump(),
                "status": "resolved" if native_resolved_label else "unresolved",
                "reason": (
                    "exact native PDF text match"
                    if native_resolved_label
                    else "overlapping observations disagree"
                ),
            }
        )
    if len(kind_counts) > 1:
        dominant = kind_counts[selected_kind] > max(
            count for kind, count in kind_counts.items() if kind != selected_kind
        )
        ambiguities.append(
            {
                "type": "evidence_kind_conflict",
                "page_index": canonical.page_index,
                "node_id": node_id,
                "kinds": dict(kind_counts),
                "selected_kind": selected_kind,
                "bbox": fused_bbox.model_dump(),
                "status": "resolved" if dominant else "unresolved",
                "reason": "dominant overlapping evidence"
                if dominant
                else "equal conflicting evidence",
            }
        )
    if selected_kind == "opc" and attributes.get("opc_context_required"):
        ambiguities.append(
            {
                "type": "opc_context_validation",
                "page_index": canonical.page_index,
                "node_id": node_id,
                "label": selected_label,
                "bbox": fused_bbox.model_dump(),
                "status": "unresolved",
                "reason": "explicit continuation reference is away from the physical PDF edge",
            }
        )

    return (
        ReconciledNode(
            id=node_id,
            kind=selected_kind,
            label=selected_label,
            bbox_global=fused_bbox,
            page_index=canonical.page_index,
            attributes=attributes,
            confidence=identity_canonical.confidence,
            source_quote=(
                identity_canonical.raw_text
                or identity_canonical.label
                or (raw_readings[0] if raw_readings else None)
            ),
            alternate_readings=[label for label in labels if label != selected_label],
            source_annotation_ids=[item.id for item in ordered],
            source_evidence_ids=evidence_ids,
            system_confidence=score,
            system_confidence_level=_confidence_level(score),
        ),
        ambiguities,
        len(native_candidates),
    )


def _nearby_tag_text(spans: list[TextEvidence], bbox: BBox) -> list[TextEvidence]:
    padding = max(20, int(max(bbox.w, bbox.h) * 0.75))
    x0 = bbox.x - padding
    y0 = bbox.y - padding
    x1 = bbox.x2 + padding
    y1 = bbox.y2 + padding
    candidates = [
        span
        for span in spans
        if _TAG_RE.search(span.text)
        and span.bbox.x < x1
        and span.bbox.x2 > x0
        and span.bbox.y < y1
        and span.bbox.y2 > y0
    ]
    return sorted(candidates, key=lambda span: _center_distance(span.bbox, bbox))[:8]


def _median_bbox(detections: list[DetectionRecord]) -> BBox:
    values = (
        statistics.median(getattr(item.bbox, field_name) for item in detections)
        for field_name in ("x", "y", "w", "h")
    )
    x, y, w, h = (int(round(value)) for value in values)
    return BBox(x=max(0, x), y=max(0, y), w=max(1, w), h=max(1, h))


def _normalise_taxonomy(attributes: dict[str, Any], *, kind: str) -> dict[str, Any]:
    attrs = dict(attributes)
    direction = _normalise_key(attrs.get("direction"))
    direction_aliases = {
        "to": "out",
        "outgoing": "out",
        "outlet": "out",
        "outflow": "out",
        "to_network": "out",
        "from": "in",
        "incoming": "in",
        "inlet": "in",
        "inflow": "in",
        "inbound": "in",
    }
    if direction:
        attrs["direction"] = direction_aliases.get(direction, direction)

    if kind == "equipment":
        raw_equipment = _normalise_key(attrs.get("equipment_class"))
        raw_valve = _normalise_key(attrs.get("valve_type"))
        if raw_equipment == "valve" and not raw_valve:
            raw_valve = "other"
        if raw_valve:
            normalised_valve = _VALVE_ALIASES.get(raw_valve, raw_valve)
            if normalised_valve not in VALVE_TYPE_KEYS:
                normalised_valve = "other"
            if normalised_valve != raw_valve:
                attrs.setdefault("model_valve_type", raw_valve)
            attrs["valve_type"] = normalised_valve
            attrs.pop("equipment_class", None)
        elif raw_equipment:
            normalised_equipment = _EQUIPMENT_ALIASES.get(raw_equipment, raw_equipment)
            if normalised_equipment not in EQUIPMENT_CLASS_KEYS:
                normalised_equipment = "unclassified_equipment"
            if normalised_equipment != raw_equipment:
                attrs.setdefault("model_equipment_class", raw_equipment)
            attrs["equipment_class"] = normalised_equipment

    if kind == "instrument":
        raw_class = _normalise_key(attrs.get("instrument_class"))
        raw_function = _normalise_key(attrs.get("instrument_function"))
        if raw_class and raw_class not in INSTRUMENT_CLASS_KEYS:
            attrs.setdefault("model_instrument_class", raw_class)
            attrs.pop("instrument_class", None)
            if not raw_function or raw_function == "unclassified_instrument":
                raw_function = _instrument_function_from_text(raw_class)
            variable = _measured_variable_from_text(raw_class)
            if variable and not attrs.get("measured_variable"):
                attrs["measured_variable"] = variable
        if raw_function:
            normalised_function = _instrument_function_from_text(raw_function)
            attrs["instrument_function"] = normalised_function
        elif not attrs.get("instrument_function"):
            attrs["instrument_function"] = "unclassified_instrument"
    return attrs


def _normalise_key(value: Any) -> str:
    return re.sub(r"_+", "_", re.sub(r"[^a-z0-9]+", "_", str(value or "").lower())).strip("_")


def _instrument_function_from_text(value: str) -> str:
    for key in (
        "controller",
        "transmitter",
        "indicator",
        "recorder",
        "element",
        "switch",
        "alarm",
        "valve_actuator",
    ):
        if key in value:
            return key
    return value if value in INSTRUMENT_FUNCTION_KEYS else "unclassified_instrument"


def _measured_variable_from_text(value: str) -> str | None:
    for key in ("pressure", "temperature", "flow", "level", "analysis"):
        if key in value:
            return key
    return None


def _stable_node_id(
    detection: DetectionRecord,
    label: str,
    *,
    bbox: BBox | None = None,
) -> str:
    bbox = bbox or detection.bbox
    quantized = tuple(int(round(value / 10.0) * 10) for value in (bbox.x, bbox.y, bbox.w, bbox.h))
    payload = repr(
        (detection.page_index, detection.kind, normalise_label(label), quantized)
    ).encode("utf-8")
    return "n-" + hashlib.sha256(payload).hexdigest()[:16]


def _match_opcs(
    nodes: list[ReconciledNode],
    *,
    pages_by_index: dict[int, PageEvidence],
) -> tuple[list[ReconciledEdge], list[dict[str, Any]], list[dict[str, Any]]]:
    opcs = [node for node in nodes if node.kind == "opc"]
    sheet_refs = {
        page_index: _page_drawing_reference(page) for page_index, page in pages_by_index.items()
    }
    matched: set[str] = set()
    edges: list[ReconciledEdge] = []
    ambiguities: list[dict[str, Any]] = []

    # A pair is safe to create without an LLM when the connector references
    # are reciprocal with the two title-block drawing numbers, the directions
    # oppose, the services do not conflict, and neither endpoint has an equally
    # supported alternative. This is the native convention used by the 2401
    # drawing and is substantially stronger than equal-label matching.
    reciprocal_candidates: list[tuple[float, ReconciledNode, ReconciledNode]] = []
    for index, left in enumerate(opcs):
        for right in opcs[index + 1 :]:
            if left.page_index == right.page_index:
                continue
            left_ref = _opc_visible_reference(left)
            right_ref = _opc_visible_reference(right)
            left_sheet = sheet_refs.get(left.page_index)
            right_sheet = sheet_refs.get(right.page_index)
            if not (
                left_ref
                and right_ref
                and left_sheet
                and right_sheet
                and left_ref == right_sheet
                and right_ref == left_sheet
            ):
                continue
            left_direction = str(left.attributes.get("direction") or "").casefold()
            right_direction = str(right.attributes.get("direction") or "").casefold()
            if {left_direction, right_direction} != {"in", "out"}:
                continue
            compatible, service_score = _opc_services_compatible(left, right)
            if not compatible:
                continue
            reciprocal_candidates.append((10.0 + service_score, left, right))

    selected = _maximum_weight_opc_pairs(opcs, reciprocal_candidates)
    candidates_by_node: dict[str, list[float]] = {}
    for score, left, right in reciprocal_candidates:
        candidates_by_node.setdefault(left.id, []).append(score)
        candidates_by_node.setdefault(right.id, []).append(score)
    for score, left, right in selected:
        left_scores = sorted(candidates_by_node.get(left.id, []), reverse=True)
        right_scores = sorted(candidates_by_node.get(right.id, []), reverse=True)
        unique = (len(left_scores) == 1 or left_scores[0] - left_scores[1] >= 1.0) and (
            len(right_scores) == 1 or right_scores[0] - right_scores[1] >= 1.0
        )
        if not unique:
            ambiguities.append(
                _opc_ambiguity(
                    left,
                    right,
                    score=score,
                    reason="reciprocal sheet references have a competing one-to-one candidate",
                    sheet_refs=sheet_refs,
                )
            )
            continue
        matched.update((left.id, right.id))
        edges.append(
            _opc_edge(
                left,
                right,
                confidence="high",
                system_confidence=0.94,
                attributes={
                    "match_basis": "reciprocal_title_block_references",
                    "left_sheet_ref": sheet_refs.get(left.page_index),
                    "right_sheet_ref": sheet_refs.get(right.page_index),
                    "candidate_score": round(score, 3),
                },
            )
        )

    reference_groups: dict[str, list[ReconciledNode]] = {}
    for node in opcs:
        if node.id in matched:
            continue
        reference = _opc_reference(node)
        if reference:
            reference_groups.setdefault(reference, []).append(node)
    for reference, values in sorted(reference_groups.items()):
        ordered_values = sorted(values, key=lambda node: (node.page_index, node.id))
        candidates = _opc_pair_candidates(ordered_values)
        selected_pairs = _maximum_weight_opc_pairs(ordered_values, candidates)
        candidate_table = [
            {
                "node_ids": [left.id, right.id],
                "pages": [left.page_index + 1, right.page_index + 1],
                "score": round(score, 3),
                "left_direction": left.attributes.get("direction"),
                "right_direction": right.attributes.get("direction"),
                "left_service": left.attributes.get("service"),
                "right_service": right.attributes.get("service"),
                "left_line_id": left.attributes.get("line_id"),
                "right_line_id": right.attributes.get("line_id"),
            }
            for score, left, right in candidates[:16]
        ]
        for score, left, right in selected_pairs:
            ambiguities.append(
                {
                    "type": "ambiguous_opc_evidence",
                    "reference": reference,
                    "node_ids": [left.id, right.id],
                    "page_indices": [left.page_index, right.page_index],
                    "candidate_score": round(score, 3),
                    "candidate_group_size": len(ordered_values),
                    "candidate_pairs": candidate_table,
                    "status": "unresolved",
                    "reason": (
                        "maximum-weight one-to-one candidate requires bounded visual confirmation"
                    ),
                }
            )

    dangling = [
        {
            "node_id": node.id,
            "label": node.label,
            "page_index": node.page_index,
            "reason": "no uniquely supported evidence-v2 OPC pair",
        }
        for node in opcs
        if node.id not in matched
    ]
    return edges, dangling, ambiguities


def _page_drawing_reference(page: PageEvidence) -> str | None:
    """Read the sheet's own drawing number from its lower-right title block."""
    candidates: list[tuple[float, str]] = []
    for span in page.text_spans:
        match = _EXPLICIT_OPC_REF_RE.search(span.text)
        if match is None:
            continue
        # Connector references occur in the drawing body. The sheet identifier
        # is conventionally in the lower-right title block; require that region
        # so a continuation label cannot masquerade as the current sheet.
        if span.bbox.x < page.width * 0.55 or span.bbox.y < page.height * 0.78:
            continue
        reference = re.sub(r"\s+", "", match.group(0)).upper()
        score = span.bbox.x / page.width + span.bbox.y / page.height
        candidates.append((score, reference))
    if not candidates:
        return None
    candidates.sort(key=lambda row: (-row[0], row[1]))
    return candidates[0][1]


def _opc_visible_reference(node: ReconciledNode) -> str | None:
    """Return only a reference supported by visible node text.

    A model-only ``drawing_ref`` on an unlabelled symbol is useful evidence for
    review but is not strong enough for an automatic cross-sheet edge.
    """
    values = (
        node.label,
        node.source_quote,
        node.attributes.get("canonical_tag"),
    )
    for value in values:
        match = _EXPLICIT_OPC_REF_RE.search(str(value or ""))
        if match:
            return re.sub(r"\s+", "", match.group(0)).upper()
    return None


def _opc_services_compatible(
    left: ReconciledNode,
    right: ReconciledNode,
) -> tuple[bool, float]:
    left_service = _opc_service_key(left.attributes.get("service"))
    right_service = _opc_service_key(right.attributes.get("service"))
    if not left_service or not right_service:
        return True, 0.0
    if left_service == right_service:
        return True, 2.0
    if left_service in right_service or right_service in left_service:
        return True, 1.0
    return False, 0.0


def _opc_ambiguity(
    left: ReconciledNode,
    right: ReconciledNode,
    *,
    score: float,
    reason: str,
    sheet_refs: dict[int, str | None],
) -> dict[str, Any]:
    return {
        "type": "ambiguous_opc_evidence",
        "node_ids": [left.id, right.id],
        "page_indices": [left.page_index, right.page_index],
        "candidate_score": round(score, 3),
        "sheet_references": [
            sheet_refs.get(left.page_index),
            sheet_refs.get(right.page_index),
        ],
        "status": "unresolved",
        "reason": reason,
    }


def _opc_edge(
    left: ReconciledNode,
    right: ReconciledNode,
    *,
    confidence: Confidence,
    system_confidence: float,
    attributes: dict[str, Any],
) -> ReconciledEdge:
    left_direction = str(left.attributes.get("direction") or "").casefold()
    outgoing, incoming = (left, right) if left_direction == "out" else (right, left)
    edge_id = "e-opc-" + hashlib.sha256(f"{outgoing.id}|{incoming.id}".encode()).hexdigest()[:12]
    return ReconciledEdge(
        id=edge_id,
        from_node=outgoing.id,
        to_node=incoming.id,
        line_type="process",
        cross_sheet=True,
        confidence=confidence,
        source_evidence_ids=sorted(set(left.source_evidence_ids + right.source_evidence_ids)),
        system_confidence=system_confidence,
        system_confidence_level=_confidence_level(system_confidence),
        attributes=attributes,
    )


def _opc_pair_candidates(
    values: list[ReconciledNode],
) -> list[tuple[float, ReconciledNode, ReconciledNode]]:
    return sorted(
        (
            (_opc_pair_score(left, right), left, right)
            for index, left in enumerate(values)
            for right in values[index + 1 :]
            if left.page_index != right.page_index
        ),
        key=lambda row: (-row[0], row[1].id, row[2].id),
    )


def _maximum_weight_opc_pairs(
    values: list[ReconciledNode],
    candidates: list[tuple[float, ReconciledNode, ReconciledNode]],
) -> list[tuple[float, ReconciledNode, ReconciledNode]]:
    """Return a deterministic globally optimal set of disjoint candidate pairs."""
    if not candidates:
        return []
    if len(values) > 16:
        # Exact subset matching is exponential. Extremely repetitive connector
        # references are already low-information, so use the same deterministic
        # score order while preserving the one-to-one invariant.
        claimed: set[str] = set()
        selected: list[tuple[float, ReconciledNode, ReconciledNode]] = []
        for score, left, right in candidates:
            if left.id in claimed or right.id in claimed:
                continue
            claimed.update((left.id, right.id))
            selected.append((score, left, right))
        return selected
    by_id = {node.id: node for node in values}
    score_by_pair = {tuple(sorted((left.id, right.id))): score for score, left, right in candidates}
    ids = tuple(sorted(by_id))

    @cache
    def solve(remaining: tuple[str, ...]) -> tuple[float, tuple[tuple[str, str], ...]]:
        if len(remaining) < 2:
            return 0.0, ()
        first = remaining[0]
        best_score, best_pairs = solve(remaining[1:])
        for offset, other in enumerate(remaining[1:], start=1):
            key = tuple(sorted((first, other)))
            pair_score = score_by_pair.get(key)
            if pair_score is None:
                continue
            rest = remaining[1:offset] + remaining[offset + 1 :]
            rest_score, rest_pairs = solve(rest)
            proposed_score = pair_score + rest_score
            proposed_pairs = tuple(sorted((key, *rest_pairs)))
            if proposed_score > best_score or (
                math.isclose(proposed_score, best_score) and proposed_pairs < best_pairs
            ):
                best_score, best_pairs = proposed_score, proposed_pairs
        return best_score, best_pairs

    _, selected = solve(ids)
    result = [(score_by_pair[pair], by_id[pair[0]], by_id[pair[1]]) for pair in selected]
    return sorted(result, key=lambda row: (-row[0], row[1].id, row[2].id))


def _opc_reference(node: ReconciledNode) -> str | None:
    values = (
        node.label,
        node.attributes.get("canonical_tag"),
        node.attributes.get("drawing_ref"),
    )
    for value in values:
        match = _EXPLICIT_OPC_REF_RE.search(str(value or ""))
        if match:
            return re.sub(r"\s+", "", match.group(0)).upper()
    return None


def _opc_pair_score(left: ReconciledNode, right: ReconciledNode) -> float:
    score = 1.0
    left_direction = str(left.attributes.get("direction") or "").casefold()
    right_direction = str(right.attributes.get("direction") or "").casefold()
    if {left_direction, right_direction} == {"in", "out"}:
        score += 1.5
    left_service = _opc_service_key(left.attributes.get("service"))
    right_service = _opc_service_key(right.attributes.get("service"))
    if left_service and right_service:
        if left_service == right_service:
            score += 2.0
        elif left_service in right_service or right_service in left_service:
            score += 1.0
    left_line = normalise_label(str(left.attributes.get("line_id") or ""))
    right_line = normalise_label(str(right.attributes.get("line_id") or ""))
    if left_line and left_line == right_line:
        score += 2.0
    return score


def _opc_service_key(value: Any) -> str:
    text = str(value or "").casefold()
    service_aliases = (
        (("instrument air", "仪表空气"), "instrument_air"),
        (("compressed air", "压缩空气"), "compressed_air"),
        (("dry air", "dried air", "干燥风", "干燥空气"), "dried_air"),
        (("purified air", "净化风", "净化空气"), "purified_air"),
        (("nitrogen", "氮气"), "nitrogen"),
        (("cooling water supply", "循环冷却水给水", "cws"), "cooling_water_supply"),
        (("cooling water return", "循环冷却水回水", "cwr"), "cooling_water_return"),
    )
    for aliases, canonical in service_aliases:
        if any(alias in text for alias in aliases):
            return canonical
    text = re.sub(r"(?:来自|去往|至|自|\bto\b|\bfrom\b)", " ", text)
    text = re.sub(r"2401[-a-z0-9/]+", " ", text)
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", text)


def _deduplicate_edges(edges: list[ReconciledEdge]) -> list[ReconciledEdge]:
    selected: dict[tuple[Any, ...], ReconciledEdge] = {}
    for edge in edges:
        endpoints = sorted((edge.from_node, edge.to_node))
        poly_ends = []
        if edge.polyline_global:
            poly_ends = sorted(
                (
                    tuple(int(round(value / 10.0) * 10) for value in edge.polyline_global[0]),
                    tuple(int(round(value / 10.0) * 10) for value in edge.polyline_global[-1]),
                )
            )
        key = (
            endpoints[0],
            endpoints[1],
            str(edge.line_type or "other"),
            tuple(poly_ends),
        )
        previous = selected.get(key)
        if previous is None or len(edge.polyline_global) < len(previous.polyline_global):
            selected[key] = edge
    return list(selected.values())


def _center_distance(left: BBox, right: BBox) -> float:
    left_center = (left.x + left.w / 2, left.y + left.h / 2)
    right_center = (right.x + right.w / 2, right.y + right.h / 2)
    return math.dist(left_center, right_center)


def _ordered_unique(values: Any) -> list[str]:
    out: list[str] = []
    for value in values:
        rendered = str(value or "").strip()
        if rendered and rendered not in out:
            out.append(rendered)
    return out


def _confidence_level(score: float) -> Confidence:
    if score >= 0.78:
        return "high"
    if score >= 0.52:
        return "medium"
    return "low"


def _coerce_page_status(status: str) -> str:
    return status if status in {"ok", "partial", "cost_exhausted", "error"} else "error"
