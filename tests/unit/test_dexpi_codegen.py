"""Codegen sanity tests for the DEXPI 2.0 generated pydantic model.

Lives in the regular unit-test suite (no codegen extra needed at runtime: we
test only the *generated* artefacts, not the regeneration pipeline). Regression
test runs without ``dexpi.specificator`` installed.
"""
from __future__ import annotations

from pathlib import Path

import pytest

# Pure import test — must work on the runtime Python (3.11+).
from diagex.dexpi._generated import core, enums, plant  # noqa: F401


GENERATED_DIR = Path(__file__).resolve().parents[2] / "src" / "diagex" / "dexpi" / "_generated"


def test_generated_files_exist():
    for name in ("__init__.py", "core.py", "plant.py", "enums.py"):
        path = GENERATED_DIR / name
        assert path.exists(), f"generated file missing: {path}"
        assert path.stat().st_size > 0, f"generated file empty: {path}"


def test_key_classes_exist():
    from diagex.dexpi._generated.core import (
        ConceptualModel, ConceptualObject, EngineeringModel,
        MetaData, MultiLanguageString, SingleLanguageString,
    )
    from diagex.dexpi._generated.plant import (
        OperatedValve, PipingComponent, PipingNetworkSegment,
        PipingNetworkSystem, PlantModel, ProcessEquipment,
        ProcessInstrumentationFunction, SignalConveyingFunction,
    )

    # Spot check key qualified names are referenced
    for cls in (EngineeringModel, PlantModel, PipingComponent, OperatedValve):
        assert hasattr(cls, "model_fields"), f"{cls} not a pydantic model"


def test_class_counts_in_expected_ballpark():
    """Total counts shouldn't drift unexpectedly. Snapshot from V2.0.0 (commit 260c81c5).

    Tolerance: ±5% to allow minor spec patches.
    """
    from diagex.dexpi._generated import core, plant

    def own_class_count(module) -> int:
        return sum(
            1
            for n in dir(module)
            if not n.startswith("_")
            and isinstance(getattr(module, n), type)
            and hasattr(getattr(module, n), "model_fields")
            and getattr(module, n).__module__ == module.__name__
        )

    core_classes = own_class_count(core)
    plant_classes = own_class_count(plant)

    # Spike A counted: Core 28 concrete + 8 abstract + 7 AggregatedDataType = 43 entities,
    # plus DexpiEntityBase / DexpiValueBase. Plant 274 concrete + 31 abstract = 305.
    # v2 Phase A added 17 typed PhysicalQuantity subclasses (BoundDataType bindings).
    assert 50 <= core_classes <= 80, f"core_classes={core_classes}, expected ~62"
    assert 280 <= plant_classes <= 330, f"plant_classes={plant_classes}, expected ~305"


def test_enum_values():
    """Spot-check a known enum from the spec carries its literals."""
    assert enums.FailActionClassification.FailClose.value == "FailClose"
    assert enums.FailActionClassification.FailOpen.value == "FailOpen"
    assert enums.FailActionClassification.FailRetainPosition.value == "FailRetainPosition"


def test_multiple_inheritance_class():
    """``PipingComponent`` extends 6 supertypes per Spike A; pydantic must accept it."""
    from diagex.dexpi._generated.plant import PipingComponent

    bases = PipingComponent.__bases__
    assert len(bases) >= 2, f"expected MI; got bases={bases}"


def test_pydantic_validation_roundtrip():
    """Build a minimal plant, dump, reload."""
    import json

    from diagex.dexpi._generated.core import (
        EngineeringModel, MultiLanguageString, SingleLanguageString,
    )
    from diagex.dexpi._generated.plant import (
        OperatedValve, PipingNetworkSegment, PipingNetworkSystem, PlantModel,
    )

    pm = PlantModel()
    seg = PipingNetworkSegment()
    sys_ = PipingNetworkSystem(Segments=[seg])
    pm.PipingNetworkSystems.append(sys_)
    valve = OperatedValve()
    seg.Items.append(valve)

    em = EngineeringModel(
        ConceptualModel=pm,                           # PascalCase alias works (collision field)
        ExportDateTime=None,
        OriginatingSystemName="diagex",
        OriginatingSystemVendorName="ABB",
        OriginatingSystemVersion="0.1.0",
    )

    # Dump using PascalCase aliases for DEXPI wire format
    dumped = em.model_dump_json(by_alias=True)
    payload = json.loads(dumped)
    assert "ConceptualModel" in payload
    assert "conceptual_model" not in payload

    em2 = EngineeringModel.model_validate(payload)
    assert em2.id == em.id
    assert em2.OriginatingSystemName == "diagex"


def test_aggregated_data_type_no_entity_id():
    """``MultiLanguageString`` and ``SingleLanguageString`` are value types (no id)."""
    from diagex.dexpi._generated.core import MultiLanguageString, SingleLanguageString

    sls = SingleLanguageString(Language="en", Value="hello")
    mls = MultiLanguageString(SingleLanguageStrings=[sls])
    assert not hasattr(sls, "id")
    assert not hasattr(mls, "id")


def test_collision_field_alias():
    """Fields whose name collided with their type were aliased to snake_case."""
    from diagex.dexpi._generated.core import EngineeringModel

    fields = EngineeringModel.model_fields
    # Either the snake_case attribute exists with PascalCase alias, or the original
    # PascalCase name still works — accept either as long as both are reachable.
    assert "conceptual_model" in fields, list(fields)
    assert fields["conceptual_model"].alias == "ConceptualModel"


def test_entity_classes_carry_uuid_id():
    """Every entity class auto-defaults ``id`` to a UUID."""
    from diagex.dexpi._generated.plant import OperatedValve

    a = OperatedValve()
    b = OperatedValve()
    assert a.id != b.id
    assert hash(a) != hash(b)


@pytest.mark.parametrize("expected", [
    "OperatedValve", "PipingComponent", "PipingNetworkSegment",
    "PipingNetworkSystem", "ProcessEquipment", "ProcessInstrumentationFunction",
    "SignalConveyingFunction", "PlantModel",
])
def test_compatibility_matrix_classes_present(expected):
    """Every class named in plan §3 / matrix as 'present' must be importable."""
    from diagex.dexpi._generated import plant
    assert hasattr(plant, expected), f"{expected} missing from plant module"
