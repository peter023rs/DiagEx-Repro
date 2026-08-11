"""Phase 4 acceptance tests: ``diagex.dexpi.xml_io`` write + round-trip.

Scope:

- diagex-emitted XML round-trips byte-stably (excluding top-level ``id``,
  which the wire format omits for the root ``<Object>``).
- Wire-format details: ``<Model>`` envelope, ``<Import>``, ``<Object>``,
  ``<Components>``, ``<Data>``, primitive value elements, ``<DataReference>``
  for enums.
- Diagex-internal fields (``customAttributes``, ``proteusId``) are dropped on
  emit per matrix §4 option A.
- Custom* extensions raise :class:`UnsupportedClassError` on emit (v1
  limitation; see ``xml_io.py`` module docstring).

Out of scope for v1:

- Full round-trip of the official ``reference_pid.xml`` fixture (uses
  features like ``<ObjectReference>`` and detailed ``BoundDataType``
  encoding the v1 generator/parser do not yet support).
"""
from __future__ import annotations

from xml.etree import ElementTree as ET

import pytest

from diagex.dexpi import xml_io
from diagex.dexpi._generated.core import EngineeringModel, MultiLanguageString, SingleLanguageString
from diagex.dexpi._generated.plant import (
    OperatedValve,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PlantModel,
)
from diagex.dexpi.extensions import (
    CustomEquipment,
    CustomOperatedValve,
    CustomStringAttribute,
)


def _build_minimal_plant() -> EngineeringModel:
    pm = PlantModel()
    seg = PipingNetworkSegment()
    sys_ = PipingNetworkSystem(Segments=[seg])
    pm.PipingNetworkSystems.append(sys_)
    seg.Items.append(OperatedValve())
    return EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )


# ---------------------------------------------------------------------------
# Envelope


def test_root_is_model_with_imports():
    em = _build_minimal_plant()
    xml = xml_io.dumps(em)
    root = ET.fromstring(xml)
    assert root.tag == "Model"
    imports = [c for c in root if c.tag == "Import"]
    assert len(imports) == 2
    prefixes = {i.get("prefix") for i in imports}
    assert prefixes == {"Core", "Plant"}


def test_top_level_object_is_engineering_model_without_id():
    """Top-level <Object> uses the type but omits the id, per the reference fixture."""
    em = _build_minimal_plant()
    root = ET.fromstring(xml_io.dumps(em))
    obj = next(c for c in root if c.tag == "Object")
    assert obj.get("type") == "Core/EngineeringModel"
    assert obj.get("id") is None


def test_xml_declaration_present():
    xml = xml_io.dumps(_build_minimal_plant())
    assert xml.startswith('<?xml version="1.0" encoding="UTF-8"?>')


# ---------------------------------------------------------------------------
# Object structure


def test_nested_objects_use_type_prefix():
    em = _build_minimal_plant()
    xml = xml_io.dumps(em)
    assert 'type="Plant/PlantModel"' in xml
    assert 'type="Plant/Piping.PipingNetworkSystem"' in xml
    assert 'type="Plant/Piping.PipingNetworkSegment"' in xml
    assert 'type="Plant/Piping.OperatedValve"' in xml


def test_compositions_wrap_nested_objects():
    em = _build_minimal_plant()
    root = ET.fromstring(xml_io.dumps(em))
    em_obj = next(c for c in root if c.tag == "Object")
    components_props = {c.get("property") for c in em_obj if c.tag == "Components"}
    assert "ConceptualModel" in components_props


# ---------------------------------------------------------------------------
# Data values


def test_primitive_strings_emitted_as_string_elements():
    em = _build_minimal_plant()
    xml = xml_io.dumps(em)
    assert "<String>diagex</String>" in xml
    assert "<String>ABB</String>" in xml


def test_enum_emitted_as_data_reference():
    """Enum field on an entity becomes <Data><DataReference data="..."/></Data>."""
    from diagex.dexpi._generated.enums import FailActionClassification
    from diagex.dexpi._generated.plant import ControlledActuator

    actuator = ControlledActuator(FailAction=FailActionClassification.FailClose)
    pm = PlantModel()
    # ControlledActuator can't be a direct child of PlantModel; wrap in something.
    # Easiest: emit just the actuator and test its serialisation.
    root = ET.Element("Model")
    xml_io._write_object(root, actuator)
    xml = ET.tostring(root, encoding="unicode")
    assert 'data="Plant/Enumerations.FailActionClassification.FailClose"' in xml


