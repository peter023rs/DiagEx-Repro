"""DEXPI 2.0 validation — XSD envelope check + semantic rule pack.

Two layers:

- :func:`xsd_validate` — wraps the official ``DEXPI_XML_Schema.xsd`` (vendored
  under ``codegen/vendored/``) via the optional ``xmlschema`` PyPI package.
  Reports element-level violations (missing required attributes, wrong child
  ordering, malformed identifiers).
- :func:`semantic_validate` — pure-Python checks against an in-memory model
  graph (post-parse). Catches things the XSD can't: orphaned references,
  unmapped tag formats, missing mandatory metadata, etc.

Each rule has a stable ID (``DEX0001`` …), a severity (``error`` / ``warning``),
and a single sentence describing the rationale. The CLI emits issues sorted by
``(path, rule_id)`` so the output diffs cleanly across runs.

Adding rules: append a callable to :data:`SEMANTIC_RULES`. The contract is
``(model: BaseModel) -> Iterable[Issue]``. Rule IDs are *append-only*; never
re-number an existing rule, even if it's removed (mark deprecated).
"""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Any

from pydantic import BaseModel


VENDORED_XSD = (
    Path(__file__).parent / "codegen" / "vendored" / "DEXPI_XML_Schema.xsd"
)


@dataclass(frozen=True)
class Issue:
    """One validation finding.

    ``path`` is a slash-delimited locator (e.g. ``EngineeringModel/PlantModel/...``)
    that's stable enough to grep on but doesn't try to be a full XPath.
    """

    rule_id: str
    severity: str  # "error" | "warning"
    message: str
    path: str = ""

    def __str__(self) -> str:
        loc = f" at {self.path}" if self.path else ""
        return f"[{self.severity}] {self.rule_id}: {self.message}{loc}"


# ---------------------------------------------------------------------------
# XSD layer (optional dependency)


class XmlschemaUnavailableError(RuntimeError):
    """Raised when ``xmlschema`` is not installed but XSD validation is requested."""


def xsd_validate(xml_path: str | Path) -> list[Issue]:
    """Validate ``xml_path`` against the vendored DEXPI 2.0 XSD.

    Requires ``xmlschema`` (install with ``pip install xmlschema`` or
    ``pip install -e '.[validate]'``). Returns a list of :class:`Issue`s.
    """
    try:
        import xmlschema  # noqa: PLC0415
    except ImportError as exc:
        raise XmlschemaUnavailableError(
            "xsd_validate requires the 'xmlschema' package. "
            "Install via: pip install xmlschema"
        ) from exc

    schema = xmlschema.XMLSchema(str(VENDORED_XSD))
    issues: list[Issue] = []
    for err in schema.iter_errors(str(xml_path)):
        issues.append(
            Issue(
                rule_id="DEX_XSD",
                severity="error",
                message=str(err.reason or err),
                path=err.path or "",
            )
        )
    return issues


# ---------------------------------------------------------------------------
# Semantic rule pack (pure Python, no extra deps)


_TAG_NAME_RE = re.compile(r"^[A-Za-z][A-Za-z0-9_\-./ ]*$")


def _walk(obj: Any, path: str = "", visited: set[int] | None = None) -> Iterable[tuple[str, BaseModel]]:
    """Yield ``(path, instance)`` for every entity in the graph, depth-first.

    Stops descending at value-typed objects (no ``id`` field) so we don't
    enumerate every quantity. Tracks visited ids to break reference cycles.
    """
    if visited is None:
        visited = set()
    if obj is None or not isinstance(obj, BaseModel):
        return
    is_entity = "id" in type(obj).model_fields
    if is_entity:
        oid = id(obj)
        if oid in visited:
            return
        visited.add(oid)
        yield path or type(obj).__name__, obj
    for fname in type(obj).model_fields:
        if fname in ("id", "proteusId", "customAttributes"):
            continue
        try:
            val = getattr(obj, fname)
        except AttributeError:
            continue
        sub_path = f"{path}/{fname}" if path else fname
        if isinstance(val, list):
            for i, item in enumerate(val):
                yield from _walk(item, f"{sub_path}[{i}]", visited)
        else:
            yield from _walk(val, sub_path, visited)


