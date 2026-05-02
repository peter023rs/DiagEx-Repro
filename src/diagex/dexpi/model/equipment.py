"""``eq`` namespace — equipment classes.

Re-exports every class from :mod:`diagex.dexpi._generated.plant` so legacy
``getattr(eq, "Tank")`` lookups keep working. pyDEXPI's ``Equipment`` is the
abstract base for all equipment items; in DEXPI 2.0 this role is played by
``Plant.ProcessEquipment.ProcessEquipment``, re-exported under both names.
"""
from __future__ import annotations

from diagex.dexpi._generated import plant as _plant
from diagex.dexpi._generated.plant import ProcessEquipment

# Diagex extension
from diagex.dexpi.extensions import CustomEquipment

# Legacy pyDEXPI alias.
Equipment = ProcessEquipment

# Re-export every class defined in the generated plant module so callers can
# do ``getattr(eq, "<ClassName>")`` for every equipment subclass. We
# deliberately bind names directly into module globals (rather than star-import)
# so static analysis can still see the namespace.
_exports = {
    name
    for name, obj in vars(_plant).items()
    if isinstance(obj, type) and obj.__module__ == _plant.__name__
}

for _name in _exports:
    globals().setdefault(_name, getattr(_plant, _name))

__all__ = sorted(_exports | {"Equipment", "ProcessEquipment", "CustomEquipment"})
