"""Namespace re-exports preserving pyDEXPI's import surface.

Allows existing code that does, e.g.::

    from diagex.dexpi.model import equipment as eq
    from diagex.dexpi.model import piping as pp

to be migrated off pyDEXPI with a minimal diff.

Each submodule maps a pyDEXPI module's class names to their DEXPI 2.0
equivalents per the compatibility matrix in
``plan/dexpi-decoupling-phase1-compatibility-matrix.md``. Diagex extensions
(:class:`CustomEquipment`, :class:`CustomOperatedValve`,
:class:`CustomStringAttribute`) live in :mod:`diagex.dexpi.extensions` and are
re-exported through the appropriate namespace.
"""

from diagex.dexpi.model import (  # noqa: F401  (re-exports for `import diagex.dexpi.model as ...`)
    customization,
    dexpiModel,
    equipment,
    instrumentation,
    piping,
    pydantic_classes,
)
