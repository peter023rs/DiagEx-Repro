"""diagex-native JSON I/O for DEXPI 2.0 pydantic models.

Format envelope::

    {
      "_diagex_format": "1",
      "_dexpi_version": "2.0.0",
      "model": <object>
    }

Each entity object carries::

    {
      "_type": "<ClassName>",
      "id": "<uuid>",
      ...
    }

Cross-references (objects referenced from more than one place) are emitted as
``{"$ref": "<id>"}`` after the first full occurrence. Object identity is
preserved on round-trip.

This format is **diagex-internal**. The DEXPI XML writer in Phase 4 produces a
spec-conformant DEXPI 2.0 XML separately; the JSON form preserves diagex
extensions (notably ``customAttributes``) that DEXPI XML cannot carry.

Known v1 limitations:

- Cycles where the shared object's full body has not yet been emitted at the
  point of the first ``$ref`` raise :class:`CyclicRefError`. Most DEXPI plant
  graphs are trees with shared refs forward-only; cycles are uncommon.
"""
from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

from pydantic import BaseModel

DIAGEX_FORMAT_VERSION = "1"
DEXPI_VERSION = "2.0.0"


# Custom errors so callers can catch them precisely.
class DiagexJsonError(ValueError):
    """Base for diagex JSON I/O errors."""


class DuplicateIdError(DiagexJsonError):
    pass


class IncompleteRefError(DiagexJsonError):
    pass


class UnknownTypeError(DiagexJsonError):
    pass


class CyclicRefError(DiagexJsonError):
    pass


class FormatVersionError(DiagexJsonError):
    pass


# ---------------------------------------------------------------------------
# Class registry — built lazily to avoid import cycles.

_REGISTRY: dict[str, type] | None = None


def _build_registry() -> dict[str, type]:
    """Return ``{class_name: class}`` for every entity / value class diagex knows.

    Walks the generated modules and the extensions module. Names are simple
    (e.g. ``"OperatedValve"``); collisions are not expected since Spike C
    confirmed Core+Plant has zero name collisions, and extensions use unique
    names.
    """
    from diagex.dexpi import extensions as _ext
    from diagex.dexpi._generated import core as _core
    from diagex.dexpi._generated import plant as _plant
    from diagex.dexpi._generated import process as _process

    registry: dict[str, type] = {}
    for module in (_core, _plant, _process, _ext):
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and issubclass(obj, BaseModel)
                and not name.startswith("_")
                and obj.__module__ == module.__name__
            ):
                registry[name] = obj
    return registry


def _registry() -> dict[str, type]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


# ---------------------------------------------------------------------------
# Encode


def _is_entity(obj: BaseModel) -> bool:
    """Entities have a top-level ``id`` field; value types do not."""
    return "id" in type(obj).model_fields


def _encode_value(value: Any, seen: dict[str, bool]) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, datetime):
        return value.isoformat()
    if isinstance(value, list):
        return [_encode_value(v, seen) for v in value]
    if isinstance(value, dict):
        return {k: _encode_value(v, seen) for k, v in value.items()}
    if isinstance(value, BaseModel):
        return _encode_obj(value, seen)
    # Enum / other — fall back to str representation
    if hasattr(value, "value"):
        return value.value
    return str(value)


def _encode_obj(obj: BaseModel, seen: dict[str, bool]) -> dict[str, Any]:
    """Encode a single pydantic model to a JSON dict.

    Entities have ``_type`` + ``id`` and dedup via ``$ref``; value types have
    ``_type`` only.
    """
    if _is_entity(obj):
        oid = obj.id
        if oid in seen:
            return {"$ref": oid}
        seen[oid] = True

    out: dict[str, Any] = {"_type": type(obj).__name__}
    for fname, finfo in type(obj).model_fields.items():
        wire_name = finfo.alias if finfo.alias else fname
        value = getattr(obj, fname)
        out[wire_name] = _encode_value(value, seen)
    return out


