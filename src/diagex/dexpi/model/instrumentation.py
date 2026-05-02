"""``inst`` namespace — instrumentation classes.

Re-exports every class from :mod:`diagex.dexpi._generated.plant` so legacy
``getattr(inst, "ProcessControlFunction")`` lookups keep working. (DEXPI 2.0
co-locates the instrumentation classes inside the Plant module rather than a
separate ``instrumentation`` module like pyDEXPI did.)
"""
from __future__ import annotations

from diagex.dexpi._generated import plant as _plant

_exports = {
    name
    for name, obj in vars(_plant).items()
    if isinstance(obj, type) and obj.__module__ == _plant.__name__
}

for _name in _exports:
    globals().setdefault(_name, getattr(_plant, _name))

__all__ = sorted(_exports)
