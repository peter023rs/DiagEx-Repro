"""v2 Phase A: typed PhysicalQuantity classes survive JSON + XML round-trip.

Spike A1 found 17 distinct ``BoundDataType<PhysicalQuantity, UnitType=...>``
bindings across the v2.0.0 spec. The codegen (``pydantic_emit.py``) now emits
one ``<UnitFamily>Quantity`` subclass per binding, so fields like
``InsulationThickness`` are typed ``LengthQuantity | None`` rather than the
v1 ``Any | None`` placeholder.

These tests pin the round-trip end-to-end: the value+unit pair must survive
both serialisers, and the type tag on the wire must match the typed subclass.
"""
from __future__ import annotations

from xml.etree import ElementTree as ET

from diagex.dexpi import json_io, xml_io
from diagex.dexpi._generated.core import (
    EngineeringModel,
    LengthQuantity,
    PressureGaugeQuantity,
    VolumeFlowRateQuantity,
)
from diagex.dexpi._generated.enums import (
    LengthUnit,
    PressureGaugeUnit,
    VolumeFlowRateUnit,
)
from diagex.dexpi._generated.plant import (
    OperatedValve,
    PipingNetworkSegment,
    PipingNetworkSystem,
    PlantModel,
    Pump,
    SafetyValveOrFitting,
)


def _model_with_quantities() -> EngineeringModel:
    """A small plant carrying one quantity of each kind we care about."""
    pump = Pump(
        DesignVolumeFlowRate=VolumeFlowRateQuantity(
            Value=12.5, Unit=VolumeFlowRateUnit.MetreCubedPerHour
        ),
    )
    valve = OperatedValve(
        InsulationThickness=LengthQuantity(Value=50.0, Unit=LengthUnit.Millimetre),
    )
    sv = SafetyValveOrFitting(
        SetPressureHigh=PressureGaugeQuantity(Value=10.5, Unit=PressureGaugeUnit.Bar),
        SetPressureLow=PressureGaugeQuantity(Value=8.0, Unit=PressureGaugeUnit.Bar),
    )
    pm = PlantModel(TaggedPlantItems=[pump])
    seg = PipingNetworkSegment(Items=[valve, sv])
    pm.PipingNetworkSystems.append(PipingNetworkSystem(Segments=[seg]))
    return EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )


def test_typed_quantity_classes_share_PhysicalQuantity_base():
    """All 17 ``<X>Quantity`` classes inherit from ``PhysicalQuantity``."""
    from diagex.dexpi._generated import core
    from diagex.dexpi._generated.core import PhysicalQuantity

    quantity_classes = [
        getattr(core, n)
        for n in dir(core)
        if isinstance(getattr(core, n), type)
        and getattr(core, n) is not PhysicalQuantity
        and issubclass(getattr(core, n), PhysicalQuantity)
    ]
    assert len(quantity_classes) == 17, (
        f"expected 17 typed quantity subclasses, got {len(quantity_classes)}"
    )
    for cls in quantity_classes:
        # All carry Value: float and a typed Unit field.
        assert "Value" in cls.model_fields
        assert "Unit" in cls.model_fields


def test_typed_quantity_field_annotation():
    """Bound fields on plant classes pick up the typed quantity, not ``Any``."""
    assert (
        Pump.model_fields["DesignVolumeFlowRate"].annotation
        == VolumeFlowRateQuantity | None
    )
    assert (
        OperatedValve.model_fields["InsulationThickness"].annotation
        == LengthQuantity | None
    )
    assert (
        SafetyValveOrFitting.model_fields["SetPressureHigh"].annotation
        == PressureGaugeQuantity | None
    )


def test_quantity_roundtrip_through_json(tmp_path):
    model = _model_with_quantities()
    path = tmp_path / "model.dexpi.json"
    json_io.dump(model, path)
    loaded = json_io.load(path)

    seg = loaded.conceptual_model.PipingNetworkSystems[0].Segments[0]
    valve, sv = seg.Items
    pump = loaded.conceptual_model.TaggedPlantItems[0]

    assert isinstance(valve.InsulationThickness, LengthQuantity)
    assert valve.InsulationThickness.Value == 50.0
    assert valve.InsulationThickness.Unit == LengthUnit.Millimetre

    assert isinstance(sv.SetPressureHigh, PressureGaugeQuantity)
    assert sv.SetPressureHigh.Value == 10.5
    assert sv.SetPressureHigh.Unit == PressureGaugeUnit.Bar
    assert sv.SetPressureLow.Value == 8.0

    assert isinstance(pump.DesignVolumeFlowRate, VolumeFlowRateQuantity)
    assert pump.DesignVolumeFlowRate.Value == 12.5
    assert pump.DesignVolumeFlowRate.Unit == VolumeFlowRateUnit.MetreCubedPerHour


def test_quantity_roundtrip_through_xml():
    model = _model_with_quantities()
    xml_text = xml_io.dumps(model)

    # Wire format: each typed quantity is an <AggregatedDataValue> with the
    # PhysicalQuantity qname, carrying <Data property="Value"><Double>... and
    # <Data property="Unit"><DataReference data="<EnumQname>.<Literal>"/>.
    assert "AggregatedDataValue" in xml_text
    assert 'type="Core/PhysicalQuantities.PhysicalQuantity"' in xml_text
    assert 'data="Core/PhysicalQuantities.LengthUnit.Millimetre"' in xml_text
    assert 'data="Core/PhysicalQuantities.PressureGaugeUnit.Bar"' in xml_text

    # Round-trip
    loaded = xml_io.loads(xml_text)
    seg = loaded.conceptual_model.PipingNetworkSystems[0].Segments[0]
    valve, sv = seg.Items
    pump = loaded.conceptual_model.TaggedPlantItems[0]

    # XML emits the bare PhysicalQuantity wire type, so on parse we get the
    # base class — Value+Unit must still match.
    assert valve.InsulationThickness.Value == 50.0
    assert valve.InsulationThickness.Unit == LengthUnit.Millimetre
    assert sv.SetPressureHigh.Value == 10.5
    assert sv.SetPressureLow.Value == 8.0
    assert pump.DesignVolumeFlowRate.Value == 12.5
    assert pump.DesignVolumeFlowRate.Unit == VolumeFlowRateUnit.MetreCubedPerHour


def test_xml_emits_value_and_unit_under_data_elements():
    """Spec wire format: the value object's Value + Unit live under <Data> children."""
    valve = OperatedValve(
        InsulationThickness=LengthQuantity(Value=42.0, Unit=LengthUnit.Inch)
    )
    pm = PlantModel(
        PipingNetworkSystems=[
            PipingNetworkSystem(Segments=[PipingNetworkSegment(Items=[valve])])
        ]
    )
    model = EngineeringModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )
    xml_text = xml_io.dumps(model)

    root = ET.fromstring(xml_text)
    adv = root.find(".//AggregatedDataValue")
    assert adv is not None, "no AggregatedDataValue emitted"
    data_props = {d.get("property") for d in adv.findall("Data")}
    assert {"Value", "Unit"}.issubset(data_props)
