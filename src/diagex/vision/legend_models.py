"""Legend data models shared across Phase 2 extractors (spec §7.2.2).

A `LegendEntry` is the atomic unit — one symbol with its label, class, and
optional image bytes. A `LegendPack` is the serialised collection that the
legend cache reads/writes to disk, keyed on the source plus an extractor
fingerprint so input, model, prompt-contract, and schema changes can force
re-extraction.
"""

from __future__ import annotations

import base64
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from diagex.dexpi_schema import (
    EQUIPMENT_CLASS_KEYS,
    EQUIPMENT_CLASS_ROUTER_VALVE_KEY,
    INSTRUMENT_FUNCTION_KEYS,
    VALVE_TYPE_KEYS,
)
from diagex.vision.models import BBox, SourceView

SymbolStandard = Literal["isa-5.1", "iso-10628", "sama", "none"]
LEGEND_CACHE_SCHEMA_VERSION = "0.2.0"


# DEXPI subset (spec §7.2.1) — the vocabulary the DexpiBuilder maps into.
# Sourced from :mod:`diagex.dexpi_schema` so the registry is the single source
# of truth; legend validation stays consistent with the phase-2 prompt and
# the DexpiBuilder dispatch table. The "valve" router key is surfaced here
# because legend entries are allowed to name it as an equipment_class
# (actuated valves drawn body-on-line); the phase-2 annotate schema routes
# valves via ``valve_type`` instead.
EquipmentClass = Literal[  # type: ignore[valid-type]
    EQUIPMENT_CLASS_KEYS + (EQUIPMENT_CLASS_ROUTER_VALVE_KEY,)  # noqa: F821
]

ValveType = Literal[VALVE_TYPE_KEYS]  # type: ignore[valid-type]  # noqa: F821

InstrumentFunction = Literal[INSTRUMENT_FUNCTION_KEYS]  # type: ignore[valid-type]  # noqa: F821


class LegendEntry(BaseModel):
    """One (label, class, optional image) triple extracted from a legend or a built-in library."""

    label: str                                   # agent-facing name, e.g. "FIC", "butterfly valve"
    description: str | None = None               # short human gloss
    symbol_class: str                            # entry in the DEXPI/ISA vocabulary (§7.2.1)
    kind: Literal["equipment", "instrument", "line", "valve", "connector", "other"] = "other"
    standard: SymbolStandard | None = None       # "isa-5.1" etc.; None for customer-extracted
    image_b64: str | None = None                 # optional PNG bytes, base64; None means text-only
    attributes: dict[str, str] = Field(default_factory=dict)
    source: Literal["built_in", "legend_extracted", "customer_override"] = "built_in"
    # Audit data for project-extracted thumbnails.  These fields intentionally
    # survive cache serialization so a human can trace an image back to the
    # page coordinates that produced it and future code can recrop it.
    source_page_index: int | None = None
    source_bbox: BBox | None = None
    source_label_bbox: BBox | None = None
    source_view: SourceView | None = None
    crop_method: Literal["model_bbox", "native_text_paths"] | None = None
    crop_quality: Literal[
        "accepted",
        "recovered",
        "omitted_abbreviation",
        "rejected_blank",
        "rejected_text_overlap",
        "rejected_duplicate",
        "unavailable",
    ] | None = None

    def image_bytes(self) -> bytes | None:
        if not self.image_b64:
            return None
        return base64.b64decode(self.image_b64)


class LegendPack(BaseModel):
    """A bundle of legend entries + metadata; what the cache serialises."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    schema_version: str = LEGEND_CACHE_SCHEMA_VERSION
    source_hash: str = ""                        # sha256 of the source bytes (§7.2.2)
    # Includes the extraction implementation, prompt contract, and model.
    # A matching source PDF alone is not sufficient to trust old crops.
    extractor_fingerprint: str = ""
    source_ref: str = ""                         # "<stem>#pages=1,2" or "file:legend.pdf"
    standard: SymbolStandard = "isa-5.1"
    entries: list[LegendEntry] = Field(default_factory=list)
    notes: str = ""

    def merge(self, other: LegendPack) -> LegendPack:
        """Return a new pack: `self` wins on label collisions (§7.2.2 built_in * extracted).

        Per spec: when built-in and extracted disagree, extracted wins. Callers
        pass `extracted.merge(built_in)` for that direction; callers building a
        presentation order call with the opposite order and use `LegendPack`
        purely for transport.
        """
        seen: set[str] = {e.label.strip().lower() for e in self.entries}
        merged = list(self.entries)
        for e in other.entries:
            if e.label.strip().lower() in seen:
                continue
            merged.append(e)
        return LegendPack(
            schema_version=self.schema_version,
            source_hash=self.source_hash,
            extractor_fingerprint=self.extractor_fingerprint,
            source_ref=self.source_ref,
            standard=self.standard,
            entries=merged,
            notes=(self.notes + (" | " if self.notes and other.notes else "") + other.notes).strip(" |"),
        )


class LegendBudget(BaseModel):
    """Split of entries into cached few-shot vs lookup-tool fallback (spec §7.2.2)."""

    few_shot: list[LegendEntry] = Field(default_factory=list)
    lookup_only: list[LegendEntry] = Field(default_factory=list)
    budget_tokens: int = 0                       # target ceiling for few_shot tokens
    used_tokens: int = 0                         # rough estimate ≈ sum of entry costs
