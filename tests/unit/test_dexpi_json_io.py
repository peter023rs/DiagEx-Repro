"""Phase 3 acceptance tests: ``diagex.dexpi.json_io`` round-trip + identity."""
from __future__ import annotations

import json

import pytest

from diagex.dexpi import json_io
from diagex.dexpi._generated.core import (
    EngineeringModel,
    MultiLanguageString,
    SingleLanguageString,
)
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


# ---------------------------------------------------------------------------
# Fixtures


def _build_minimal_plant() -> EngineeringModel:
    """Tree-only plant: one equipment, one piping network."""
    pump = CustomEquipment(typeName="centrifugal-pump")
    pump.customAttributes.append(CustomStringAttribute(name="confidence", value="0.92"))

    valve = CustomOperatedValve(typeName="check-valve")
    seg = PipingNetworkSegment(Items=[valve])
    sys_ = PipingNetworkSystem(Segments=[seg])

    pm = PlantModel()
    pm.PipingNetworkSystems.append(sys_)
    pm.TaggedPlantItems.append(pump)

    return EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )


# ---------------------------------------------------------------------------
# Format envelope


def test_format_envelope():
    em = _build_minimal_plant()
    data = json.loads(json_io.dumps(em))
    assert data["_diagex_format"] == "1"
    assert data["_dexpi_version"] == "2.0.0"
    assert "model" in data
    assert data["model"]["_type"] == "EngineeringModel"


def test_unsupported_format_raises():
    with pytest.raises(json_io.FormatVersionError):
        json_io.loads('{"_diagex_format": "0.9", "model": {}}')


def test_missing_model_raises():
    with pytest.raises(json_io.DiagexJsonError):
        json_io.loads('{"_diagex_format": "1"}')


# ---------------------------------------------------------------------------
# Polymorphic type tags


def test_each_entity_carries_type_tag():
    em = _build_minimal_plant()
    data = json.loads(json_io.dumps(em))
    body = data["model"]
    assert body["_type"] == "EngineeringModel"
    cm = body["ConceptualModel"]
    assert cm["_type"] == "PlantModel"
    pump = cm["TaggedPlantItems"][0]
    assert pump["_type"] == "CustomEquipment"
    seg = cm["PipingNetworkSystems"][0]["Segments"][0]
    assert seg["_type"] == "PipingNetworkSegment"
    valve = seg["Items"][0]
    assert valve["_type"] == "CustomOperatedValve"


def test_unknown_type_raises():
    payload = {
        "_diagex_format": "1",
        "_dexpi_version": "2.0.0",
        "model": {"_type": "DoesNotExist", "id": "x"},
    }
    with pytest.raises(json_io.UnknownTypeError):
        json_io.loads(json.dumps(payload))


# ---------------------------------------------------------------------------
# Round-trip


def test_tree_roundtrip_preserves_ids():
    em = _build_minimal_plant()
    text = json_io.dumps(em)
    em2 = json_io.loads(text)

    assert isinstance(em2, EngineeringModel)
    assert em2.id == em.id
    pm2 = em2.conceptual_model
    assert isinstance(pm2, PlantModel)
    assert pm2.id == em.conceptual_model.id

    pump2 = pm2.TaggedPlantItems[0]
    assert isinstance(pump2, CustomEquipment)
    assert pump2.typeName == "centrifugal-pump"
    assert pump2.id == em.conceptual_model.TaggedPlantItems[0].id


def test_dump_load_dump_byte_identical(tmp_path):
    em = _build_minimal_plant()
    p1 = tmp_path / "first.json"
    p2 = tmp_path / "second.json"
    json_io.dump(em, p1)
    em2 = json_io.load(p1)
    json_io.dump(em2, p2)
    assert p1.read_text() == p2.read_text()


def test_custom_attributes_survive_roundtrip():
    em = _build_minimal_plant()
    em2 = json_io.loads(json_io.dumps(em))

    pump = em2.conceptual_model.TaggedPlantItems[0]
    assert len(pump.customAttributes) == 1
    # Pydantic deserializes the dict shape; the round-tripped object may be
    # a dict-like CustomStringAttribute. Either way the data is preserved.
    ca = pump.customAttributes[0]
    if isinstance(ca, CustomStringAttribute):
        assert ca.name == "confidence" and ca.value == "0.92"
    else:
        # If pydantic kept it as dict (because field type is `list`), that's fine
        assert ca["name"] == "confidence" and ca["value"] == "0.92"


