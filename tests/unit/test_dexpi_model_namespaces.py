"""Phase 2 acceptance: ``diagex.dexpi.model`` exposes pyDEXPI's import surface.

Validates the compatibility-matrix mapping by importing every name listed in
plan §3 through the legacy-shaped namespaces (``eq``, ``inst``, ``pp``, ``cu``,
``pc``, ``dm``).
"""
from __future__ import annotations

import pytest


def test_legacy_pydexpi_import_shape_works():
    """Recreate the exact import lines from ``src/diagex/extractors/dexpi_builder.py``."""
    from diagex.dexpi.model import customization as cu  # noqa: F401
    from diagex.dexpi.model import dexpiModel as dm  # noqa: F401
    from diagex.dexpi.model import equipment as eq  # noqa: F401
    from diagex.dexpi.model import instrumentation as inst  # noqa: F401
    from diagex.dexpi.model import piping as pp  # noqa: F401
    from diagex.dexpi.model import pydantic_classes as pc  # noqa: F401


@pytest.mark.parametrize(
    "ns,name",
    [
        ("dexpiModel", "ConceptualModel"),
        ("dexpiModel", "DexpiModel"),
        ("dexpiModel", "EngineeringModel"),
        ("equipment", "Equipment"),  # alias for ProcessEquipment
        ("equipment", "ProcessEquipment"),
        ("equipment", "CustomEquipment"),
        ("instrumentation", "ProcessControlFunction"),
        ("instrumentation", "ProcessInstrumentationFunction"),
        ("instrumentation", "SignalConveyingFunction"),
        ("piping", "CustomOperatedValve"),
        ("piping", "OperatedValve"),
        ("piping", "PipingComponent"),
        ("piping", "PipingNetworkSegment"),
        ("piping", "PipingNetworkSystem"),
        ("piping", "FlowInPipeOffPageConnector"),
        ("piping", "FlowOutPipeOffPageConnector"),
        ("piping", "PipingNode"),
        ("pydantic_classes", "MetaData"),
        ("pydantic_classes", "MultiLanguageString"),
        ("pydantic_classes", "SingleLanguageString"),
        ("customization", "CustomStringAttribute"),
    ],
)
def test_namespace_member_present(ns, name):
    """Each (namespace, name) pair listed in plan §3 must resolve to a class."""
    import importlib

    mod = importlib.import_module(f"diagex.dexpi.model.{ns}")
    assert hasattr(mod, name), f"diagex.dexpi.model.{ns}.{name} is missing"
    obj = getattr(mod, name)
    assert isinstance(obj, type), f"{ns}.{name} is not a class: {obj!r}"


def test_dexpi_model_alias_resolves_to_engineering_model():
    """``dm.DexpiModel`` is an alias for the DEXPI 2.0 ``EngineeringModel``."""
    from diagex.dexpi.model import dexpiModel as dm

    assert dm.DexpiModel is dm.EngineeringModel
    assert dm.DexpiModel.__name__ == "EngineeringModel"


def test_equipment_alias_resolves_to_process_equipment():
    """``eq.Equipment`` is an alias for the DEXPI 2.0 ``ProcessEquipment`` abstract base."""
    from diagex.dexpi.model import equipment as eq

    assert eq.Equipment is eq.ProcessEquipment
    assert eq.Equipment.__name__ == "ProcessEquipment"


def test_can_build_a_full_plant_through_namespace_layer():
    """Smoke test the full pyDEXPI-style construction path.

    Note: this test asserts only direct-construction parity. Polymorphic
    JSON round-trip (concrete subclass surviving deserialization) is a
    Phase 3 concern handled by ``json_io.py``; this Phase 2 test predates it.
    """
    from diagex.dexpi._generated.plant import PlantModel
    from diagex.dexpi.model import customization as cu
    from diagex.dexpi.model import dexpiModel as dm
    from diagex.dexpi.model import equipment as eq
    from diagex.dexpi.model import piping as pp

    pump = eq.CustomEquipment(typeName="centrifugal-pump")
    pump.customAttributes.append(cu.CustomStringAttribute(name="confidence", value="0.92"))

    valve = pp.CustomOperatedValve(typeName="check-valve")

    seg = pp.PipingNetworkSegment(Items=[valve])
    sys_ = pp.PipingNetworkSystem(Segments=[seg])

    pm = PlantModel()
    pm.PipingNetworkSystems.append(sys_)
    pm.TaggedPlantItems.append(pump)

    em = dm.DexpiModel(
        ConceptualModel=pm,
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )

    # Direct-construction assertions (no round-trip)
    assert em.OriginatingSystemName == "diagex"
    assert em.conceptual_model is pm
    assert len(pm.TaggedPlantItems) == 1
    assert pm.TaggedPlantItems[0].customAttributes[0].name == "confidence"
    assert len(pm.PipingNetworkSystems[0].Segments[0].Items) == 1
    assert pm.PipingNetworkSystems[0].Segments[0].Items[0].typeName == "check-valve"
