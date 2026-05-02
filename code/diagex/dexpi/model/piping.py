"""``pp`` namespace — piping classes.

Re-exports every class from :mod:`diagex.dexpi._generated.plant` so legacy
``getattr(pp, "GateValve")`` lookups keep working.
"""
from __future__ import annotations

from diagex.dexpi._generated import plant as _plant

# Diagex extension
from diagex.dexpi.extensions import CustomOperatedValve

_exports = {
    name
    for name, obj in vars(_plant).items()
    if isinstance(obj, type) and obj.__module__ == _plant.__name__
}

for _name in _exports:
    globals().setdefault(_name, getattr(_plant, _name))

__all__ = sorted(_exports | {"CustomOperatedValve"})