# ---------------------------------------------------------------------------
# Cross-reference handling


def test_shared_reference_emitted_as_ref():
    """If the same entity appears under two parents, the second is `$ref`."""
    pump = CustomEquipment(typeName="P1")
    # Reference the SAME object from two parents: PlantModel.TaggedPlantItems
    # and customAttributes (via a hand-built duplication).
    pm = PlantModel(TaggedPlantItems=[pump])

    # Wedge the same pump into a second list (abusing customAttributes which
    # is `list[Any]`) to create a shared reference.
    pump_via_attr = pump
    em = EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    em.customAttributes.append(pump_via_attr)

    text = json_io.dumps(em)
    # Count occurrences of the pump's full body (with `_type`+`id`) vs `$ref`
    assert text.count(f'"{pump.id}"') >= 2  # appears at least twice in JSON
    assert '"$ref"' in text


def test_shared_reference_roundtrip_preserves_object_identity():
    pump = CustomEquipment(typeName="P1")
    pm = PlantModel(TaggedPlantItems=[pump])
    em = EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    em.customAttributes.append(pump)

    em2 = json_io.loads(json_io.dumps(em))
    pm2 = em2.conceptual_model
    pump_from_pm = pm2.TaggedPlantItems[0]
    pump_from_attr = em2.customAttributes[0]
    # Object identity preserved across the two pointers
    assert pump_from_pm is pump_from_attr


def test_dangling_ref_raises():
    payload = {
        "_diagex_format": "1",
        "_dexpi_version": "2.0.0",
        "model": {"_type": "PlantModel", "id": "p1",
                  "TaggedPlantItems": [{"$ref": "missing"}]},
    }
    with pytest.raises(json_io.IncompleteRefError):
        json_io.loads(json.dumps(payload))


def test_duplicate_id_raises():
    """Two distinct entity bodies with the same id is a hard error."""
    payload = {
        "_diagex_format": "1",
        "_dexpi_version": "2.0.0",
        "model": {
            "_type": "PlantModel",
            "id": "p1",
            "TaggedPlantItems": [
                {"_type": "CustomEquipment", "id": "x", "typeName": "a"},
                {"_type": "CustomEquipment", "id": "x", "typeName": "b"},
            ],
        },
    }
    with pytest.raises(json_io.DuplicateIdError):
        json_io.loads(json.dumps(payload))


# ---------------------------------------------------------------------------
# Identity preservation


def test_load_does_not_regenerate_ids():
    """Loaded entities must keep their JSON ids exactly; no UUID regeneration."""
    em = _build_minimal_plant()
    original_ids = {
        em.id,
        em.conceptual_model.id,
        em.conceptual_model.TaggedPlantItems[0].id,
        em.conceptual_model.PipingNetworkSystems[0].id,
        em.conceptual_model.PipingNetworkSystems[0].Segments[0].id,
        em.conceptual_model.PipingNetworkSystems[0].Segments[0].Items[0].id,
    }
    em2 = json_io.loads(json_io.dumps(em))
    loaded_ids = {
        em2.id,
        em2.conceptual_model.id,
        em2.conceptual_model.TaggedPlantItems[0].id,
        em2.conceptual_model.PipingNetworkSystems[0].id,
        em2.conceptual_model.PipingNetworkSystems[0].Segments[0].id,
        em2.conceptual_model.PipingNetworkSystems[0].Segments[0].Items[0].id,
    }
    assert original_ids == loaded_ids


# ---------------------------------------------------------------------------
# Value types


def test_value_types_have_no_id_in_json():
    sls = SingleLanguageString(Language="en", Value="hello")
    text = json_io.dumps(MultiLanguageString(SingleLanguageStrings=[sls]))
    data = json.loads(text)
    body = data["model"]
    assert body["_type"] == "MultiLanguageString"
    inner = body["SingleLanguageStrings"][0]
    assert inner["_type"] == "SingleLanguageString"
    assert "id" not in inner  # value type carries no entity id
