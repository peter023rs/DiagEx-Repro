"""Walk a `dexpi.specificator` metamodel and emit pydantic v2 source code.

Produces three files in ``src/diagex/dexpi/_generated/``:

- ``enums.py``  — every Enumeration across Core + Plant
- ``core.py``   — Core package: entity classes, AggregatedDataTypes, AbstractDataType unions
- ``plant.py``  — Plant package: equipment / piping / instrumentation hierarchy

The emitter is intentionally minimal:

- It does **not** try to preserve unit information for ``BoundDataType`` properties
  (~217 fields in Plant). Those land as ``Any`` for v1; refining is a Phase 2+ task.
- It emits PascalCase pydantic field names matching DEXPI 2.0; no camelCase aliases.
- It uses ``from __future__ import annotations`` and calls ``model_rebuild()`` at
  end of each module to handle forward refs and inheritance cycles.

This module is loaded only at codegen time. It depends on ``dexpi.specificator``
(MIT, Python 3.12+) and ``pnb.mcl.metamodel.standard`` (its transitive dep).
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path
from typing import Iterable

from dexpi.specificator.dsl_reader import DslReader
from pnb.mcl.metamodel.standard import (
    AbstractClass,
    AbstractDataType,
    AggregatedDataType,
    BoundDataType,
    ConcreteClass,
    DataProperty,
    DataType,
    Enumeration,
    Package,
)


# Map specificator's Builtin namespace to Python primitives.
_BUILTIN_TO_PY: dict[str, str] = {
    "Builtin.String": "str",
    "Builtin.Boolean": "bool",
    "Builtin.Integer": "int",
    "Builtin.UnsignedByte": "int",
    "Builtin.Double": "float",
    "Builtin.DateTime": "datetime",
    "Builtin.AnyURI": "str",
}


_HEADER_TEMPLATE = '''"""{title}

Auto-generated from the DEXPI Specification 2.0.0 sources at upstream commit
260c81c5 (V2.0.0, 2025-10-10). DO NOT EDIT BY HAND. Regenerate via:

    python -m diagex.dexpi.codegen.regenerate

