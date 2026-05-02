"""DEXPI 2.0 XML I/O for diagex.

Emits the spec-conformant DEXPI XML envelope around an :class:`EngineeringModel`
graph, and parses an existing DEXPI XML file back into pydantic. The wire
format follows DEXPI 2.0 (the meta-schema in
``codegen/vendored/DEXPI_XML_Schema.xsd``); see Spike B notes in
``plan/dexpi-decoupling-phase1-spike-findings.md`` for the encoding rules:

- Root element is ``<Model>`` with ``Import`` declarations for each namespace.
- Entity instances are ``<Object id="..." type="<Prefix>/<QName>"/>``.
- Composition: ``<Components property="..."><Object .../></Components>``.
- Data values: ``<Data property="..."><String|Integer|Double|Boolean|...>v</...></Data>``.
- Enum values: ``<Data property="..."><DataReference data="<Prefix>/<EnumQName>.<Literal>"/></Data>``.
- Aggregated value types: ``<Data property="..."><AggregatedDataValue type="..."/></Data>``.

Diagex-internal fields (``customAttributes``, ``proteusId``) are dropped on
emit per compatibility-matrix decision §4 option A.

Known v1 limitations:

- Diagex extension classes (``CustomEquipment``, ``CustomOperatedValve``)
  cannot be emitted to DEXPI XML — they have no DEXPI 2.0 type. Phase 5 is
  expected to ensure ``dexpi_builder.py`` always classifies into concrete
  DEXPI 2.0 classes; until then the writer raises
  :class:`UnsupportedClassError`.
- ``BoundDataType`` properties (~217 fields) are not yet round-tripped
  faithfully. They land as ``Optional[Any]`` in the generated model and are
  emitted/parsed as best-effort.
- Cross-references via ``<ObjectReference>`` are not produced. The reference
  fixture (``reference_pid.xml``) is purely tree-structured.
"""
from __future__ import annotations

from datetime import datetime
from enum import Enum
from pathlib import Path
import types
from typing import Any, Union, get_args, get_origin
from xml.etree import ElementTree as ET

from pydantic import BaseModel

DEXPI_VERSION = "2.0.0"
NS_URLS = {
    "Core": f"https://data.dexpi.org/models/{DEXPI_VERSION}/Core.xml",
    "Plant": f"https://data.dexpi.org/models/{DEXPI_VERSION}/Plant.xml",
}


class DexpiXmlError(ValueError):
    pass


class UnsupportedClassError(DexpiXmlError):
    pass


class UnknownTypeError(DexpiXmlError):
    pass


# Annotation introspection. Both helpers walk through ``X | None`` /
# ``Union[X, None]`` / ``Optional[X]`` because the generated model alternates
# between those forms depending on which ruff rules ran on the regen.
def _union_arms(annotation: Any) -> tuple[Any, ...]:
    if get_origin(annotation) in (Union, types.UnionType):
        return get_args(annotation)
    return (annotation,)


def _allows_none(annotation: Any) -> bool:
    return any(arm is type(None) for arm in _union_arms(annotation))


def _allows_list(annotation: Any) -> bool:
    return any(get_origin(arm) is list for arm in _union_arms(annotation))


# ---------------------------------------------------------------------------
# Class registry & qname helpers


_REGISTRY: dict[str, type] | None = None
_ENUM_QNAMES: dict[str, str] | None = None


def _build_registry() -> dict[str, type]:
    from diagex.dexpi._generated import core as _core
    from diagex.dexpi._generated import enums as _enums
    from diagex.dexpi._generated import plant as _plant
    from diagex.dexpi._generated import process as _process
    from diagex.dexpi import extensions as _ext  # noqa: F401

    out: dict[str, type] = {}
    for module in (_core, _plant, _process, _enums):
        for name in dir(module):
            obj = getattr(module, name)
            if (
                isinstance(obj, type)
                and not name.startswith("_")
                and obj.__module__ == module.__name__
            ):
                out[name] = obj
    return out


def _registry() -> dict[str, type]:
    global _REGISTRY
    if _REGISTRY is None:
        _REGISTRY = _build_registry()
    return _REGISTRY