def dumps(model: BaseModel, indent: int | None = 2) -> str:
    """Encode a pydantic model graph to a diagex-native JSON string."""
    seen: dict[str, bool] = {}
    payload = {
        "_diagex_format": DIAGEX_FORMAT_VERSION,
        "_dexpi_version": DEXPI_VERSION,
        "model": _encode_obj(model, seen),
    }
    return json.dumps(payload, indent=indent, sort_keys=False)


def dump(model: BaseModel, path: Path | str, indent: int | None = 2) -> Path:
    """Encode and write to ``path``. Returns the written path."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dumps(model, indent=indent), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Decode


def _scan_ids(node: Any, by_id: dict[str, dict]) -> None:
    """Pass 1: collect every entity dict (anything with ``_type`` and ``id``) by id."""
    if isinstance(node, dict):
        if "_type" in node and "id" in node:
            existing = by_id.get(node["id"])
            if existing is not None and existing is not node:
                raise DuplicateIdError(
                    f"two entity objects share id {node['id']!r}"
                )
            by_id[node["id"]] = node
        for v in node.values():
            _scan_ids(v, by_id)
    elif isinstance(node, list):
        for v in node:
            _scan_ids(v, by_id)


def _resolve_field_name(cls: type, wire_name: str) -> str:
    """Map a JSON-wire field name to the Python attribute name on ``cls``.

    Pydantic_emit renames a field to snake_case + alias when the field name
    collides with its type name (e.g. ``ConceptualModel`` → ``conceptual_model``
    + ``alias="ConceptualModel"``). The JSON wire form keeps the alias.
    """
    if wire_name in cls.model_fields:
        return wire_name
    for fname, finfo in cls.model_fields.items():
        if finfo.alias == wire_name:
            return fname
    return wire_name


def _is_reference_field(cls: type, py_name: str) -> bool:
    """Whether ``py_name`` (Python attribute name) is a DEXPI reference field.

    Defers to the generated ``_dexpi_kind`` classmethod when available; returns
    False otherwise so non-DEXPI / extension classes keep v1 behaviour.
    """
    fn = getattr(cls, "_dexpi_kind", None)
    if not callable(fn):
        return False
    return fn(py_name) == "reference"


def _allows_none_for(cls: type, py_name: str) -> bool:
    """Whether the field's annotation includes ``None`` (Optional / X | None)."""
    finfo = cls.model_fields.get(py_name)
    if finfo is None:
        return True  # unknown field — be permissive
    ann = finfo.annotation
    args = getattr(ann, "__args__", None) or ()
    return type(None) in args


def _safe_reference_default(cls: type, py_name: str) -> Any:
    """Default placeholder used when deferring a reference field during decode.

    Mirrors the field's cardinality so model_validate accepts the partial
    construction; the real value is patched in via setattr after the instance
    is registered in ``instances``.
    """
    finfo = cls.model_fields.get(py_name)
    if finfo is None:
        return None
    ann = finfo.annotation
    origin = getattr(ann, "__origin__", None)
    if origin is list:
        return []
    return None


