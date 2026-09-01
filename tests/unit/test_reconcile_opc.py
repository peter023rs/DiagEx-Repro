from __future__ import annotations

from diagex.vision.models import Annotation, BBox, ReconciledGraph, ReconciledNode
from diagex.vision.reconcile import _enrich_opcs, reconcile


def _annotation(
    aid: str,
    *,
    page: int,
    kind: str,
    label: str,
    x: int,
    y: int,
    attributes: dict | None = None,
    source_quote: str | None = None,
) -> Annotation:
    box = BBox(x=x, y=y, w=220, h=40)
    return Annotation(
        id=aid,
        page_index=page,
        kind=kind,  # type: ignore[arg-type]
        source_view="overview",
        bbox_local=box,
        bbox_global=box,
        label=label,
        attributes=attributes or {},
        confidence="high",
        source_quote=source_quote,
    )


def test_reconcile_preserves_source_quote_and_enriches_opc_conservatively():
    graph = reconcile(
        [
            _annotation(
                "opc-1",
                page=0,
                kind="opc",
                label="Compressed Air inlet",
                x=300,
                y=500,
                source_quote="压缩空气自2401-V-002",
            ),
            _annotation(
                "text-ref",
                page=0,
                kind="text",
                label="DW02-0003",
                x=350,
                y=555,
            ),
        ]
    )
    opc = next(node for node in graph.nodes if node.kind == "opc")
    assert opc.source_quote == "压缩空气自2401-V-002"
    assert opc.attributes["raw_text"] == "压缩空气自2401-V-002"
    assert opc.attributes["service"] == "compressed_air"
    assert opc.attributes["direction"] == "in"
    assert opc.attributes["source_equipment"] == "2401-V-002"
    assert opc.attributes["drawing_ref"] == "DW02-0003"
    assert opc.attributes["attribute_evidence"]["source_equipment"] == "printed_text"


def test_repeated_same_direction_utility_opcs_are_not_ambiguous():
    graph = reconcile(
        [
            _annotation("a", page=0, kind="opc", label="Compressed Air inlet", x=10, y=10),
            _annotation("b", page=1, kind="opc", label="Compressed Air inlet", x=10, y=10),
            _annotation("c", page=2, kind="opc", label="Compressed Air inlet", x=10, y=10),
        ]
    )
    assert not any(conflict.get("type") == "ambiguous_opc" for conflict in graph.conflicts)
    assert len(graph.dangling_opcs) == 3
    assert {item["reason"] for item in graph.dangling_opcs} == {"no_complementary_direction"}


def test_multiple_opcs_pair_only_on_unique_shared_reference():
    graph = reconcile(
        [
            _annotation("out-a", page=0, kind="opc", label="Nitrogen outlet", x=10, y=10,
                        attributes={"direction": "out", "drawing_ref": "DW02-1001"}),
            _annotation("in-a", page=1, kind="opc", label="Nitrogen inlet", x=10, y=10,
                        attributes={"direction": "in", "drawing_ref": "DW02-1001"}),
            _annotation("out-b", page=2, kind="opc", label="Nitrogen outlet", x=10, y=10,
                        attributes={"direction": "out", "drawing_ref": "DW02-1002"}),
            _annotation("in-b", page=3, kind="opc", label="Nitrogen inlet", x=10, y=10,
                        attributes={"direction": "in", "drawing_ref": "DW02-1002"}),
        ]
    )
    assert len([edge for edge in graph.edges if edge.cross_sheet]) == 2
    assert not any(conflict.get("type") == "ambiguous_opc" for conflict in graph.conflicts)


def test_single_complementary_pair_without_shared_reference_is_not_auto_stitched():
    graph = reconcile(
        [
            _annotation("out", page=0, kind="opc", label="CWS outlet", x=10, y=10),
            _annotation("in", page=1, kind="opc", label="CWS inlet", x=10, y=10),
        ]
    )
    assert not any(edge.cross_sheet for edge in graph.edges)
    conflict = next(item for item in graph.conflicts if item.get("type") == "ambiguous_opc")
    assert conflict["reason"] == "complementary connectors lack a shared drawing/line reference"


def test_ambiguous_complementary_opcs_still_require_review():
    graph = reconcile(
        [
            _annotation("out-a", page=0, kind="opc", label="Steam outlet", x=10, y=10),
            _annotation("out-b", page=1, kind="opc", label="Steam outlet", x=10, y=10),
            _annotation("in-a", page=2, kind="opc", label="Steam inlet", x=10, y=10),
        ]
    )
    conflicts = [conflict for conflict in graph.conflicts if conflict.get("type") == "ambiguous_opc"]
    assert len(conflicts) == 1
    assert conflicts[0]["reason"] == "multiple complementary connectors lack a unique shared reference"


def test_enrichment_omits_ambiguous_nearby_references():
    graph = ReconciledGraph(
        source_path="test.pdf",
        nodes=[
            ReconciledNode(id="opc", kind="opc", label="Steam inlet", bbox_global=BBox(x=100, y=100, w=200, h=40), page_index=0, confidence="high"),
            ReconciledNode(id="ref-a", kind="text", label="DW02-1001", bbox_global=BBox(x=100, y=150, w=100, h=20), page_index=0, confidence="high"),
            ReconciledNode(id="ref-b", kind="text", label="DW02-1002", bbox_global=BBox(x=210, y=150, w=100, h=20), page_index=0, confidence="high"),
        ]
    )
    _enrich_opcs(graph.nodes, graph.edges)
    opc = graph.nodes[0]
    assert "drawing_ref" not in opc.attributes


def test_enrichment_does_not_choose_a_conflicting_direction():
    node = ReconciledNode(
        id="opc", kind="opc", label="Steam outlet",
        bbox_global=BBox(x=100, y=100, w=200, h=40), page_index=0,
        confidence="high", source_quote="Steam from V-100",
    )
    _enrich_opcs([node], [])
    assert "direction" not in node.attributes
    assert node.attributes["direction_candidates"] == ["in", "out"]
    assert node.attributes["attribute_evidence"]["direction"] == "conflicting_evidence"