def _enum_qnames() -> dict[str, str]:
    global _ENUM_QNAMES
    if _ENUM_QNAMES is None:
        from diagex.dexpi._generated.enums import _DEXPI_QNAME
        _ENUM_QNAMES = dict(_DEXPI_QNAME)
    return _ENUM_QNAMES


def _wire_qname_for(cls: type) -> str:
    """Return the DEXPI wire-form qname for a class.

    For diagex extensions (which subclass DEXPI classes but have no qname of
    their own), raises :class:`UnsupportedClassError` — see the v1 limitation
    above.
    """
    qn = cls.__dict__.get("__dexpi_qname__")
    if qn is not None:
        return qn
    # Inherited from base — likely a diagex extension on top of a DEXPI parent.
    parent_qn = getattr(cls, "__dexpi_qname__", None)
    if parent_qn is not None:
        # Detect diagex extensions by checking the parent has a different qname
        # and the current class isn't directly defined in _generated.
        if cls.__module__.endswith(".extensions"):
            raise UnsupportedClassError(
                f"{cls.__name__} is a diagex extension; cannot emit as DEXPI XML "
                f"because it has no DEXPI 2.0 wire type. Classify the entity into "
                f"a concrete DEXPI 2.0 class before emit."
            )
        return parent_qn
    raise UnsupportedClassError(f"{cls.__name__} has no __dexpi_qname__")


def _is_entity(cls: type) -> bool:
    return "id" in cls.model_fields


# ---------------------------------------------------------------------------
# Writer


def _write_value(parent: ET.Element, prop_name: str, value: Any) -> None:
    """Append a ``<Data property="...">…</Data>`` child encoding ``value``."""
    data = ET.SubElement(parent, "Data", attrib={"property": prop_name})
    _write_value_body(data, value)


def _write_value_body(data: ET.Element, value: Any) -> None:
    """Inner of `<Data>`: a single typed value child."""
    if isinstance(value, bool):
        ET.SubElement(data, "Boolean").text = "true" if value else "false"
    elif isinstance(value, int):
        ET.SubElement(data, "Integer").text = str(value)
    elif isinstance(value, float):
        ET.SubElement(data, "Double").text = repr(value)
    elif isinstance(value, datetime):
        ET.SubElement(data, "DateTime").text = value.isoformat()
    elif isinstance(value, Enum):
        # Enum: encode as <DataReference data="<EnumQname>.<Literal>"/>
        enum_qname = _enum_qnames().get(type(value).__name__)
        if enum_qname is None:
            raise UnknownTypeError(
                f"unknown enum class {type(value).__name__}; "
                f"no qname in _DEXPI_QNAME registry"
            )
        ET.SubElement(
            data,
            "DataReference",
            attrib={"data": f"{enum_qname}.{value.value}"},
        )
    elif isinstance(value, BaseModel):
        # Aggregated value type
        ET.SubElement(
            data,
            "AggregatedDataValue",
            attrib={"type": _wire_qname_for(type(value))},
        ).extend(_pydantic_to_data_children(value))
    elif isinstance(value, str):
        ET.SubElement(data, "String").text = value
    elif value is None:
        # caller should have skipped None values
        pass
    else:
        # fallback: stringify
        ET.SubElement(data, "String").text = str(value)


def _pydantic_to_data_children(obj: BaseModel) -> list[ET.Element]:
    """Render a pydantic value-object's properties as a list of ``<Data>`` elements."""
    out: list[ET.Element] = []
    for fname, finfo in type(obj).model_fields.items():
        if fname in ("id", "proteusId", "customAttributes"):
            continue
        value = getattr(obj, fname)
        if value is None or (isinstance(value, list) and not value):
            continue
        prop_name = finfo.alias or fname
        if isinstance(value, list):
            data = ET.Element("Data", attrib={"property": prop_name})
            for v in value:
                _write_value_body(data, v)
            out.append(data)
        else:
            data = ET.Element("Data", attrib={"property": prop_name})
            _write_value_body(data, value)
            out.append(data)
    return out