# ---------------------------------------------------------------------------
# Diagex-internal fields dropped


def test_custom_attributes_dropped_on_emit():
    """customAttributes must not appear in the emitted DEXPI XML (matrix §4 A)."""
    valve = OperatedValve()
    valve.customAttributes.append(CustomStringAttribute(name="hint", value="LLM"))

    pm = PlantModel(PipingNetworkSystems=[
        PipingNetworkSystem(Segments=[PipingNetworkSegment(Items=[valve])])
    ])
    em = EngineeringModel(
        ConceptualModel=pm, ExportDateTime=None,
        OriginatingSystemName="diagex", OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    xml = xml_io.dumps(em)
    assert "customAttributes" not in xml
    assert "CustomStringAttribute" not in xml
    assert "hint" not in xml


def test_proteusid_dropped_on_emit():
    em = _build_minimal_plant()
    em.proteusId = "PRO-1234"
    xml = xml_io.dumps(em)
    assert "proteusId" not in xml
    assert "PRO-1234" not in xml


# ---------------------------------------------------------------------------
# Diagex extensions raise on emit


def test_custom_equipment_raises_on_emit():
    pm = PlantModel(TaggedPlantItems=[CustomEquipment(typeName="unknown-pump")])
    em = EngineeringModel(
        ConceptualModel=pm, ExportDateTime=None,
        OriginatingSystemName="diagex", OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    with pytest.raises(xml_io.UnsupportedClassError):
        xml_io.dumps(em)


def test_custom_operated_valve_raises_on_emit():
    pm = PlantModel(PipingNetworkSystems=[
        PipingNetworkSystem(Segments=[
            PipingNetworkSegment(Items=[CustomOperatedValve(typeName="check-valve")])
        ])
    ])
    em = EngineeringModel(
        ConceptualModel=pm, ExportDateTime=None,
        OriginatingSystemName="diagex", OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    with pytest.raises(xml_io.UnsupportedClassError):
        xml_io.dumps(em)


# ---------------------------------------------------------------------------
# Round-trip


def test_diagex_emitted_xml_roundtrips():
    em = _build_minimal_plant()
    xml = xml_io.dumps(em)
    em2 = xml_io.loads(xml)

    assert isinstance(em2, EngineeringModel)
    assert em2.OriginatingSystemName == "diagex"
    pm2 = em2.conceptual_model
    assert isinstance(pm2, PlantModel)
    assert len(pm2.PipingNetworkSystems) == 1
    assert len(pm2.PipingNetworkSystems[0].Segments) == 1
    items = pm2.PipingNetworkSystems[0].Segments[0].Items
    assert len(items) == 1
    assert isinstance(items[0], OperatedValve)


def test_single_item_value_object_list_roundtrips():
    """A one-item aggregated list must not collapse into a scalar on parse."""
    value = MultiLanguageString(
        SingleLanguageStrings=[
            SingleLanguageString(Language="en-US", Value="compressor")
        ]
    )
    root = ET.Element("Model")
    xml_io._write_object(root, value, top_level=True)

    parsed = xml_io.loads(ET.tostring(root, encoding="unicode"))

    assert isinstance(parsed, MultiLanguageString)
    assert len(parsed.SingleLanguageStrings) == 1
    assert parsed.SingleLanguageStrings[0].Language == "en-US"
    assert parsed.SingleLanguageStrings[0].Value == "compressor"


def test_nested_ids_preserved_through_roundtrip():
    """Top-level id is dropped by the wire format, but nested ids must survive."""
    em = _build_minimal_plant()
    pm_id = em.conceptual_model.id
    sys_id = em.conceptual_model.PipingNetworkSystems[0].id
    seg_id = em.conceptual_model.PipingNetworkSystems[0].Segments[0].id
    valve_id = em.conceptual_model.PipingNetworkSystems[0].Segments[0].Items[0].id

    em2 = xml_io.loads(xml_io.dumps(em))
    pm2 = em2.conceptual_model
    assert pm2.id == pm_id
    assert pm2.PipingNetworkSystems[0].id == sys_id
    assert pm2.PipingNetworkSystems[0].Segments[0].id == seg_id
    assert pm2.PipingNetworkSystems[0].Segments[0].Items[0].id == valve_id


def test_dump_load_dump_byte_identical(tmp_path):
    em = _build_minimal_plant()
    p1 = tmp_path / "first.xml"
    p2 = tmp_path / "second.xml"
    xml_io.dump(em, p1)
    em2 = xml_io.load(p1)
    xml_io.dump(em2, p2)
    assert p1.read_text() == p2.read_text()


# ---------------------------------------------------------------------------
# Reference fixture (informational — limited scope for v1)


def test_official_reference_can_at_least_be_parsed_partially():
    """Sanity: official ``reference_pid.xml`` is well-formed XML and loads as <Model>."""
    text = (
        __import__("pathlib").Path(
            "tests/fixtures/dexpi_2_0/reference_pid.xml"
        ).read_text(encoding="utf-8")
    )
    root = ET.fromstring(text)
    assert root.tag == "Model"
    imports = [c.get("prefix") for c in root if c.tag == "Import"]
    assert "Core" in imports and "Plant" in imports


def test_official_reference_pid_round_trips_structurally():
    """v2 Phase B6: parse → re-emit → re-parse preserves the structural skeleton.

    Counts the core entities (piping systems, tagged items, instrumentation
    functions, diagram presence) and asserts they're identical after a full
    write-and-load cycle. Byte-stable round-trip is gated on canonicalisation
    (Phase F) and the spec/fixture inconsistency around ``model_construct``
    fallback fields (e.g. ``Shape.SymbolRegistrationNumber``); structural
    equivalence is the contract here.
    """
    from pathlib import Path
    text = Path("tests/fixtures/dexpi_2_0/reference_pid.xml").read_text(encoding="utf-8")

    model = xml_io.loads(text)
    pm = model.conceptual_model
    counts_before = (
        len(pm.PipingNetworkSystems),
        len(pm.TaggedPlantItems),
        len(pm.ProcessInstrumentationFunctions),
        model.diagram is not None,
    )
    assert counts_before == (11, 5, 4, True)

    re_emitted = xml_io.dumps(model)
    # Wire-format invariants from the spec
    assert "<References" in re_emitted, "references must round-trip as <References>"
    assert "AggregatedDataValue" in re_emitted, "value types must round-trip"
    assert 'type="Core/PhysicalQuantities.PhysicalQuantity"' in re_emitted, (
        "typed quantities must round-trip"
    )

    model2 = xml_io.loads(re_emitted)
    pm2 = model2.conceptual_model
    counts_after = (
        len(pm2.PipingNetworkSystems),
        len(pm2.TaggedPlantItems),
        len(pm2.ProcessInstrumentationFunctions),
        model2.diagram is not None,
    )
    assert counts_after == counts_before


def test_official_reference_pid_preserves_object_identity_through_references():
    """Spot check: a shared target referenced from multiple places stays one object.

    ``#PlantMetaData1`` is referenced from many ``<References ... property="Object"/>``
    elements in the AttributeRepresentation graph. After parse the reference
    targets must all be the same Python object.
    """
    from pathlib import Path
    text = Path("tests/fixtures/dexpi_2_0/reference_pid.xml").read_text(encoding="utf-8")
    model = xml_io.loads(text)

    # Walk the model gathering every AttributeRepresentation; their .Object
    # field references the same shared target in the fixture (PlantMetaData1).
    # Cycles via reference fields are real (Phase B5); track visited objects.
    seen_targets: list = []
    visited: set[int] = set()

    def walk(o):
        if o is None or id(o) in visited:
            return
        if hasattr(type(o), "model_fields"):
            visited.add(id(o))
            if type(o).__name__ == "AttributeRepresentation":
                try:
                    seen_targets.append(o.Object)
                except AttributeError:
                    pass
            for fn in type(o).model_fields:
                try:
                    v = getattr(o, fn)
                except AttributeError:
                    continue
                if isinstance(v, list):
                    for x in v:
                        walk(x)
                else:
                    walk(v)

    walk(model)
    # AttributeRepresentation references many different metadata objects, but
    # whenever two references carry the same id, the parser must resolve them
    # to the same Python instance.
    assert len(seen_targets) > 100, (
        "fixture should contain many AttributeRepresentation nodes"
    )
    by_id: dict[str, object] = {}
    for t in seen_targets:
        if t is None or not hasattr(type(t), "model_fields"):
            continue
        oid = getattr(t, "id", None)
        if oid is None:
            continue
        prev = by_id.get(oid)
        if prev is None:
            by_id[oid] = t
        else:
            assert prev is t, f"two refs to id={oid!r} resolved to different objects"
    # And at least one id is repeated (otherwise the test isn't exercising shared refs).
    assert any(
        sum(1 for t in seen_targets if getattr(t, "id", None) == oid) > 1
        for oid in by_id
    )
