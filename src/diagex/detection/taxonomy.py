"""Ordered symbol vocabulary and prompt descriptions, independent of graph export."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class SymbolSpec:
    key: str
    prompt_gloss: str = ""
    subtype_hint_attr: str | None = None
    subtype_hints: dict = field(default_factory=dict)
    drawio_subtype_shapes: dict = field(default_factory=dict)


_EQUIPMENT_REAL: tuple = (
    SymbolSpec(key="tank", prompt_gloss="tank (storage, atmospheric or low-pressure)"),
    SymbolSpec(key="vessel", prompt_gloss="pressure vessel, drum, receiver, knockout pot"),
    SymbolSpec(key="column", prompt_gloss="distillation / absorption / stripping column or tower"),
    SymbolSpec(
        key="heat_exchanger",
        subtype_hint_attr="heat_exchanger_type",
        subtype_hints={"shell_tube": None, "shell-tube": None, "tubular": None, "plate": None},
        prompt_gloss="heat exchanger (shell-and-tube, plate, air cooler)",
        drawio_subtype_shapes={
            "shell_tube": None,
            "shell-tube": None,
            "shell_and_tube": None,
            "tubular": None,
            "fixed_tubes": None,
            "fixed_straight_tubes": None,
            "floating_head": None,
            "u_tube": None,
            "u-tube": None,
            "u_shaped_tubes": None,
            "plate": None,
            "plate_and_frame": None,
            "spiral": None,
            "hairpin": None,
            "double_pipe": None,
            "reboiler": None,
            "coil": None,
            "coil_tubes": None,
            "finned": None,
            "finned_tubes": None,
            "finned_fan": None,
            "air_cooler": None,
            "evaporator": None,
            "thin_film_evaporator": None,
        },
    ),
    SymbolSpec(
        key="pump",
        subtype_hint_attr="pump_type",
        subtype_hints={"centrifugal": None, "reciprocating": None, "rotary": None},
        prompt_gloss="pump (centrifugal, positive-displacement)",
        drawio_subtype_shapes={"centrifugal": None, "reciprocating": None, "rotary": None},
    ),
    SymbolSpec(
        key="compressor",
        subtype_hint_attr="compressor_type",
        subtype_hints={"centrifugal": None, "reciprocating": None, "rotary": None, "axial": None},
        prompt_gloss="gas compressor (centrifugal, reciprocating, rotary, axial)",
        drawio_subtype_shapes={
            "centrifugal": None,
            "reciprocating": None,
            "rotary": None,
            "axial": None,
        },
    ),
    SymbolSpec(
        key="reactor",
        subtype_hint_attr="reactor_type",
        subtype_hints={
            "stirred": None,
            "cstr": None,
            "tubular": None,
            "fixed_bed": None,
            "fluidised_bed": None,
            "fluidized_bed": None,
        },
        prompt_gloss="reaction vessel (batch / CSTR / tubular / fixed- or fluidised-bed)",
        drawio_subtype_shapes={
            "stirred": None,
            "cstr": None,
            "tubular": None,
            "fixed_bed": None,
            "fluidised_bed": None,
            "fluidized_bed": None,
        },
    ),
    SymbolSpec(
        key="agitator", prompt_gloss="agitator / mixer drive on a vessel (shaft + impeller)"
    ),
    SymbolSpec(
        key="filter",
        subtype_hint_attr="filter_type",
        subtype_hints={"liquid": None, "gas": None, "bag": None, "cartridge": None, "plate": None},
        prompt_gloss="filter (bag, cartridge, plate-and-frame, strainer)",
        drawio_subtype_shapes={
            "liquid": None,
            "gas": None,
            "bag": None,
            "cartridge": None,
            "plate": None,
        },
    ),
    SymbolSpec(
        key="separator",
        subtype_hint_attr="separator_type",
        subtype_hints={
            "gravity": None,
            "gravitational": None,
            "mechanical": None,
            "electrical": None,
            "electrostatic": None,
            "scrubbing": None,
            "scrubber": None,
        },
        prompt_gloss="two-/three-phase separator (gravity, mechanical, scrubber)",
        drawio_subtype_shapes={
            "gravity": None,
            "gravitational": None,
            "mechanical": None,
            "electrical": None,
            "electrostatic": None,
            "scrubbing": None,
            "scrubber": None,
        },
    ),
    SymbolSpec(
        key="fired_heater", prompt_gloss="fired heater, furnace, process heater (fuel-fired)"
    ),
    SymbolSpec(
        key="cooling_tower",
        subtype_hint_attr="cooling_tower_type",
        subtype_hints={"wet": None, "dry": None},
        prompt_gloss="cooling tower (wet / dry, forced- or natural-draft)",
        drawio_subtype_shapes={"wet": None, "dry": None},
    ),
    SymbolSpec(
        key="fan_blower",
        subtype_hint_attr="fan_blower_type",
        subtype_hints={
            "axial": None,
            "radial": None,
            "centrifugal_fan": None,
            "centrifugal_blower": None,
            "axial_blower": None,
            "blower": None,
        },
        prompt_gloss="fan or blower (axial, radial / centrifugal)",
    ),
    SymbolSpec(
        key="turbine",
        subtype_hint_attr="turbine_type",
        subtype_hints={"steam": None, "gas": None},
        prompt_gloss="turbine (steam, gas, expander)",
    ),
    SymbolSpec(
        key="centrifuge",
        subtype_hint_attr="centrifuge_type",
        subtype_hints={"sedimental": None, "sedimenting": None, "filtering": None},
        prompt_gloss="centrifuge (sedimenting or filtering, for solid-liquid separation)",
    ),
    SymbolSpec(
        key="dryer",
        subtype_hint_attr="dryer_type",
        subtype_hints={
            "convection": None,
            "convective": None,
            "heated_surface": None,
            "contact": None,
        },
        prompt_gloss="dryer (convection / heated-surface)",
    ),
    SymbolSpec(
        key="weigher",
        subtype_hint_attr="weigher_type",
        subtype_hints={"batch": None, "continuous": None},
        prompt_gloss="weigher / scale (batch or continuous)",
    ),
    SymbolSpec(
        key="mixer",
        subtype_hint_attr="mixer_type",
        subtype_hints={"static": None, "in_line": None, "inline": None, "rotary": None},
        prompt_gloss="mixer (static / in-line / rotary)",
    ),
    SymbolSpec(
        key="transport_system",
        subtype_hint_attr="transport_type",
        subtype_hints={
            "stationary": None,
            "mobile": None,
            "loading": None,
            "unloading": None,
            "loading_unloading": None,
        },
        prompt_gloss="conveyor / loading-unloading / mobile transport system",
    ),
    SymbolSpec(key="burner", prompt_gloss="burner (gas/oil/duct burner)"),
    SymbolSpec(key="air_cooler", prompt_gloss="air cooler / fin-fan cooler"),
)
_EQUIPMENT_SENTINELS: tuple = (
    SymbolSpec(
        key="unclassified_equipment",
        prompt_gloss="unknown / non-standard symbol - describe in source_quote",
    ),
)
EQUIPMENT_REGISTRY: tuple = _EQUIPMENT_REAL + _EQUIPMENT_SENTINELS
EQUIPMENT_CLASS_ROUTER_VALVE_KEY = "valve"
_VALVE_REAL: tuple = (
    SymbolSpec(key="gate", prompt_gloss="gate valve - on/off; full-bore linear gate"),
    SymbolSpec(key="globe", prompt_gloss="globe valve - throttling; rounded body"),
    SymbolSpec(key="check", prompt_gloss="check valve - flow in one direction only"),
    SymbolSpec(key="ball", prompt_gloss="ball valve - quarter-turn; bore through a sphere"),
    SymbolSpec(key="butterfly", prompt_gloss="butterfly valve - quarter-turn disc"),
    SymbolSpec(key="control", prompt_gloss="control valve - actuated, modulating process variable"),
    SymbolSpec(
        key="safety_relief",
        prompt_gloss="safety / relief / PSV - spring-loaded over-pressure protection",
    ),
    SymbolSpec(key="three_way", prompt_gloss="three-way valve - diverting / mixing on a branch"),
    SymbolSpec(
        key="needle", prompt_gloss="needle valve - fine throttling, small-bore instrument service"
    ),
    SymbolSpec(key="plug", prompt_gloss="plug valve - quarter-turn tapered plug, gas service"),
    SymbolSpec(
        key="strainer", prompt_gloss="in-line strainer (Y-type, T-type) - coarse particle catch"
    ),
    SymbolSpec(
        key="rupture_disc",
        prompt_gloss="rupture disc / bursting disc - one-shot over-pressure protection",
    ),
)
_VALVE_SENTINELS: tuple = (
    SymbolSpec(key="other", prompt_gloss="valve not matching the above categories"),
)
VALVE_REGISTRY: tuple = _VALVE_REAL + _VALVE_SENTINELS
_INSTRUMENT_REAL: tuple = (
    SymbolSpec(key="indicator", prompt_gloss="local or panel indicator (I, FI, PI, TI, LI)"),
    SymbolSpec(
        key="transmitter", prompt_gloss="transmitter (FT, PT, TT, LT) - sends signal to DCS"
    ),
    SymbolSpec(key="controller", prompt_gloss="controller (FC, PC, TC, LC, FIC, …)"),
    SymbolSpec(key="recorder", prompt_gloss="recorder (FR, PR, TR, LR)"),
    SymbolSpec(key="element", prompt_gloss="primary element (FE, TE, LE, AE)"),
    SymbolSpec(key="switch", prompt_gloss="switch (FS, PS, TS, LS, PSH, LSL)"),
    SymbolSpec(key="alarm", prompt_gloss="alarm (FA, PA, TA, LA, PAH, LAL)"),
    SymbolSpec(key="valve_actuator", prompt_gloss="valve actuator / positioner loop"),
)
_INSTRUMENT_SENTINELS: tuple = (
    SymbolSpec(
        key="unclassified_instrument", prompt_gloss="instrument with unrecognised function letters"
    ),
)
INSTRUMENT_REGISTRY: tuple = _INSTRUMENT_REAL + _INSTRUMENT_SENTINELS
INSTRUMENT_CLASS_REGISTRY: tuple = (
    SymbolSpec(
        key="control_loop",
        prompt_gloss="closed-loop control (has controller + final control element)",
    ),
    SymbolSpec(
        key="instrumentation_loop",
        prompt_gloss="indicator / transmitter / read-only loop (default if omitted)",
    ),
)
INSTRUMENT_CLASS_KEYS: tuple = tuple(s.key for s in INSTRUMENT_CLASS_REGISTRY)


def render_instrument_class_slash_list() -> str:
    return "/".join(s.key for s in INSTRUMENT_CLASS_REGISTRY)


EQUIPMENT_CLASS_KEYS: tuple = tuple(s.key for s in EQUIPMENT_REGISTRY)
VALVE_TYPE_KEYS: tuple = tuple(s.key for s in VALVE_REGISTRY)
ACTUATION_TYPE_KEYS: tuple = (
    "manual",
    "solenoid",
    "electric_motor",
    "pneumatic",
    "hydraulic",
    "spring",
    "other",
)
INSTRUMENT_FUNCTION_KEYS: tuple = tuple(s.key for s in INSTRUMENT_REGISTRY)


def render_equipment_taxonomy_enum() -> str:
    """Render the equipment_class enum as a comma-separated brace-list.

    Output shape: ``{tank, vessel, column, heat_exchanger, pump, compressor,
    unclassified_equipment}`` - matches the pre-refactor prompt verbatim.
    """
    return "{" + ", ".join(s.key for s in EQUIPMENT_REGISTRY) + "}"


def render_valve_type_enum() -> str:
    return "{" + ", ".join(s.key for s in VALVE_REGISTRY) + "}"


def render_instrument_function_enum() -> str:
    return "{" + ", ".join(s.key for s in INSTRUMENT_REGISTRY) + "}"


def render_equipment_slash_list() -> str:
    """Slash-separated equipment keys for compact docstrings (e.g. annotate tool)."""
    return "/".join(s.key for s in EQUIPMENT_REGISTRY)


def render_valve_slash_list() -> str:
    return "/".join(s.key for s in VALVE_REGISTRY)


def render_instrument_slash_list() -> str:
    return "/".join(s.key for s in INSTRUMENT_REGISTRY)


def render_equipment_subtype_hints() -> str:
    """Render a comma-separated list of subtype-hint attribute names.

    Used in the phase-2 prompt's "optional free-text hints" bullet. Only
    entries that actually define a subtype hint contribute.
    """
    hints = [s.subtype_hint_attr for s in EQUIPMENT_REGISTRY if s.subtype_hint_attr]
    seen: set[str] = set()
    deduped: list[str] = []
    for h in hints:
        assert h is not None
        if h not in seen:
            seen.add(h)
            deduped.append(h)
    return ", ".join(deduped)


def render_equipment_subtype_values() -> str:
    """Render the prompt-side **enumeration of valid subtype values** for each
    subtype-hint attribute.

    Without this, the agent has to invent strings (it has been emitting things
    like ``shell_and_tube`` while our hint maps only knew ``shell_tube``).
    Now every spec contributes its known keys (union of pydexpi-class hints
    and drawio-shape hints, deduped, in registry order) so the agent picks
    from a closed list.

    Output (each line indented for inline embedding under a bullet):

    .. code-block:: text

        heat_exchanger_type ∈ {shell_and_tube, floating_head, u_tube, plate, ...}
        pump_type ∈ {centrifugal, reciprocating, rotary}
        compressor_type ∈ {centrifugal, reciprocating, rotary, axial}
        ...

    Append-only invariant: as long as new entries are appended at the end of
    each spec's ``subtype_hints`` / ``drawio_subtype_shapes`` mappings, the
    rendered prefix bytes stay stable up to the new entry - minor cache hit
    only on the affected attribute line.
    """
    lines: list[str] = []
    seen_attrs: set[str] = set()
    for spec in EQUIPMENT_REGISTRY:
        attr = spec.subtype_hint_attr
        if not attr or attr in seen_attrs:
            continue
        seen_attrs.add(attr)
        keys: list[str] = []
        seen_keys: set[str] = set()
        for k in list(spec.subtype_hints.keys()) + list(spec.drawio_subtype_shapes.keys()):
            if k in seen_keys:
                continue
            seen_keys.add(k)
            keys.append(k)
        if not keys:
            continue
        lines.append(f"    {attr} ∈ {{" + ", ".join(keys) + "}")
    return "\n".join(lines)


def render_legend_equipment_list() -> str:
    """Space-separated equipment keys for the legend-extraction prompt's bullet.

    Matches the pre-refactor wording: ``tank, vessel, column, heat_exchanger,
    pump, compressor, valve, unclassified_equipment``.

    The legend prompt surfaces ``valve`` as an equipment_class alias (it's the
    router key into VALVE_REGISTRY); the phase-2 extraction prompt does not.
    """
    keys = [s.key for s in EQUIPMENT_REGISTRY if s.key != "unclassified_equipment"]
    keys.append(EQUIPMENT_CLASS_ROUTER_VALVE_KEY)
    keys.append("unclassified_equipment")
    return ", ".join(keys)


def render_legend_valve_list() -> str:
    return ", ".join(s.key for s in VALVE_REGISTRY)


def render_legend_instrument_list() -> str:
    return ", ".join(s.key for s in INSTRUMENT_REGISTRY)
