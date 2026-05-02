"""Diagex extensions to the generated DEXPI 2.0 model.

These classes are **not** part of the DEXPI 2.0 specification. They are diagex
additions that mirror the equivalent extensions pyDEXPI shipped (which we are
replacing). They live outside ``_generated/`` because they are hand-written and
must not be overwritten by codegen.

- :class:`CustomEquipment` (deprecated v2 Phase C) — kept loadable so v1 JSON
  artefacts in ``runs/`` still parse, but the builder no longer emits it.
- :class:`CustomOperatedValve` (deprecated v2 Phase C) — same treatment.
- :class:`CustomStringAttribute` — still in active use; carries LLM hints in
  the diagex-internal ``customAttributes`` list. Preserved by the JSON writer,
  dropped by the XML writer.

v2 Phase C migrated the builder so unrecognised LLM names fall back to the
nearest concrete DEXPI ancestor (``ProcessEquipment`` / ``OperatedValve``) and
the original LLM string lives on ``customAttributes``. The ``Custom*`` classes
remain importable but emit a ``DeprecationWarning`` on construction; planned
removal: v3.
"""

from __future__ import annotations

import warnings
from typing import Any

from pydantic import BaseModel, ConfigDict

from diagex.dexpi._generated.plant import OperatedValve, ProcessEquipment


_DEPRECATION_MSG = (
    "{name} is deprecated since v2 Phase C; the builder now falls back to "
    "{replacement} and stores the original LLM type-name on "
    "customAttributes['agent_{kind}']. Planned removal: v3."
)


class CustomEquipment(ProcessEquipment):
    """Equipment whose specific DEXPI subclass could not be determined.

    Deprecated v2 Phase C: prefer ``ProcessEquipment`` with an
    ``agent_equipment_class`` custom attribute carrying the LLM-supplied label.
    Kept loadable so v1 JSON artefacts in ``runs/`` continue to parse.
    """

    typeName: str

    def __init__(self, **data: Any) -> None:
        warnings.warn(
            _DEPRECATION_MSG.format(
                name="CustomEquipment",
                replacement="ProcessEquipment",
                kind="equipment_class",
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class CustomOperatedValve(OperatedValve):
    """Operated valve whose specific DEXPI valve subclass could not be determined.

    Deprecated v2 Phase C: prefer ``OperatedValve`` with an ``agent_valve_type``
    custom attribute. Kept loadable for v1 JSON compatibility.
    """

    typeName: str

    def __init__(self, **data: Any) -> None:
        warnings.warn(
            _DEPRECATION_MSG.format(
                name="CustomOperatedValve",
                replacement="OperatedValve",
                kind="valve_type",
            ),
            DeprecationWarning,
            stacklevel=2,
        )
        super().__init__(**data)


class CustomStringAttribute(BaseModel):
    """A ``(name, value)`` pair used in diagex-internal ``customAttributes`` lists.

    Carries LLM-extracted hints that don't map onto a typed DEXPI 2.0 property.
    DEXPI 2.0 has no free-form attribute-bag mechanism (compatibility matrix
    §4); diagex retains custom attributes in its native JSON output but skips
    them on DEXPI XML emit.
    """

    model_config = ConfigDict(validate_assignment=True)
    name: str
    value: str
