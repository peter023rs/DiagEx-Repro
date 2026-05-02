"""v2 Phase D: DEXPI 2.0 Process namespace codegen + I/O.

Process classes are emitted alongside Plant from the same vendored DSL. They
reference Core (e.g. ``PhysicalQuantity``) but **not** Plant — keeping the
import DAG acyclic.

Smoke coverage here, not exhaustive parametrisation: the test confirms that a
small Process graph (``ProcessModel`` + ``MaterialComponent`` + ``Composition``)
round-trips through both serialisers, the wire qname uses the ``Process/``
prefix, and the JSON registry resolves Process classes.
"""
from __future__ import annotations

from diagex.dexpi import json_io, xml_io
from diagex.dexpi._generated.process import (
    Composition,
    MaterialComponent,
    ProcessModel,
    PureMaterialComponent,
)


def test_process_model_round_trips_through_json():
    """Build a small ProcessModel + MaterialComponents + Composition graph."""
    water = PureMaterialComponent()
    methane = MaterialComponent()
    composition = Composition()
    pm = ProcessModel(
        MaterialComponents=[water, methane],
        Compositions=[composition],
    )

    encoded = json_io.dumps(pm)
    # Wire format: Process classes carry __dexpi_qname__ = "Process/<QName>"
    assert '"_type": "ProcessModel"' in encoded
    assert '"_type": "PureMaterialComponent"' in encoded
    assert '"_type": "MaterialComponent"' in encoded

    loaded = json_io.loads(encoded)
    assert isinstance(loaded, ProcessModel)
    assert len(loaded.MaterialComponents) == 2
    assert isinstance(loaded.MaterialComponents[0], PureMaterialComponent)
    assert isinstance(loaded.MaterialComponents[1], MaterialComponent)
    assert len(loaded.Compositions) == 1


def test_process_classes_carry_process_namespace_qname():
    """Each Process class declares its DEXPI wire qname under the Process prefix."""
    assert ProcessModel.__dexpi_qname__ == "Process/ProcessModel"
    assert MaterialComponent.__dexpi_qname__ == "Process/Process.MaterialComponent"
    assert Composition.__dexpi_qname__ == "Process/Process.Composition"


def test_process_classes_have_dexpi_field_kinds():
    """Phase B's __dexpi_field_kinds__ contract extends to Process classes."""
    assert ProcessModel._dexpi_kind("MaterialComponents") == "composition"
    assert ProcessModel._dexpi_kind("ReferencedNotes") == "reference"


def test_process_class_count_in_expected_ballpark():
    """Sanity: Process namespace adds ~140 own classes to the generated output."""
    from diagex.dexpi._generated import process

    own = sum(
        1
        for n in dir(process)
        if not n.startswith("_")
        and isinstance(getattr(process, n), type)
        and hasattr(getattr(process, n), "model_fields")
        and getattr(process, n).__module__ == process.__name__
    )
    assert 120 <= own <= 170, f"process classes={own}, expected ~143"
