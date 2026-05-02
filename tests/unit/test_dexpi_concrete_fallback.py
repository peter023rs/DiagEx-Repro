"""v2 Phase C: every LLM-extraction output routes to a concrete DEXPI 2.0 class.

After Phase C, ``dexpi_builder.build_dexpi`` no longer emits ``CustomEquipment``
or ``CustomOperatedValve``. Unrecognised LLM keys fall back to the most
specific concrete DEXPI ancestor (``ProcessEquipment`` / ``OperatedValve``)
and the original LLM string is preserved on ``customAttributes`` via the
``agent_*`` prefix.

The XML writer's ``UnsupportedClassError`` is therefore unreachable from any
production path: a model produced by ``build_dexpi`` always emits cleanly.
"""
from __future__ import annotations

import pytest

from diagex.dexpi import xml_io
from diagex.dexpi._generated.plant import OperatedValve, ProcessEquipment
from diagex.extractors.dexpi_builder import build_dexpi
from diagex.vision.models import BBox, ReconciledEdge, ReconciledGraph, ReconciledNode


def _node(
    nid: str,
    kind: str,
    label: str,
    attrs: dict | None = None,
    conf: str = "high",
) -> ReconciledNode:
    return ReconciledNode(
        id=nid,
        kind=kind,  # type: ignore[arg-type]
        label=label,
        bbox_global=BBox(x=0, y=0, w=20, h=20),
        page_index=0,
        attributes=attrs or {},
        confidence=conf,  # type: ignore[arg-type]
    )


def _edge(eid: str, src: str, tgt: str) -> ReconciledEdge:
    return ReconciledEdge(
        id=eid,
        from_node=src,
        to_node=tgt,
        line_type="process",
        polyline_global=[(0, 0), (10, 0)],
        confidence="high",
    )


# Names the LLM might emit that aren't in the diagex schema registry.
UNMAPPED_EQUIPMENT = [
    "reactor",
    "stirred_tank_reactor",
    "not_in_vocabulary",
    "unclassified_equipment",
    "frobnicator",
    "",  # empty equipment_class
]


UNMAPPED_VALVES = [
    "three_way",
    "wedge",
    "bizarre_valve",
    "control",  # control intent
    "",  # missing
]


@pytest.mark.parametrize("equipment_class", UNMAPPED_EQUIPMENT)
def test_unmapped_equipment_resolves_to_process_equipment(equipment_class: str):
    """Every unmapped key promotes to ``ProcessEquipment`` (no Custom* class)."""
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[_node("n1", "equipment", "X-1", {"equipment_class": equipment_class})],
    )
    result = build_dexpi(g)
    items = result.model.conceptual_model.TaggedPlantItems
    assert len(items) == 1
    assert type(items[0]) is ProcessEquipment, (
        f"unmapped class {equipment_class!r} should be ProcessEquipment, "
        f"got {type(items[0]).__name__}"
    )
    by_name = {ca.name: ca.value for ca in items[0].customAttributes}
    if equipment_class:
        assert by_name.get("agent_equipment_class") == equipment_class


@pytest.mark.parametrize("valve_type", UNMAPPED_VALVES)
def test_unmapped_valve_resolves_to_operated_valve(valve_type: str):
    """Every unmapped valve_type promotes to ``OperatedValve``, never Custom*."""
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[
            _node("t1", "equipment", "T-1", {"equipment_class": "tank"}),
            _node(
                "v1", "equipment", "V-1",
                {"equipment_class": "valve", "valve_type": valve_type},
            ),
        ],
        edges=[_edge("e1", "t1", "v1")],
    )
    result = build_dexpi(g)
    valves = [
        s
        for net in result.model.conceptual_model.PipingNetworkSystems
        for seg in net.Segments
        for s in seg.Items
        if isinstance(s, OperatedValve)
    ]
    assert valves, f"no OperatedValve emitted for valve_type={valve_type!r}"
    for v in valves:
        # Phase C contract: bare OperatedValve or a concrete subtype, never Custom*.
        assert "Custom" not in type(v).__name__


def test_xml_emit_does_not_raise_on_full_builder_output():
    """A model built from a graph mixing recognised + unmapped names emits cleanly."""
    nodes = [
        _node("e1", "equipment", "T-1", {"equipment_class": "tank"}),
        _node("e2", "equipment", "R-101", {"equipment_class": "reactor"}),
        _node("e3", "equipment", "M-1", {"equipment_class": "frobnicator"}),
        _node("v1", "equipment", "V-1", {"equipment_class": "valve", "valve_type": "ball"}),
        _node("v2", "equipment", "V-3W", {"equipment_class": "valve", "valve_type": "three_way"}),
        _node("v3", "equipment", "FCV-101", {"equipment_class": "valve", "valve_type": "control"}),
    ]
    edges = [
        _edge("ed1", "e1", "v1"),
        _edge("ed2", "v1", "e2"),
        _edge("ed3", "e2", "v2"),
        _edge("ed4", "v2", "e3"),
        _edge("ed5", "e3", "v3"),
    ]
    g = ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges)
    result = build_dexpi(g)
    # The full graph must emit cleanly — no UnsupportedClassError, no other write
    # error from the v1 Custom* code path.
    xml = xml_io.dumps(result.model)
    assert "<Model" in xml
    # Spot check the LLM hints survive in customAttributes via JSON; XML drops
    # customAttributes per matrix §4 option A but the model itself carries them.
    captured_classes = {
        ca.value
        for item in result.model.conceptual_model.TaggedPlantItems
        for ca in item.customAttributes
        if ca.name == "agent_equipment_class"
    }
    assert {"reactor", "frobnicator"}.issubset(captured_classes)


def test_unclassified_count_only_includes_promoted_fallbacks():
    """A graph with one recognised + two unmapped equipment items records 2."""
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[
            _node("e1", "equipment", "T-1", {"equipment_class": "tank"}),
            _node("e2", "equipment", "X-2", {"equipment_class": "reactor"}),
            _node("e3", "equipment", "X-3", {"equipment_class": "frobnicator"}),
        ],
    )
    result = build_dexpi(g)
    assert result.stats["equipment_count"] == 3
    assert result.stats["unclassified_count"] == 2