def _rule_DEX0001_tag_name_format(model: BaseModel) -> Iterable[Issue]:
    """Tag names must match ``[A-Za-z][A-Za-z0-9_\\-./ ]*``."""
    for path, obj in _walk(model):
        tag = getattr(obj, "TagName", None)
        if not isinstance(tag, str) or not tag:
            continue
        if not _TAG_NAME_RE.match(tag):
            yield Issue(
                rule_id="DEX0001",
                severity="warning",
                message=f"TagName {tag!r} doesn't match the recommended format",
                path=path,
            )


def _rule_DEX0002_metadata_drawing_number(model: BaseModel) -> Iterable[Issue]:
    """``MetaData.DrawingNumber`` should be populated for paper-grade output."""
    cm = getattr(model, "conceptual_model", None)
    if cm is None:
        return
    md = getattr(cm, "meta_data", None)
    if md is None:
        yield Issue(
            rule_id="DEX0002",
            severity="warning",
            message="ConceptualModel has no MetaData",
            path="conceptual_model",
        )
        return
    if not getattr(md, "DrawingNumber", None):
        yield Issue(
            rule_id="DEX0002",
            severity="warning",
            message="MetaData.DrawingNumber is missing",
            path="conceptual_model/meta_data",
        )


def _rule_DEX0003_signal_conveying_endpoints(model: BaseModel) -> Iterable[Issue]:
    """Every ``SignalConveyingFunction`` must have both Source and Target set."""
    for path, obj in _walk(model):
        if type(obj).__name__ != "SignalConveyingFunction":
            continue
        if getattr(obj, "Source", None) is None:
            yield Issue(
                rule_id="DEX0003",
                severity="error",
                message="SignalConveyingFunction.Source is missing",
                path=path,
            )
        if getattr(obj, "Target", None) is None:
            yield Issue(
                rule_id="DEX0003",
                severity="error",
                message="SignalConveyingFunction.Target is missing",
                path=path,
            )


def _rule_DEX0004_pif_has_number(model: BaseModel) -> Iterable[Issue]:
    """Every ``ProcessInstrumentationFunction`` should carry a loop number."""
    for path, obj in _walk(model):
        if type(obj).__name__ not in (
            "ProcessInstrumentationFunction",
            "ProcessControlFunction",
        ):
            continue
        if not getattr(obj, "ProcessInstrumentationFunctionNumber", None):
            yield Issue(
                rule_id="DEX0004",
                severity="warning",
                message=(
                    f"{type(obj).__name__} has no "
                    f"ProcessInstrumentationFunctionNumber"
                ),
                path=path,
            )


def _rule_DEX0005_piping_segment_has_items(model: BaseModel) -> Iterable[Issue]:
    """A ``PipingNetworkSegment`` with no Items / SourceItem / TargetItem is suspicious."""
    for path, obj in _walk(model):
        if type(obj).__name__ != "PipingNetworkSegment":
            continue
        items = getattr(obj, "Items", []) or []
        src = getattr(obj, "SourceItem", None)
        tgt = getattr(obj, "TargetItem", None)
        if not items and src is None and tgt is None:
            yield Issue(
                rule_id="DEX0005",
                severity="warning",
                message="PipingNetworkSegment has no Items, SourceItem, or TargetItem",
                path=path,
            )


SEMANTIC_RULES: tuple = (
    _rule_DEX0001_tag_name_format,
    _rule_DEX0002_metadata_drawing_number,
    _rule_DEX0003_signal_conveying_endpoints,
    _rule_DEX0004_pif_has_number,
    _rule_DEX0005_piping_segment_has_items,
)


def semantic_validate(
    model: BaseModel,
    rules: tuple = SEMANTIC_RULES,
    rule_filter: set[str] | None = None,
) -> list[Issue]:
    """Run the semantic rule pack over ``model``. Returns issues sorted by
    ``(path, rule_id)`` so output diffs cleanly across runs.

    ``rule_filter``: if provided, only rules whose ID is in the set run.
    """
    issues: list[Issue] = []
    for rule in rules:
        for issue in rule(model):
            if rule_filter is not None and issue.rule_id not in rule_filter:
                continue
            issues.append(issue)
    issues.sort(key=lambda i: (i.path, i.rule_id))
    return issues


def has_errors(issues: Iterable[Issue]) -> bool:
    """True if any issue carries severity 'error'."""
    return any(i.severity == "error" for i in issues)