def _build(
    node: Any,
    by_id: dict[str, dict],
    instances: dict[str, BaseModel],
    in_progress: set[str],
    registry: dict[str, type],
    deferred_back_refs: list[tuple[BaseModel, str, Any]],
) -> Any:
    """Pass 2: instantiate entities and value objects, resolving ``$ref`` against ``instances``.

    Cycle handling: reference-typed fields are queued in ``deferred_back_refs``
    and resolved at the very end of decoding (after every entity is in
    ``instances``). Composition fields stay eager — cycles through composition
    would imply an object owns itself, which DEXPI's metamodel doesn't allow.
    """
    if isinstance(node, dict):
        # $ref
        if "$ref" in node:
            ref_id = node["$ref"]
            if ref_id in instances:
                return instances[ref_id]
            if ref_id not in by_id:
                raise IncompleteRefError(f"$ref to unknown id {ref_id!r}")
            if ref_id in in_progress:
                raise CyclicRefError(
                    f"cyclic $ref to id {ref_id!r} via composition path; "
                    "DEXPI cycles must go through reference-typed fields"
                )
            return _build(
                by_id[ref_id], by_id, instances, in_progress, registry, deferred_back_refs
            )

        # Typed object
        if "_type" in node:
            cls_name = node["_type"]
            cls = registry.get(cls_name)
            if cls is None:
                raise UnknownTypeError(f"unknown class in JSON: {cls_name!r}")
            obj_id = node.get("id")
            if obj_id is not None:
                if obj_id in instances:
                    return instances[obj_id]
                in_progress.add(obj_id)
            kwargs: dict[str, Any] = {}
            local_deferred: list[tuple[str, Any]] = []
            for k, v in node.items():
                if k == "_type":
                    continue
                py_name = _resolve_field_name(cls, k)
                if obj_id is not None and _is_reference_field(cls, py_name):
                    local_deferred.append((py_name, v))
                    default = _safe_reference_default(cls, py_name)
                    if default is not None or _allows_none_for(cls, py_name):
                        kwargs[k] = default
                else:
                    kwargs[k] = _build(
                        v, by_id, instances, in_progress, registry, deferred_back_refs
                    )
            has_required_deferred = any(
                cls.model_fields.get(py_name)
                and cls.model_fields[py_name].is_required()
                and not _allows_none_for(cls, py_name)
                for py_name, _ in local_deferred
            )
            if has_required_deferred:
                obj = cls.model_construct(**kwargs)
            else:
                obj = cls.model_validate(kwargs)
            if obj_id is not None:
                instances[obj_id] = obj
                in_progress.discard(obj_id)
            for py_name, v in local_deferred:
                deferred_back_refs.append((obj, py_name, v))
            return obj

        # Plain dict (no _type) — pass through with recursion (rare)
        return {
            k: _build(v, by_id, instances, in_progress, registry, deferred_back_refs)
            for k, v in node.items()
        }

    if isinstance(node, list):
        return [
            _build(v, by_id, instances, in_progress, registry, deferred_back_refs)
            for v in node
        ]
    return node


def _resolve_back_refs(
    deferred: list[tuple[BaseModel, str, Any]],
    by_id: dict[str, dict],
    instances: dict[str, BaseModel],
    registry: dict[str, type],
) -> None:
    """Pass 3: walk every deferred reference field and assign the resolved value.

    Run after the eager-composition pass, so every entity is already in
    ``instances`` and a back-reference cycle resolves to the existing instance
    rather than recursing into a partially-built body.
    """
    in_progress: set[str] = set()
    for obj, py_name, raw_value in deferred:
        resolved = _build(
            raw_value, by_id, instances, in_progress, registry, deferred
        )
        setattr(obj, py_name, resolved)


def loads(text: str) -> BaseModel:
    """Decode a diagex-native JSON string back into a pydantic model graph."""
    data = json.loads(text)
    fmt = data.get("_diagex_format")
    if fmt != DIAGEX_FORMAT_VERSION:
        raise FormatVersionError(
            f"unsupported _diagex_format {fmt!r}; this build understands {DIAGEX_FORMAT_VERSION!r}"
        )
    if "model" not in data:
        raise DiagexJsonError("missing 'model' key in payload")

    body = data["model"]
    by_id: dict[str, dict] = {}
    _scan_ids(body, by_id)

    instances: dict[str, BaseModel] = {}
    in_progress: set[str] = set()
    deferred: list[tuple[BaseModel, str, Any]] = []
    root = _build(body, by_id, instances, in_progress, _registry(), deferred)
    _resolve_back_refs(deferred, by_id, instances, _registry())
    return root


def load(path: Path | str) -> BaseModel:
    """Read ``path`` and decode."""
    return loads(Path(path).read_text(encoding="utf-8"))
