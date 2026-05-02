"""``dm`` namespace — top-level DEXPI model wrappers.

pyDEXPI's ``DexpiModel`` is renamed to ``EngineeringModel`` in DEXPI 2.0.
``ConceptualModel`` survives as the base; the equipment / piping containers
have moved to ``PlantModel`` (its plant-domain subclass).
"""
from __future__ import annotations

from diagex.dexpi._generated.core import ConceptualModel, EngineeringModel
from diagex.dexpi._generated.plant import PlantModel

# Legacy pyDEXPI alias.
DexpiModel = EngineeringModel

__all__ = ["ConceptualModel", "DexpiModel", "EngineeringModel", "PlantModel"]
