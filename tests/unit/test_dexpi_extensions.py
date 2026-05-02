"""Tests for the diagex extensions to the generated DEXPI 2.0 model."""
from __future__ import annotations


def test_custom_equipment_is_subclass_of_process_equipment():
    from diagex.dexpi._generated.plant import ProcessEquipment
    from diagex.dexpi.extensions import CustomEquipment

    assert issubclass(CustomEquipment, ProcessEquipment)
    ce = CustomEquipment(typeName="centrifugal-pump")
    assert ce.typeName == "centrifugal-pump"
    # Inherits entity boilerplate
    assert isinstance(ce.id, str) and len(ce.id) >= 32
    assert ce.customAttributes == []


def test_custom_operated_valve_is_subclass_of_operated_valve():
    from diagex.dexpi._generated.plant import OperatedValve
    from diagex.dexpi.extensions import CustomOperatedValve

    assert issubclass(CustomOperatedValve, OperatedValve)
    cov = CustomOperatedValve(typeName="check-valve")
    assert cov.typeName == "check-valve"
    assert isinstance(cov.id, str)


def test_custom_string_attribute_is_simple_pair():
    from diagex.dexpi.extensions import CustomStringAttribute

    a = CustomStringAttribute(name="source", value="LLM")
    assert a.name == "source"
    assert a.value == "LLM"
    # Value type — no entity id, no hash boilerplate
    assert not hasattr(a, "id")


def test_custom_attributes_survives_on_entity():
    from diagex.dexpi._generated.plant import OperatedValve
    from diagex.dexpi.extensions import CustomStringAttribute

    v = OperatedValve()
    a = CustomStringAttribute(name="extracted_by", value="GPT-4.1")
    b = CustomStringAttribute(name="confidence", value="0.92")
    v.customAttributes.append(a)
    v.customAttributes.append(b)

    assert len(v.customAttributes) == 2
    assert v.customAttributes[0].name == "extracted_by"


def test_custom_equipment_serializes_to_json_with_type_name():
    """``typeName`` must round-trip through JSON to support the diagex JSON output."""
    import json

    from diagex.dexpi.extensions import CustomEquipment

    ce = CustomEquipment(typeName="reactor-with-jacket")
    payload = json.loads(ce.model_dump_json(by_alias=True))
    assert payload["typeName"] == "reactor-with-jacket"
    # Round-trip
    ce2 = CustomEquipment.model_validate(payload)
    assert ce2.id == ce.id
    assert ce2.typeName == "reactor-with-jacket"