Source DSL files (c) 2025 DEXPI Initiative, licensed under CC-BY 4.0
(https://creativecommons.org/licenses/by/4.0/). This generated module is
adapted material; modifications are limited to the deterministic transformation
performed by ``src/diagex/dexpi/codegen/pydantic_emit.py``. Generator and
runtime glue (c) 2026 the diagex authors, licensed under Apache-2.0.

This artefact does not imply DEXPI Initiative endorsement.
"""
# ruff: noqa: E501, F401, F405, F811, A003, N801, N815, N816, UP006, UP007
from __future__ import annotations

{extra_imports}'''


_ENTITY_BASE_SRC = '''
class DexpiEntityBase(BaseModel):
    """Base for entity classes (every concrete + abstract DEXPI class).

    Provides automatic UUID id, optional proteusId alias for cross-version
    interop, identity-based hashing so pydantic models work as dict keys and
    set members, and a ``customAttributes`` list for diagex-internal annotation.

    ``customAttributes`` is **not** part of DEXPI 2.0; it is a diagex-internal
    channel used to carry LLM-extracted hints. The DEXPI XML writer drops it on
    emit (per compatibility-matrix decision §4 option A); the diagex JSON writer
    preserves it.
    """

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)
    # XML ``xs:ID`` requires a name-safe leading character and disallows the
    # hyphens in a canonical UUID. Keep UUID entropy while emitting valid IDs.
    id: str = Field(default_factory=lambda: f"id_{uuid.uuid4().hex}")
    proteusId: Optional[str] = None
    customAttributes: list = Field(default_factory=list)

    def __hash__(self) -> int:
        return hash((self.id, type(self)))

    @classmethod
    def _dexpi_kind(cls, field_name: str) -> str:
        """Look up DEXPI property kind ("composition", "reference", "data") for a field.

        Walks the MRO so inherited fields find their kind on a parent class.
        Returns "data" if no class declares a kind (a defensive default; the
        writer treats unknown fields as data, matching v1 behaviour).
        """
        for klass in cls.__mro__:
            kinds = klass.__dict__.get("__dexpi_field_kinds__")
            if kinds and field_name in kinds:
                return kinds[field_name]
        return "data"
'''


_VALUE_BASE_SRC = '''
class DexpiValueBase(BaseModel):
    """Base for AggregatedDataType (value types — no id, no identity hash)."""

    model_config = ConfigDict(validate_assignment=True, populate_by_name=True)
'''


# ---------------------------------------------------------------------------
# Walking helpers


def walk_types(node) -> Iterable:
    """Recursively yield every class / enum / datatype directly inside the package."""
    for member in node.packagedElements:
        if isinstance(member, Package):
            yield from walk_types(member)
        elif isinstance(member, (ConcreteClass, AbstractClass, Enumeration, DataType)):
            yield member


def collect_all_named_types(reader: DslReader, namespaces: tuple[str, ...]) -> dict[str, object]:
    """Return ``{simple_name: type}`` across the given top-level namespaces."""
    out: dict[str, object] = {}
    for ns in namespaces:
        if ns not in reader.model_by_name:
            continue
        for t in walk_types(reader.model_by_name[ns]):
            # If a name collides we keep the first; matrix Spike C confirmed no collisions
            # across Core + Plant in the v1 scope, so this is defensive only.
            out.setdefault(t.name, t)
    return out


# ---------------------------------------------------------------------------
# Bound-quantity registry
#
# DEXPI 2.0 uses ``BoundDataType<PhysicalQuantity, UnitType=<X>Unit>`` to type
# physical-quantity properties (217 in the v2.0.0 Plant + Core spec).  Spike A1
# confirmed every such property has a single ``UnitType`` binding to a concrete
# ``Enumeration`` and 17 distinct unit families exist.
#
# We emit one pydantic subclass of ``PhysicalQuantity`` per (base, unit-enum)
# pair, named ``<UnitFamily>Quantity`` (e.g. ``LengthQuantity``).  The base
# stays generic ``PhysicalQuantity`` so non-typed callers keep working.

# Populated by ``collect_bound_quantity_specs``; keys: ``(base_qname, frozen-bindings)``
# where frozen-bindings is ``tuple[(param_name, unit_enum_simple_name), ...]``.
_BOUND_QUANTITY_REGISTRY: dict[tuple, str] = {}


def _bound_key(t: BoundDataType) -> tuple:
    base_q = t.base.qualifiedName_chained
    bindings = tuple(
        (b.parameter.name, b.type.name)
        for b in t.bindings
    )
    return (base_q, bindings)


def _bound_class_name(t: BoundDataType) -> str:
    """``BoundDataType<PhysicalQuantity, UnitType=LengthUnit>`` -> ``LengthQuantity``."""
    bindings = list(t.bindings)
    # Single-binding ``UnitType=<X>Unit`` is the only shape in v2.0.0.
    if len(bindings) == 1 and bindings[0].parameter.name == "UnitType":
        unit_simple = bindings[0].type.name
        if unit_simple.endswith("Unit"):
            return unit_simple[: -len("Unit")] + "Quantity"
        return unit_simple + "Quantity"
    # Multi-binding fallback: concat parameter values.
    parts = [b.type.name for b in bindings]
    return "".join(parts) + "Quantity"


def collect_bound_quantity_specs(
    reader: DslReader, namespaces: tuple[str, ...]
) -> list[BoundDataType]:
    """Return one canonical ``BoundDataType`` per distinct (base, bindings) pair."""
    seen: dict[tuple, BoundDataType] = {}
    for ns in namespaces:
        if ns not in reader.model_by_name:
            continue
        for cls in walk_types(reader.model_by_name[ns]):
            if not isinstance(cls, (ConcreteClass, AbstractClass)):
                continue
            for prop in cls.ownedAttributes:
                _walk_for_bound(prop.type, seen)
    return [seen[k] for k in sorted(seen, key=lambda k: _bound_class_name(seen[k]))]


def _walk_for_bound(t, seen: dict[tuple, BoundDataType]) -> None:
    if isinstance(t, BoundDataType):
        seen.setdefault(_bound_key(t), t)
    elif type(t).__name__ == "UnionDataType":
        for base in t.bases:
            _walk_for_bound(base, seen)


def render_bound_quantity_class(t: BoundDataType) -> str:
    """Emit a typed ``<UnitFamily>Quantity`` pydantic subclass of ``PhysicalQuantity``."""
    name = _bound_class_name(t)
    base_q = t.base.qualifiedName_chained
    base_simple = t.base.name
    bindings = list(t.bindings)
    binding_doc = ", ".join(
        f"{b.parameter.name}={b.type.qualifiedName_chained}" for b in bindings
    )
    docstring = (
        f'    """DEXPI 2.0 typed physical quantity {base_q}<{binding_doc}>."""'
    )
    qname_decl = f'    __dexpi_qname__: ClassVar[str] = "{_dexpi_wire_qname(t.base)}"\n'
    if len(bindings) == 1 and bindings[0].parameter.name == "UnitType":
        unit_simple = bindings[0].type.name
        unit_field = f"    Unit: {unit_simple}\n"
    else:
        unit_field = "    Unit: Any\n"
    return (
        f"class {name}({base_simple}):\n"
        f"{docstring}\n"
        f"{qname_decl}"
        f"{unit_field}"
        f"    Value: float\n"
    )


# ---------------------------------------------------------------------------
# Type rendering


def _qname(t) -> str | None:
    return getattr(t, "qualifiedName_chained", None)


def render_type(t, known: dict[str, object]) -> str:
    """Render a metamodel type reference as a Python annotation string."""
    if t is None:
        return "Any"
    q = _qname(t)
    if q in _BUILTIN_TO_PY:
        return _BUILTIN_TO_PY[q]
    if q == "Builtin.Undefined":
        # Bare Undefined shouldn't be a property type on its own; treat as Any.
        return "Any"
    if isinstance(t, BoundDataType):
        key = _bound_key(t)
        cls_name = _BOUND_QUANTITY_REGISTRY.get(key)
        if cls_name is not None:
            return cls_name
        # Fallback: caller hasn't populated the registry. Return the bare base.
        return t.base.name
    kind = type(t).__name__
    if kind == "UnionDataType":
        nullable = False
        parts: list[str] = []
        for base in t.bases:
            if _qname(base) == "Builtin.Undefined":
                nullable = True
                continue
            parts.append(render_type(base, known))
        if not parts:
            return "Any"
        inner = parts[0] if len(parts) == 1 else "Union[" + ", ".join(parts) + "]"
        return f"Optional[{inner}]" if nullable else inner
    # ClassParameter and other unhandled metamodel types → Any.
    if q is None:
        return "Any"
    # Class / enum / aggregated data type — use simple name; cross-module imports
    # are added at the top of each emitted file.
    name = t.name
    if name in known:
        return name
    # Reference into Core when emitting plant.py; if not in `known` here the call
    # site will adjust by passing a wider known-set.
    return "Any"


def _pascal_to_snake(name: str) -> str:
    """``ConceptualModel`` -> ``conceptual_model``."""
    out: list[str] = []
    for i, ch in enumerate(name):
        if ch.isupper() and i > 0 and (name[i - 1].islower() or
                                       (i + 1 < len(name) and name[i + 1].islower())):
            out.append("_")
        out.append(ch.lower())
    return "".join(out)


def _type_simple_name(rendered: str) -> str:
    """Pull the bare class name out of a rendered annotation, if any."""
    s = rendered
    for prefix in ("Optional[", "list[", "Union["):
        if s.startswith(prefix):
            s = s[len(prefix):].rstrip("]")
            break
    # Strip remaining brackets/commas
    return s.split(",")[0].strip().strip("[]")


def render_property(p, known: dict[str, object]) -> str:
    inner = render_type(p.type, known)
    lower = p.lower or 0
    upper = p.upper  # int or None (None ≡ unbounded)
    is_list = upper is None or (isinstance(upper, int) and upper > 1)
    already_optional = inner.startswith("Optional[")

    # Collision handling: if the field name equals the type simple-name, pydantic
    # gets confused by name shadowing. Rename the Python attribute to snake_case
    # and alias the wire-format PascalCase via Field(alias=...).
    type_simple = _type_simple_name(inner)
    name_collides = (p.name == type_simple)

    if is_list:
        annotation = f"list[{inner}]"
        default = "Field(default_factory=list)"
    elif lower == 0 and not already_optional:
        annotation = f"Optional[{inner}]"
        default = "None"
    else:
        annotation = inner
        default = "None" if (already_optional and lower == 0) else None

    if name_collides:
        py_name = _pascal_to_snake(p.name)
        alias = f', alias="{p.name}"'
        if default == "Field(default_factory=list)":
            default_expr = f'Field(default_factory=list{alias})'
        elif default is None:
            default_expr = f'Field(...{alias})'
        else:
            default_expr = f'Field(default={default}{alias})'
        return f"    {py_name}: {annotation} = {default_expr}"

    if default == "Field(default_factory=list)":
        return f"    {p.name}: {annotation} = {default}"
    if default is None:
        return f"    {p.name}: {annotation}"
    return f"    {p.name}: {annotation} = {default}"


# ---------------------------------------------------------------------------
# Per-class emission


def render_abstract_data_type(adt: AbstractDataType) -> str:
    sub_names = [s.name for s in adt.subTypes if isinstance(s, Enumeration)]
    if not sub_names:
        # Subtypes are themselves AbstractDataType — recursive case (e.g. PressureUnit).
        # For v1 emit a TypeAlias of all leaf enums under the tree.
        leaves: list[str] = []
        stack = list(adt.subTypes)
        while stack:
            s = stack.pop()
            if isinstance(s, Enumeration):
                leaves.append(s.name)
            elif isinstance(s, AbstractDataType):
                stack.extend(s.subTypes)
        if not leaves:
            return f"# AbstractDataType without leaf enums (skipped): {adt.name}\n"
        return f"{adt.name} = Union[{', '.join(leaves)}]\n"
    return f"{adt.name} = Union[{', '.join(sub_names)}]\n"


def _dexpi_wire_qname(cls) -> str:
    """``Plant.Piping.OperatedValve`` -> ``Plant/Piping.OperatedValve``."""
    qn = cls.qualifiedName_chained
    prefix, sep, rest = qn.partition(".")
    return f"{prefix}/{rest}" if rest else prefix


def render_class(cls, known: dict[str, object]) -> str:
    is_value = isinstance(cls, AggregatedDataType)
    bases = [sup.name for sup in cls.superTypes if sup.name in known]
    if not bases:
        bases = ["DexpiValueBase" if is_value else "DexpiEntityBase"]
    docstring_lines: list[str] = []
    if isinstance(cls, AbstractClass) and cls.isAbstract:
        docstring_lines.append(f"DEXPI 2.0 abstract class {cls.qualifiedName_chained}.")
    else:
        docstring_lines.append(f"DEXPI 2.0 class {cls.qualifiedName_chained}.")

    docstring = "    " + '"""' + " ".join(docstring_lines) + '"""\n'
    qname_decl = f'    __dexpi_qname__: ClassVar[str] = "{_dexpi_wire_qname(cls)}"\n'

    # Per-field DEXPI property kind ("composition", "reference", "data") so the
    # XML writer can pick <Components> vs <References> on emit. Only includes
    # fields owned by *this* class — inherited fields use the parent's mapping.
    kinds: dict[str, str] = {}
    for p in cls.ownedAttributes:
        kind = type(p).__name__
        if kind == "CompositionProperty":
            kinds[p.name] = "composition"
        elif kind == "ReferenceProperty":
            kinds[p.name] = "reference"
        elif kind == "DataProperty":
            kinds[p.name] = "data"
    if kinds:
        items = ", ".join(f'"{k}": "{v}"' for k, v in kinds.items())
        kinds_decl = f"    __dexpi_field_kinds__: ClassVar[dict[str, str]] = {{{items}}}\n"
    else:
        kinds_decl = ""

    props = list(cls.ownedAttributes)
    if not props:
        body = "    pass\n"
    else:
        body = "\n".join(render_property(p, known) for p in props) + "\n"
    return f"class {cls.name}({', '.join(bases)}):\n{docstring}{qname_decl}{kinds_decl}{body}"


def render_enum(e: Enumeration) -> str:
    lits = list(e.orderedOwnedLiterals)
    if not lits:
        return f"# Empty enum (skipped): {e.name}\n"
    qname = _dexpi_wire_qname(e)
    body = "\n".join(f'    {lit.name} = "{lit.name}"' for lit in lits)
    # StrEnums can't easily carry a non-str class attr; expose qname via a
    # module-level mapping instead.
    return f"class {e.name}(StrEnum):\n{body}\n_DEXPI_QNAME[{e.name}.__name__] = {qname!r}\n"


# ---------------------------------------------------------------------------
# File-level emission


def emit_enums_file(reader: DslReader, namespaces: tuple[str, ...]) -> str:
    enums: list[Enumeration] = []
    for ns in namespaces:
        if ns not in reader.model_by_name:
            continue
        for t in walk_types(reader.model_by_name[ns]):
            if isinstance(t, Enumeration):
                enums.append(t)
    enums.sort(key=lambda e: e.qualifiedName_chained)
    header = _HEADER_TEMPLATE.format(
        title="DEXPI 2.0 enumerations.",
        extra_imports="from enum import StrEnum\n\n_DEXPI_QNAME: dict[str, str] = {}\n",
    )
    body_chunks = [render_enum(e) for e in enums]
    return header + "\n" + "\n\n".join(body_chunks) + "\n"


def emit_core_file(
    reader: DslReader,
    known: dict[str, object],
    bound_specs: list[BoundDataType],
) -> str:
    classes: list = []
    abstract_dts: list[AbstractDataType] = []
    for t in walk_types(reader.model_by_name["Core"]):
        if isinstance(t, (ConcreteClass, AbstractClass, AggregatedDataType)):
            classes.append(t)
        elif isinstance(t, AbstractDataType):
            abstract_dts.append(t)
    classes_sorted = topo_sort(classes)
    abstract_dts.sort(key=lambda a: a.qualifiedName_chained)

    extra = (
        "import uuid\n"
        "from datetime import datetime\n"
        "from typing import Any, ClassVar, Optional, Union\n"
        "from pydantic import BaseModel, ConfigDict, Field\n"
        "\n"
        "from diagex.dexpi._generated.enums import *  # noqa: F401, F403\n"
    )
    header = _HEADER_TEMPLATE.format(title="DEXPI 2.0 Core package.", extra_imports=extra)
    parts = [header, _ENTITY_BASE_SRC, _VALUE_BASE_SRC]
    parts.append("\n# --- AbstractDataType type aliases ---\n")
    for a in abstract_dts:
        parts.append(render_abstract_data_type(a))
    parts.append("\n# --- Classes ---\n")
    for c in classes_sorted:
        parts.append(render_class(c, known))
    parts.append(
        "\n# --- Typed PhysicalQuantity subclasses (BoundDataType bindings) ---\n"
    )
    for t in bound_specs:
        parts.append(render_bound_quantity_class(t))
    parts.append("\n# --- model_rebuild for forward refs ---\n")
    for c in classes_sorted:
        parts.append(f"{c.name}.model_rebuild()\n")
    for t in bound_specs:
        parts.append(f"{_bound_class_name(t)}.model_rebuild()\n")
    return "\n".join(parts) + "\n"


def emit_plant_file(reader: DslReader, known: dict[str, object]) -> str:
    classes: list = []
    for t in walk_types(reader.model_by_name["Plant"]):
        if isinstance(t, (ConcreteClass, AbstractClass)):
            classes.append(t)
    classes_sorted = topo_sort(classes)
    extra = (
        "import uuid\n"
        "from datetime import datetime\n"
        "from typing import Any, ClassVar, Optional, Union\n"
        "from pydantic import BaseModel, ConfigDict, Field\n"
        "\n"
        "from diagex.dexpi._generated.core import *  # noqa: F401, F403\n"
        "from diagex.dexpi._generated.enums import *  # noqa: F401, F403\n"
    )
    header = _HEADER_TEMPLATE.format(title="DEXPI 2.0 Plant package.", extra_imports=extra)
    parts = [header]
    parts.append("\n# --- Classes ---\n")
    for c in classes_sorted:
        parts.append(render_class(c, known))
    parts.append("\n# --- model_rebuild for forward refs ---\n")
    for c in classes_sorted:
        parts.append(f"{c.name}.model_rebuild()\n")
    return "\n".join(parts) + "\n"


def emit_process_file(reader: DslReader, known: dict[str, object]) -> str:
    """Emit the DEXPI 2.0 Process namespace classes (v2 Phase D).

    Process classes reference Core (PhysicalQuantity et al) but **not** Plant —
    keeping the import DAG acyclic.
    """
    classes: list = []
    for t in walk_types(reader.model_by_name["Process"]):
        if isinstance(t, (ConcreteClass, AbstractClass)):
            classes.append(t)
    classes_sorted = topo_sort(classes)
    extra = (
        "import uuid\n"
        "from datetime import datetime\n"
        "from typing import Any, ClassVar, Optional, Union\n"
        "from pydantic import BaseModel, ConfigDict, Field\n"
        "\n"
        "from diagex.dexpi._generated.core import *  # noqa: F401, F403\n"
        "from diagex.dexpi._generated.enums import *  # noqa: F401, F403\n"
    )
    header = _HEADER_TEMPLATE.format(
        title="DEXPI 2.0 Process package.", extra_imports=extra
    )
    parts = [header]
    parts.append("\n# --- Classes ---\n")
    for c in classes_sorted:
        parts.append(render_class(c, known))
    parts.append("\n# --- model_rebuild for forward refs ---\n")
    for c in classes_sorted:
        parts.append(f"{c.name}.model_rebuild()\n")
    return "\n".join(parts) + "\n"


def topo_sort(classes: list) -> list:
    """Topological sort by superType edges; tolerates cycles by stable name fallback."""
    by_name = {c.name: c for c in classes}
    visited: set[str] = set()
    out: list = []
    in_progress: set[str] = set()

    def visit(c) -> None:
        if c.name in visited:
            return
        if c.name in in_progress:
            # cycle — pydantic forward refs handle it
            return
        in_progress.add(c.name)
        for sup in c.superTypes:
            if sup.name in by_name:
                visit(by_name[sup.name])
        in_progress.discard(c.name)
        visited.add(c.name)
        out.append(c)

    for c in sorted(classes, key=lambda x: x.qualifiedName_chained):
        visit(c)
    return out


# ---------------------------------------------------------------------------
# Entry point


def emit_all(reader: DslReader, dst_dir: Path) -> dict[str, Path]:
    """Emit all three files under ``dst_dir``. Returns ``{name: path}``."""
    dst_dir.mkdir(parents=True, exist_ok=True)
    (dst_dir / "__init__.py").write_text(
        '"""Auto-generated DEXPI 2.0 pydantic classes. Do not edit."""\n'
        "from diagex.dexpi._generated.enums import *  # noqa: F401, F403\n"
        "from diagex.dexpi._generated.core import *  # noqa: F401, F403\n"
        "from diagex.dexpi._generated.plant import *  # noqa: F401, F403\n"
        "from diagex.dexpi._generated.process import *  # noqa: F401, F403\n",
        encoding="utf-8",
    )
    known = collect_all_named_types(reader, ("Builtin", "Core", "Plant", "Process"))

    bound_specs = collect_bound_quantity_specs(reader, ("Core", "Plant", "Process"))
    _BOUND_QUANTITY_REGISTRY.clear()
    for t in bound_specs:
        _BOUND_QUANTITY_REGISTRY[_bound_key(t)] = _bound_class_name(t)

    out: dict[str, Path] = {}
    for name, content in [
        ("enums.py", emit_enums_file(reader, ("Core", "Plant", "Process"))),
        ("core.py", emit_core_file(reader, known, bound_specs)),
        ("plant.py", emit_plant_file(reader, known)),
        ("process.py", emit_process_file(reader, known)),
    ]:
        path = dst_dir / name
        path.write_text(content, encoding="utf-8")
        out[name] = path
    return out