def _field_kind(cls: type, field_name: str) -> str:
    """DEXPI property kind for a field: ``composition``, ``reference``, or ``data``.

    Generated classes carry ``__dexpi_field_kinds__`` per Phase B1.  Falls back
    to ``data`` so older or extension classes (which the writer treated as
    composition for entity-typed fields under v1) keep round-tripping if the
    map is missing.
    """
    fn = getattr(cls, "_dexpi_kind", None)
    return fn(field_name) if callable(fn) else "data"


def _write_object(parent: ET.Element, obj: BaseModel, top_level: bool = False) -> None:
    cls = type(obj)
    attrib = {"type": _wire_qname_for(cls)}
    oid = getattr(obj, "id", None)
    if not top_level and oid is not None:
        attrib["id"] = oid
    elem = ET.SubElement(parent, "Object", attrib=attrib)

    # Walk fields
    for fname, finfo in cls.model_fields.items():
        if fname in ("id", "proteusId", "customAttributes"):
            continue
        # `model_construct` (used by the parser when fixtures omit a "required"
        # field) leaves attributes literally unset. Skip those rather than
        # raising — the round-trip just preserves the gap.
        try:
            value = getattr(obj, fname)
        except AttributeError:
            continue
        if value is None:
            continue
        if isinstance(value, list) and not value:
            continue
        prop_name = finfo.alias or fname
        kind = _field_kind(cls, fname)

        if isinstance(value, list):
            entities = [v for v in value if isinstance(v, BaseModel) and _is_entity(type(v))]
            if entities and len(entities) == len(value):
                if kind == "reference":
                    refs = " ".join(f"#{getattr(v, 'id', '')}" for v in value)
                    ET.SubElement(
                        elem,
                        "References",
                        attrib={"property": prop_name, "objects": refs},
                    )
                else:
                    comps = ET.SubElement(
                        elem, "Components", attrib={"property": prop_name}
                    )
                    for v in value:
                        _write_object(comps, v)
            else:
                data = ET.SubElement(elem, "Data", attrib={"property": prop_name})
                for v in value:
                    _write_value_body(data, v)
        elif isinstance(value, BaseModel) and _is_entity(type(value)):
            if kind == "reference":
                target_id = getattr(value, "id", "")
                ET.SubElement(
                    elem,
                    "References",
                    attrib={"property": prop_name, "objects": f"#{target_id}"},
                )
            else:
                comps = ET.SubElement(elem, "Components", attrib={"property": prop_name})
                _write_object(comps, value)
        else:
            _write_value(elem, prop_name, value)


