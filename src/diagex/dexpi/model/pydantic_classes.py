"""``pc`` namespace — DEXPI value types and metadata wrappers.

In pyDEXPI these all lived in a single ``pydantic_classes`` module; in DEXPI
2.0 they're spread across :mod:`Core.DataTypes` (value types) and
:mod:`Core.Diagram` (MetaData). We re-export the union here under the legacy
``pc`` alias.
"""
from __future__ import annotations

from diagex.dexpi._generated.core import (
    MetaData,
    MultiLanguageString,
    SingleLanguageString,
)

__all__ = ["MetaData", "MultiLanguageString", "SingleLanguageString"]
