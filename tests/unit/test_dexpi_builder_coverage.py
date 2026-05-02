"""v2 Phase E: builder coverage matrix over the DEXPI 2.0 spec palette.

Every ``EquipmentSpec`` and ``ValveSpec`` key the schema declares must resolve
to a concrete DEXPI 2.0 class (not the bare ``ProcessEquipment`` / ``OperatedValve``
ancestor) when the LLM provides a matching subtype hint. The Phase C contract
guarantees the *fallback* never raises; this Phase E test guarantees the
*resolution* picks the most specific class available.

Drift detection: if a future spec patch removes a class diagex names, the
matrix entry will fail with a clear "no concrete DEXPI class" message —
ahead of any extractor regression in the eval harness.
"""
from __future__ import annotations

import pytest

from diagex.dexpi._generated.plant import OperatedValve, PipingComponent, ProcessEquipment
from diagex.dexpi_schema import (
    EQUIPMENT_REGISTRY,
    VALVE_REGISTRY,
)
from diagex.extractors.dexpi_builder import build_dexpi
from diagex.vision.models import BBox, ReconciledEdge, ReconciledGraph, ReconciledNode


def _node(nid, kind, label, attrs):
    return ReconciledNode(
        id=nid,
        kind=kind,  # type: ignore[arg-type]
        label=label,
        bbox_global=BBox(x=0, y=0, w=20, h=20),
        page_index=0,
        attributes=attrs,
        confidence="high",  # type: ignore[arg-type]
    )


def _edge(eid, src, dst):
    return ReconciledEdge(
        id=eid,
        from_node=src,
        to_node=dst,
        line_type="process",
        polyline_global=[(0, 0), (10, 0)],
        confidence="high",
    )


def _equipment_keys_with_concrete_class() -> list[str]:
    return [s.key for s in EQUIPMENT_REGISTRY if s.pydexpi_class is not None]


def _valve_keys_with_concrete_class() -> list[str]:
    return [s.key for s in VALVE_REGISTRY if s.pydexpi_class is not None]


@pytest.mark.parametrize("equipment_key", _equipment_keys_with_concrete_class())
def test_each_equipment_key_resolves_to_a_concrete_subclass(equipment_key: str):
    """Spec key with a concrete pydexpi_class must produce that class, not bare ProcessEquipment."""
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[_node("n1", "equipment", "X-1", {"equipment_class": equipment_key})],
    )
    result = build_dexpi(g)
    items = result.model.conceptual_model.TaggedPlantItems
    assert len(items) == 1
    assert isinstance(items[0], ProcessEquipment), (
        f"{equipment_key!r} produced {type(items[0]).__name__}, "
        f"not a ProcessEquipment subclass"
    )
    assert type(items[0]) is not ProcessEquipment, (
        f"{equipment_key!r} fell back to bare ProcessEquipment despite having a "
        f"concrete pydexpi_class — the resolver missed it"
    )


@pytest.mark.parametrize("valve_key", _valve_keys_with_concrete_class())
def test_each_valve_key_resolves_to_a_concrete_subclass(valve_key: str):
    """Spec key with a concrete pydexpi_class produces a concrete PipingComponent.

    Some valves in the schema are ``PipingComponent`` siblings of ``OperatedValve``
    rather than subclasses (``CheckValve``, ``SafetyValveOrFitting``, ``Strainer``,
    ``RuptureDisc``) — DEXPI 2.0 distinguishes them at the next level up.

    A handful of spec entries deliberately resolve to the bare ``OperatedValve``
    ancestor (e.g. ``control``, where the control intent is a flag rather than
    a distinct class). Those keys are exempt from the "must be concrete" check.
    """
    spec = next(s for s in VALVE_REGISTRY if s.key == valve_key)
    expected_cls = spec.pydexpi_class
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[
            _node("t1", "equipment", "T-1", {"equipment_class": "tank"}),
            _node(
                "v1", "equipment", "V-1",
                {"equipment_class": "valve", "valve_type": valve_key},
            ),
        ],
        edges=[_edge("e1", "t1", "v1")],
    )
    result = build_dexpi(g)
    components = [
        s
        for net in result.model.conceptual_model.PipingNetworkSystems
        for seg in net.Segments
        for s in seg.Items
        if isinstance(s, PipingComponent)
    ]
    assert components, f"no PipingComponent emitted for {valve_key!r}"
    # Exact class match against the spec — covers both concrete subtypes and
    # the deliberate bare-ancestor cases.
    assert any(type(v) is expected_cls for v in components), (
        f"{valve_key!r}: expected at least one {expected_cls.__name__}, "
        f"got classes={[type(v).__name__ for v in components]}"
    )


# v2 Phase E: spot-checks of new spec keys with subtype-hint resolution.
@pytest.mark.parametrize(
    "equipment_class,subtype_attr,subtype_value,expected_cls_name",
    [
        ("dryer", "dryer_type", "convection", "ConvectionDryer"),
        ("dryer", "dryer_type", "heated_surface", "HeatedSurfaceDryer"),
        ("weigher", "weigher_type", "batch", "BatchWeigher"),
        ("weigher", "weigher_type", "continuous", "ContinuousWeigher"),
        ("mixer", "mixer_type", "static", "StaticMixer"),
        # InLineMixer is a PipingComponent in DEXPI 2.0, not a ProcessEquipment;
        # exercising it requires an edge endpoint, which the equipment-side
        # test setup doesn't provide. Covered indirectly via the valve test.
        ("mixer", "mixer_type", "rotary", "RotaryMixer"),
        ("transport_system", "transport_type", "stationary", "StationaryTransportSystem"),
        ("transport_system", "transport_type", "mobile", "MobileTransportSystem"),
        ("transport_system", "transport_type", "loading", "LoadingUnloadingSystem"),
        ("burner", None, None, "Burner"),
        ("air_cooler", None, None, "AirCoolingSystem"),
    ],
)
def test_phase_e_subtype_hints_resolve_to_concrete_classes(
    equipment_class: str,
    subtype_attr: str | None,
    subtype_value: str | None,
    expected_cls_name: str,
):
    attrs = {"equipment_class": equipment_class}
    if subtype_attr and subtype_value:
        attrs[subtype_attr] = subtype_value
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[_node("n1", "equipment", "X-1", attrs)],
    )
    result = build_dexpi(g)
    items = result.model.conceptual_model.TaggedPlantItems
    assert len(items) == 1
    assert type(items[0]).__name__ == expected_cls_name


def test_phase_e_no_concrete_key_falls_back_to_process_equipment():
    """Sanity: a spec with pydexpi_class=None still falls back to ProcessEquipment."""
    g = ReconciledGraph(
        source_path="t.pdf",
        nodes=[
            _node(
                "n1", "equipment", "X-1",
                {"equipment_class": "unclassified_equipment"},
            )
        ],
    )
    result = build_dexpi(g)
    items = result.model.conceptual_model.TaggedPlantItems
    assert type(items[0]) is ProcessEquipment