def dumps(model: BaseModel) -> str:
    """Encode an EngineeringModel-rooted pydantic graph as a DEXPI 2.0 XML string."""
    root = ET.Element(
        "Model",
        attrib={"name": "diagex_export", "uri": "http://example.org/diagex"},
    )
    for prefix, url in NS_URLS.items():
        ET.SubElement(root, "Import", attrib={"prefix": prefix, "source": url})
    _write_object(root, model, top_level=True)
    ET.indent(root, space="  ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(root, encoding="unicode")


def dump(model: BaseModel, path: Path | str) -> Path:
    """Encode and write ``model`` to ``path``."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(dumps(model), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Parser


def _local_class(type_attr: str) -> type:
    """``Plant/Piping.OperatedValve`` -> the OperatedValve class."""
    name = type_attr.split(".")[-1] if "." in type_attr else type_attr.split("/", 1)[-1]
    cls = _registry().get(name)
    if cls is None:
        raise UnknownTypeError(f"unknown DEXPI type in XML: {type_attr!r}")
    return cls


def _parse_value(elem: ET.Element) -> Any:
    """Parse a single typed value child of <Data>."""
    tag = elem.tag
    if tag == "String":
        return elem.text or ""
    if tag == "Integer":
        return int(elem.text) if elem.text else 0
    if tag == "Double":
        return float(elem.text) if elem.text else 0.0
    if tag == "Boolean":
        return (elem.text or "").lower() == "true"
    if tag == "DateTime":
        return datetime.fromisoformat(elem.text) if elem.text else None
    if tag == "DataReference":
        # <DataReference data="Plant/Enumerations.FailActionClassification.FailClose"/>
        ref = elem.get("data", "")
        # The literal is the trailing segment after the last '.'
        head, _, literal = ref.rpartition(".")
        # head is the enum qname
        enum_name = head.rsplit(".", 1)[-1] if "." in head else head.rsplit("/", 1)[-1]
        cls = _registry().get(enum_name)
        if cls is None:
            return ref  # unknown enum — return raw string
        try:
            return cls(literal)
        except (ValueError, KeyError):
            return ref
    if tag == "AggregatedDataValue":
        type_attr = elem.get("type", "")
        cls = _local_class(type_attr)
        kwargs = _parse_data_children(elem)
        return cls.model_validate(kwargs)
    return elem.text


def _parse_data_children(elem: ET.Element) -> dict[str, Any]:
    """Inverse of `_pydantic_to_data_children`: parse <Data> children of a value object."""
    out: dict[str, Any] = {}
    for child in elem:
        if child.tag != "Data":
            continue
        prop = child.get("property", "")
        # Could be a single value, an aggregated value, or a list
        children = list(child)
        if len(children) == 0:
            out[prop] = None
        elif len(children) == 1:
            out[prop] = _parse_value(children[0])
        else:
            out[prop] = [_parse_value(c) for c in children]
    return out


def _coerce_to_field_type(value: Any, annotation: Any) -> Any:
    """If ``value`` is an instance of an ancestor of the expected concrete type,
    upcast via ``model_validate``. Currently only matters for typed
    ``PhysicalQuantity`` subclasses: the wire format emits the bare
    ``PhysicalQuantity`` qname, but the field is typed e.g. ``LengthQuantity``.
    """
    if value is None or not isinstance(value, BaseModel):
        return value
    for arm in _union_arms(annotation):
        if isinstance(arm, type) and issubclass(arm, BaseModel) and arm is not type(value):
            if isinstance(value, arm):
                continue
            if issubclass(arm, type(value)):
                return arm.model_validate(value.model_dump())
    return value


class _ParseContext:
    """Carries the id-table and pending <References> across the two parse passes."""

    __slots__ = ("id_table", "pending")

    def __init__(self) -> None:
        # id (without the '#' prefix) → parsed instance
        self.id_table: dict[str, BaseModel] = {}
        # (referrer, field_name, [id, ...]) — resolve in pass 2
        self.pending: list[tuple[BaseModel, str, list[str]]] = []


def _resolve_field_name(cls: type, prop: str) -> tuple[str, Any]:
    """Map a wire-format property name to ``(python_field_name, annotation)``.

    Handles the alias case where pydantic_emit renamed a field to snake_case
    because of a name-shadowing collision.  Returns ``(prop, None)`` if the
    field doesn't exist on ``cls``.
    """
    field = cls.model_fields.get(prop)
    if field is not None:
        return prop, field.annotation
    for fname, finfo in cls.model_fields.items():
        if finfo.alias == prop:
            return fname, finfo.annotation
    return prop, None


def _parse_object(elem: ET.Element, ctx: _ParseContext) -> BaseModel:
    """Parse an <Object .../> element into a pydantic instance."""
    type_attr = elem.get("type", "")
    cls = _local_class(type_attr)
    kwargs: dict[str, Any] = {}
    oid = elem.get("id")
    if oid is not None:
        kwargs["id"] = oid

    # First pass: parse Data + Components (composition), defer References.
    deferred_refs: list[tuple[str, list[str]]] = []
    for child in elem:
        if child.tag == "Data":
            prop = child.get("property", "")
            grand = list(child)
            py_name, ann = _resolve_field_name(cls, prop)
            is_list_field = ann is not None and _allows_list(ann)
            if len(grand) == 0:
                values = [None]
            elif len(grand) == 1:
                parsed = _parse_value(grand[0])
                values = [
                    _coerce_to_field_type(parsed, ann) if ann is not None else parsed
                ]
            else:
                values = [_parse_value(c) for c in grand]
                if ann is not None:
                    values = [_coerce_to_field_type(v, ann) for v in values]
            # Multiple <Data property="X"> elements with the same property name
            # accumulate into a list when the field is list-typed (e.g. Point
            # InnerPoints in ConnectorLine). For non-list fields, the last
            # occurrence wins, matching v1 behaviour.
            if is_list_field:
                existing = kwargs.get(py_name)
                if existing is None:
                    kwargs[py_name] = list(values)
                else:
                    existing.extend(values)
            else:
                kwargs[py_name] = values[0] if len(values) == 1 else values
        elif child.tag == "Components":
            prop = child.get("property", "")
            objs = [_parse_object(o, ctx) for o in child if o.tag == "Object"]
            py_name, ann = _resolve_field_name(cls, prop)
            if ann is not None and _allows_list(ann):
                kwargs[py_name] = objs
            else:
                kwargs[py_name] = objs[0] if objs else None
        elif child.tag == "References":
            prop = child.get("property", "")
            objects_attr = child.get("objects", "").strip()
            ids = [tok.lstrip("#") for tok in objects_attr.split() if tok]
            py_name, _ = _resolve_field_name(cls, prop)
            deferred_refs.append((py_name, ids))

    # Fill None for required-but-Optional fields that weren't explicitly set.
    # The DEXPI emitter drops None values, so the parser must reinstate them.
    for fname, finfo in cls.model_fields.items():
        wire = finfo.alias if finfo.alias else fname
        if fname in kwargs or wire in kwargs:
            continue
        if finfo.is_required() and _allows_none(finfo.annotation):
            kwargs[fname] = None

    # Required-non-Optional reference fields (e.g. AttributeRepresentation.Object)
    # can't pass model_validate while their value is still deferred. Construct
    # without validation in that case; the deferred-resolution pass will assign
    # the real target via setattr (validate_assignment runs at that point).
    has_required_deferred = any(
        cls.model_fields.get(py_name)
        and cls.model_fields[py_name].is_required()
        and not _allows_none(cls.model_fields[py_name].annotation)
        for py_name, _ in deferred_refs
    )
    if has_required_deferred:
        obj = cls.model_construct(**kwargs)
    else:
        try:
            obj = cls.model_validate(kwargs)
        except Exception:
            # Fixtures (incl. the official reference_pid.xml) routinely omit
            # fields the spec marks required (e.g. Shape.SymbolRegistrationNumber).
            # Fall back to model_construct so the round-trip still completes;
            # callers who want stricter checking can run validate() separately.
            obj = cls.model_construct(**kwargs)

    if oid is not None:
        ctx.id_table[oid] = obj
    for py_name, ids in deferred_refs:
        ctx.pending.append((obj, py_name, ids))
    return obj


def _resolve_pending(ctx: _ParseContext) -> None:
    """Pass 2: assign each pending reference field on its referrer."""
    for referrer, field_name, ids in ctx.pending:
        targets = [ctx.id_table[i] for i in ids if i in ctx.id_table]
        missing = [i for i in ids if i not in ctx.id_table]
        if missing:
            raise DexpiXmlError(
                f"unresolved <References> on {type(referrer).__name__}.{field_name}: "
                f"missing ids {missing}"
            )
        finfo = type(referrer).model_fields.get(field_name)
        ann = finfo.annotation if finfo is not None else None
        if ann is not None and _allows_list(ann):
            setattr(referrer, field_name, targets)
        else:
            setattr(referrer, field_name, targets[0] if targets else None)


def loads(text: str) -> BaseModel:
    """Parse a DEXPI 2.0 XML string back into a pydantic model graph."""
    root = ET.fromstring(text)
    if root.tag != "Model":
        raise DexpiXmlError(f"root element must be <Model>, got <{root.tag}>")
    ctx = _ParseContext()
    parsed_root: BaseModel | None = None
    for child in root:
        if child.tag == "Object":
            parsed_root = _parse_object(child, ctx)
            break
    if parsed_root is None:
        raise DexpiXmlError("<Model> contained no top-level <Object>")
    _resolve_pending(ctx)
    return parsed_root


def load(path: Path | str) -> BaseModel:
    return loads(Path(path).read_text(encoding="utf-8"))
