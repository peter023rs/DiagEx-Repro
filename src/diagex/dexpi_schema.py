"""Authoritative DEXPI subset registry (spec §7.2.1).

Single source of truth for the equipment / valve / instrument keys that the
extraction pipeline supports. Downstream consumers read from the registries
defined here instead of hand-maintaining parallel lists:

  - ``vision.legend_models`` — ``EquipmentClass`` / ``ValveType`` /
    ``InstrumentFunction`` ``Literal``s are generated from registry keys.
  - ``extractors.dexpi_builder`` — dispatches a ``ReconciledNode`` to the right
    DEXPI 2.0 class via :func:`equipment_spec_for` / :func:`valve_spec_for`.
  - ``llm.prompts.phase2_pid`` / ``llm.prompts.phase2_legend`` — render the
    taxonomy bullets in their cached system prompts via
    :func:`render_equipment_taxonomy` etc.
  - ``agent.tools`` — the ``annotate`` tool's ``attributes`` docstring is
    rendered from the registries.
  - ``extractors.dexpi_svg`` — reads ``svg_fill`` / ``svg_glyph`` per class.

Adding a class = one entry in the relevant registry. No other files need
edits beyond (optionally) a new SVG glyph function.

Ordering is load-bearing. The phase-2 system prompt is cache-pinned (spec
§12.1.2); reordering or inserting entries mid-list invalidates every cached
session. **Append only.**

Graceful degradation: when a named DEXPI 2.0 class is absent from the
generated model (e.g. DEXPI 2.0 dropped the Reactor hierarchy), the registry
records the spec with ``pydexpi_class=None``. The builder falls back to
``eq.CustomEquipment`` / ``pp.CustomOperatedValve`` with the registry key
recorded as ``typeName``, so unsupported classes still round-trip through the
pipeline — they just do not get typed DEXPI objects. (The historical
``pydexpi_class`` field name is kept for diff hygiene; it now holds the
DEXPI 2.0 class.)
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from diagex.dexpi.model import equipment as eq
from diagex.dexpi.model import instrumentation as inst
from diagex.dexpi.model import piping as pp


# ---------------------------------------------------------------------------
# Spec dataclasses
# ---------------------------------------------------------------------------


def _resolve(module: Any, name: str) -> type | None:
    """Return ``getattr(module, name)`` or ``None`` if the class does not exist."""
    return getattr(module, name, None)


@dataclass(frozen=True)
class EquipmentSpec:
    """One equipment class the extractor can emit.

    ``pydexpi_class`` may be ``None`` to indicate the installed pydexpi lacks
    the class; callers treat this as a ``CustomEquipment`` fallback.
    """

    key: str                                     # agent attribute value, e.g. "tank"
    pydexpi_class: type | None                   # base pydexpi class, or None
    subtype_hint_attr: str | None = None         # attribute key carrying the subtype, e.g. "pump_type"
    subtype_hints: Mapping[str, type | None] = field(default_factory=dict)
    prompt_gloss: str = ""                       # short description for prompt rendering
    svg_fill: str = "#e5e7eb"                    # fill colour key for dexpi_svg
    svg_glyph: str = ""                          # name of glyph renderer (empty = unclassified rect)
    # draw.io "Process Engineering" stencil for the base class. Format is
    # the value of the mxCell `shape=` style fragment (without the `shape=`
    # prefix), e.g. ``mxgraph.pid.vessels.tank``. Empty = fall back to a
    # generic rounded rectangle in dexpi_drawio. May include parameter
    # fragments separated by `;` (e.g. ``mxgraph.pid2misc.column;columnType=tray``).
    drawio_shape: str = ""
    # Optional per-subtype override of drawio_shape (parallel to subtype_hints).
    drawio_subtype_shapes: Mapping[str, str] = field(default_factory=dict)
    # Recommended (natural_w, natural_h) of the stencil, in drawio canvas
    # units. Sourced from the dimensions the diagrams.net sidebar palette
    # uses when the user drags the stencil onto the canvas. When set, the
    # renderer fits the cell into the agent's bbox preserving this ratio
    # and never grows past these dimensions — so a stencil with a strong
    # intrinsic shape (pump, fan, turbine) doesn't get skewed or balloon
    # when the agent's bbox happens to include a chunk of label whitespace.
    # Leave None for stencils designed to scale freely (tanks, vessels,
    # columns, heat exchangers, separators, furnaces, cooling towers).
    drawio_natural_size: tuple[int, int] | None = None

    def resolve(self, attrs: Mapping[str, Any]) -> tuple[type | None, bool]:
        """Pick a pydexpi class for this spec given agent-provided attributes.

        Returns ``(class, is_base)``:
          - ``class`` is the pydexpi class to instantiate, or ``None`` if neither
            the subtype hint nor the base class is available (caller falls back
            to ``CustomEquipment``).
          - ``is_base`` is True when no subtype hint matched — the caller used
            the spec's base class.
        """
        if self.subtype_hint_attr:
            hint = str(attrs.get(self.subtype_hint_attr, "")).strip().lower()
            if hint:
                for alias, sub_cls in self.subtype_hints.items():
                    if alias == hint and sub_cls is not None:
                        return sub_cls, False
        if self.pydexpi_class is not None:
            return self.pydexpi_class, True
        return None, True


@dataclass(frozen=True)
class ValveSpec:
    """One valve type emitted as ``kind=equipment`` with ``valve_type=<key>``."""

    key: str
    pydexpi_class: type | None
    control_intent: bool = False                 # agent emits control-intent custom attr
    prompt_gloss: str = ""
    svg_fill: str = "#fcd34d"
    svg_glyph: str = ""                          # optional override; empty = standard bowtie
    # draw.io shape style. Most valves resolve to the parameterised
    # ``mxgraph.pid2valves.valve;valveType=<x>`` style; a few specialty
    # entries (strainer, rupture_disc) point at separate stencils in
    # ``mxgraph.pid.piping`` / ``mxgraph.pid.fittings``.
    drawio_shape: str = ""
    # Default actuator parameter for the parameterised valve shape (e.g.
    # ``man``, ``diaph``, ``spring``, ``none``). The renderer overrides this
    # when a node carries an ``actuation`` attribute.
    drawio_default_actuator: str = "none"


@dataclass(frozen=True)
class InstrumentSpec:
    """One instrument-function value.

    Instruments presently resolve to ``inst.ProcessInstrumentationFunction``
    regardless of key — the value is recorded as a custom attribute. The
    registry exists so the Literal enum and prompt taxonomy stay consistent,
    and so the Layer-2 upgrade path (``instrument_class``) has a stable
    pivot point.
    """

    key: str
    prompt_gloss: str = ""
    # Optional typed-instrument upgrade path; populated in Layer 2.
    pydexpi_class: type | None = None
    # draw.io shape: every instrument resolves to ``mxgraph.pid2inst.discInst``
    # (the ISA-5.1 bubble) plus a mounting flag. Values: ``room`` (control
    # room — horizontal divider line drawn), ``field`` (no divider — local
    # to process), ``inaccessible`` (dashed divider), ``local`` (local panel).
    drawio_mounting: str = "field"


# ---------------------------------------------------------------------------
# Equipment registry (spec §7.2.1 — v0 baseline + v0.2 additions)
# ---------------------------------------------------------------------------
#
# Structure: ``_EQUIPMENT_REAL`` holds real class specs in append-only order;
# ``_EQUIPMENT_SENTINELS`` holds the unclassified fallback. They concatenate
# into ``EQUIPMENT_REGISTRY`` with the sentinel always last, so the rendered
# prompt reads naturally (``{tank, …, reactor, filter, unclassified_equipment}``)
# and adding new real classes does not reorder the sentinel.
#
# DEXPI 2.0 gaps (confirmed by probing the generated model):
#   - The ``Reactor`` hierarchy is absent — reactors degrade to
#     ``CustomEquipment`` with ``typeName="reactor"``; sub-type hints are
#     recorded as custom attrs.
#   - ``ThreeWayValve`` is absent — degrades to ``CustomOperatedValve``.


_EQUIPMENT_REAL: tuple[EquipmentSpec, ...] = (
    # -- v0 baseline (spec §7.2.1) --
    EquipmentSpec(
        key="tank",
        pydexpi_class=_resolve(eq, "Tank"),
        prompt_gloss="tank (storage, atmospheric or low-pressure)",
        svg_fill="#dbeafe",
        svg_glyph="tank",
        drawio_shape="mxgraph.pid.vessels.tank",
    ),
    EquipmentSpec(
        key="vessel",
        pydexpi_class=_resolve(eq, "Vessel"),
        prompt_gloss="pressure vessel, drum, receiver, knockout pot",
        svg_fill="#dbeafe",
        svg_glyph="vessel",
        drawio_shape="mxgraph.pid.vessels.pressurized_vessel",
    ),
    EquipmentSpec(
        key="column",
        pydexpi_class=_resolve(eq, "ProcessColumn"),
        prompt_gloss="distillation / absorption / stripping column or tower",
        svg_fill="#bfdbfe",
        svg_glyph="column",
        # The pid2 column stencil takes a columnType parameter; default to
        # the tray column (most common). Subtype-driven overrides below.
        drawio_shape="mxgraph.pid2misc.column;columnType=tray",
    ),
    EquipmentSpec(
        key="heat_exchanger",
        pydexpi_class=_resolve(eq, "HeatExchanger"),
        subtype_hint_attr="heat_exchanger_type",
        subtype_hints={
            "shell_tube": _resolve(eq, "TubularHeatExchanger"),
            "shell-tube": _resolve(eq, "TubularHeatExchanger"),
            "tubular": _resolve(eq, "TubularHeatExchanger"),
            "plate": _resolve(eq, "PlateHeatExchanger"),
        },
        prompt_gloss="heat exchanger (shell-and-tube, plate, air cooler)",
        svg_fill="#fde68a",
        svg_glyph="heat_exchanger",
        drawio_shape="mxgraph.pid.heat_exchangers.shell_and_tube_heat_exchanger_1",
        drawio_subtype_shapes={
            # Shell-and-tube family — multiple aliases the LLM is likely to emit.
            "shell_tube": "mxgraph.pid.heat_exchangers.shell_and_tube_heat_exchanger_1",
            "shell-tube": "mxgraph.pid.heat_exchangers.shell_and_tube_heat_exchanger_1",
            "shell_and_tube": "mxgraph.pid.heat_exchangers.shell_and_tube_heat_exchanger_1",
            "tubular": "mxgraph.pid.heat_exchangers.fixed_straight_tubes_heat_exchanger",
            "fixed_tubes": "mxgraph.pid.heat_exchangers.fixed_straight_tubes_heat_exchanger",
            "fixed_straight_tubes": "mxgraph.pid.heat_exchangers.fixed_straight_tubes_heat_exchanger",
            "floating_head": "mxgraph.pid.heat_exchangers.heat_exchanger_(floating_head)",
            "u_tube": "mxgraph.pid.heat_exchangers.u-tube_heat_exchanger",
            "u-tube": "mxgraph.pid.heat_exchangers.u-tube_heat_exchanger",
            "u_shaped_tubes": "mxgraph.pid.heat_exchangers.u_shaped_tubes_heat_exchanger",
            # Plate / spiral / hairpin / reboiler / coiled / finned-tube variants.
            "plate": "mxgraph.pid.heat_exchangers.heat_exchanger_(plate)",
            "plate_and_frame": "mxgraph.pid.heat_exchangers.plate_and_frame_heat_exchanger",
            "spiral": "mxgraph.pid.heat_exchangers.heat_exchanger_(spiral)",
            "hairpin": "mxgraph.pid.heat_exchangers.hairpin_exchanger",
            "double_pipe": "mxgraph.pid.heat_exchangers.double_pipe_heat_exchanger",
            "reboiler": "mxgraph.pid.heat_exchangers.reboiler",
            "coil": "mxgraph.pid.heat_exchangers.heat_exchanger_(coil_tubes)",
            "coil_tubes": "mxgraph.pid.heat_exchangers.heat_exchanger_(coil_tubes)",
            "finned": "mxgraph.pid.heat_exchangers.heat_exchanger_(finned_tubes)",
            "finned_tubes": "mxgraph.pid.heat_exchangers.heat_exchanger_(finned_tubes)",
            "finned_fan": "mxgraph.pid.heat_exchangers.heat_exchanger_(finned_tubes,_fan)",
            "air_cooler": "mxgraph.pid.heat_exchangers.heat_exchanger_(finned_tubes,_fan)",
            "evaporator": "mxgraph.pid.heat_exchangers.thin-film_evaporator",
            "thin_film_evaporator": "mxgraph.pid.heat_exchangers.thin-film_evaporator",
        },
    ),
    EquipmentSpec(
        key="pump",
        pydexpi_class=_resolve(eq, "Pump"),
        subtype_hint_attr="pump_type",
        subtype_hints={
            "centrifugal": _resolve(eq, "CentrifugalPump"),
            "reciprocating": _resolve(eq, "ReciprocatingPump"),
            "rotary": _resolve(eq, "RotaryPump"),
        },
        prompt_gloss="pump (centrifugal, positive-displacement)",
        svg_fill="#bbf7d0",
        svg_glyph="pump",
        drawio_shape="mxgraph.pid.pumps.centrifugal_pump_1",
        drawio_subtype_shapes={
            "centrifugal": "mxgraph.pid.pumps.centrifugal_pump_1",
            "reciprocating": "mxgraph.pid.pumps.peristaltic",
            "rotary": "mxgraph.pid.pumps.gear_pump",
        },
        drawio_natural_size=(60, 60),
    ),
    EquipmentSpec(
        key="compressor",
        pydexpi_class=_resolve(eq, "Compressor"),
        subtype_hint_attr="compressor_type",
        subtype_hints={
            "centrifugal": _resolve(eq, "CentrifugalCompressor"),
            "reciprocating": _resolve(eq, "ReciprocatingCompressor"),
            "rotary": _resolve(eq, "RotaryCompressor"),
            "axial": _resolve(eq, "AxialCompressor"),
        },
        prompt_gloss="gas compressor (centrifugal, reciprocating, rotary, axial)",
        svg_fill="#a7f3d0",
        svg_glyph="compressor",
        drawio_shape="mxgraph.pid.compressors.compressor",
        drawio_subtype_shapes={
            "centrifugal": "mxgraph.pid.compressors.centrifugal_compressor",
            "reciprocating": "mxgraph.pid.compressors.reciprocating_compressor",
            "rotary": "mxgraph.pid.compressors.rotary_compressor",
            # No dedicated axial-compressor stencil; reuse the generic.
            "axial": "mxgraph.pid.compressors.compressor",
        },
        drawio_natural_size=(60, 60),
    ),

    # -- v0.2 additions (P0): reactors, agitators, filters --
    EquipmentSpec(
        # DEXPI 2.0 has no Reactor class; typeName carries the key on CustomEquipment.
        key="reactor",
        pydexpi_class=_resolve(eq, "Reactor"),
        subtype_hint_attr="reactor_type",
        subtype_hints={
            "stirred": _resolve(eq, "StirredTankReactor"),
            "cstr": _resolve(eq, "StirredTankReactor"),
            "tubular": _resolve(eq, "TubularReactor"),
            "fixed_bed": _resolve(eq, "FixedBedReactor"),
            "fluidised_bed": _resolve(eq, "FluidisedBedReactor"),
            "fluidized_bed": _resolve(eq, "FluidisedBedReactor"),   # US spelling alias
        },
        prompt_gloss="reaction vessel (batch / CSTR / tubular / fixed- or fluidised-bed)",
        svg_fill="#fecaca",                      # soft red — chemistry/energy
        svg_glyph="reactor",
        drawio_shape="mxgraph.pid.vessels.reactor",
        drawio_subtype_shapes={
            "stirred": "mxgraph.pid.vessels.mixing_reactor",
            "cstr": "mxgraph.pid.vessels.mixing_reactor",
            "tubular": "mxgraph.pid.vessels.reactor",
            # Fixed/fluidised beds have no vessel stencil — re-use the column shape.
            "fixed_bed": "mxgraph.pid2misc.column;columnType=fixed",
            "fluidised_bed": "mxgraph.pid2misc.column;columnType=fluid",
            "fluidized_bed": "mxgraph.pid2misc.column;columnType=fluid",
        },
    ),
    EquipmentSpec(
        key="agitator",
        pydexpi_class=_resolve(eq, "Agitator"),
        prompt_gloss="agitator / mixer drive on a vessel (shaft + impeller)",
        svg_fill="#ddd6fe",                      # soft violet — mixing
        svg_glyph="agitator",
        drawio_shape="mxgraph.pid.agitators.agitator_(impeller)",
        # Vertical stencil — motor on top, shaft + impeller below.
        drawio_natural_size=(50, 80),
    ),
    EquipmentSpec(
        key="filter",
        pydexpi_class=_resolve(eq, "Filter"),
        subtype_hint_attr="filter_type",
        subtype_hints={
            "liquid": _resolve(eq, "LiquidFilter"),
            "gas": _resolve(eq, "GasFilter"),
            "bag": _resolve(eq, "FilterUnit"),
            "cartridge": _resolve(eq, "FilterUnit"),
            "plate": _resolve(eq, "FilterUnit"),
        },
        prompt_gloss="filter (bag, cartridge, plate-and-frame, strainer)",
        svg_fill="#c7d2fe",                      # soft indigo — separation
        svg_glyph="filter",
        drawio_shape="mxgraph.pid.filters.filter",
        drawio_subtype_shapes={
            "liquid": "mxgraph.pid.filters.liquid_filter",
            "gas": "mxgraph.pid.filters.gas_filter",
            "bag": "mxgraph.pid.filters.liquid_filter_(bag,_candle,_cartridge)",
            "cartridge": "mxgraph.pid.filters.liquid_filter_(bag,_candle,_cartridge)",
            "plate": "mxgraph.pid.filters.press_filter",
        },
    ),

    # -- v0.2 additions (P1): separators, fired heaters, cooling towers --
    EquipmentSpec(
        key="separator",
        pydexpi_class=_resolve(eq, "Separator"),
        subtype_hint_attr="separator_type",
        subtype_hints={
            "gravity": _resolve(eq, "GravitationalSeparator"),
            "gravitational": _resolve(eq, "GravitationalSeparator"),
            "mechanical": _resolve(eq, "MechanicalSeparator"),
            "electrical": _resolve(eq, "ElectricalSeparator"),
            "electrostatic": _resolve(eq, "ElectricalSeparator"),
            "scrubbing": _resolve(eq, "ScrubbingSeparator"),
            "scrubber": _resolve(eq, "ScrubbingSeparator"),
        },
        prompt_gloss="two-/three-phase separator (gravity, mechanical, scrubber)",
        svg_fill="#a5f3fc",                      # cyan — phase separation
        svg_glyph="separator",
        drawio_shape="mxgraph.pid.separators.gravity_separator,_settling_chamber",
        drawio_subtype_shapes={
            "gravity": "mxgraph.pid.separators.gravity_separator,_settling_chamber",
            "gravitational": "mxgraph.pid.separators.gravity_separator,_settling_chamber",
            "mechanical": "mxgraph.pid.separators.impact_separator",
            "electrical": "mxgraph.pid.separators.separator_(electrostatic_precipitator)",
            "electrostatic": "mxgraph.pid.separators.separator_(electrostatic_precipitator)",
            "scrubbing": "mxgraph.pid.separators.separator_(wet_scrubber)",
            "scrubber": "mxgraph.pid.separators.separator_(wet_scrubber)",
        },
    ),
    EquipmentSpec(
        # Fired heater maps to pydexpi Furnace class.
        key="fired_heater",
        pydexpi_class=_resolve(eq, "Furnace"),
        prompt_gloss="fired heater, furnace, process heater (fuel-fired)",
        svg_fill="#fed7aa",                      # warm orange — combustion
        svg_glyph="fired_heater",
        drawio_shape="mxgraph.pid.vessels.furnace",
    ),
    EquipmentSpec(
        key="cooling_tower",
        pydexpi_class=_resolve(eq, "CoolingTower"),
        subtype_hint_attr="cooling_tower_type",
        subtype_hints={
            "wet": _resolve(eq, "WetCoolingTower"),
            "dry": _resolve(eq, "DryCoolingTower"),
        },
        prompt_gloss="cooling tower (wet / dry, forced- or natural-draft)",
        svg_fill="#bae6fd",                      # sky blue — cooling utility
        svg_glyph="cooling_tower",
        drawio_shape="mxgraph.pid.misc.cooling_tower",
        drawio_subtype_shapes={
            "wet": "mxgraph.pid.misc.cooling_tower_(wet,_forced_draught)",
            "dry": "mxgraph.pid.misc.cooling_tower_(dry,_forced_draught)",
        },
    ),

    # -- v0.2 additions (P2): fans/blowers, turbines, centrifuges --
    EquipmentSpec(
        key="fan_blower",
        pydexpi_class=_resolve(eq, "Fan"),
        subtype_hint_attr="fan_blower_type",
        subtype_hints={
            "axial": _resolve(eq, "AxialFan"),
            "radial": _resolve(eq, "RadialFan"),
            "centrifugal_fan": _resolve(eq, "RadialFan"),
            "centrifugal_blower": _resolve(eq, "CentrifugalBlower"),
            "axial_blower": _resolve(eq, "AxialBlower"),
            "blower": _resolve(eq, "Blower"),
        },
        prompt_gloss="fan or blower (axial, radial / centrifugal)",
        svg_fill="#d1fae5",                      # mint — air-moving
        svg_glyph="fan_blower",
        # The pid2 fan shape is parameterised; "common" is the generic glyph.
        drawio_shape="mxgraph.pid2misc.fan;fanType=common",
        drawio_natural_size=(50, 50),
    ),
    EquipmentSpec(
        key="turbine",
        pydexpi_class=_resolve(eq, "Turbine"),
        subtype_hint_attr="turbine_type",
        subtype_hints={
            "steam": _resolve(eq, "SteamTurbine"),
            "gas": _resolve(eq, "GasTurbine"),
        },
        prompt_gloss="turbine (steam, gas, expander)",
        svg_fill="#fcd34d",                      # amber — rotating power
        svg_glyph="turbine",
        # The drawio "Turbine" stencil ships under the pumps library.
        drawio_shape="mxgraph.pid.pumps.turbine",
        drawio_natural_size=(60, 60),
    ),
    EquipmentSpec(
        key="centrifuge",
        pydexpi_class=_resolve(eq, "Centrifuge"),
        subtype_hint_attr="centrifuge_type",
        subtype_hints={
            "sedimental": _resolve(eq, "SedimentalCentrifuge"),
            "sedimenting": _resolve(eq, "SedimentalCentrifuge"),
            "filtering": _resolve(eq, "FilteringCentrifuge"),
        },
        prompt_gloss="centrifuge (sedimenting or filtering, for solid-liquid separation)",
        svg_fill="#e9d5ff",                      # lilac — rotating separation
        svg_glyph="centrifuge",
        # No dedicated centrifuge stencil; reuse the impact-separator silhouette
        # (rotating drum + outlet) as the closest visual match.
        drawio_shape="mxgraph.pid.separators.impact_separator",
        drawio_natural_size=(60, 60),
    ),

    # -- v2 Phase E additions: dryers, weighers, mixers, transport, burners, air coolers --
    EquipmentSpec(
        key="dryer",
        pydexpi_class=_resolve(eq, "Dryer"),
        subtype_hint_attr="dryer_type",
        subtype_hints={
            "convection": _resolve(eq, "ConvectionDryer"),
            "convective": _resolve(eq, "ConvectionDryer"),
            "heated_surface": _resolve(eq, "HeatedSurfaceDryer"),
            "contact": _resolve(eq, "HeatedSurfaceDryer"),
        },
        prompt_gloss="dryer (convection / heated-surface)",
        svg_fill="#fed7aa",                      # peach — heat
        svg_glyph="dryer",
        drawio_shape="mxgraph.pid.misc.dryer",
        drawio_natural_size=(60, 60),
    ),
    EquipmentSpec(
        key="weigher",
        pydexpi_class=_resolve(eq, "Weigher"),
        subtype_hint_attr="weigher_type",
        subtype_hints={
            "batch": _resolve(eq, "BatchWeigher"),
            "continuous": _resolve(eq, "ContinuousWeigher"),
        },
        prompt_gloss="weigher / scale (batch or continuous)",
        svg_fill="#cffafe",                      # icy — measurement
        svg_glyph="weigher",
        drawio_shape="mxgraph.pid.misc.scale",
        drawio_natural_size=(40, 40),
    ),
    EquipmentSpec(
        key="mixer",
        pydexpi_class=_resolve(eq, "Mixer"),
        subtype_hint_attr="mixer_type",
        subtype_hints={
            "static": _resolve(eq, "StaticMixer"),
            "in_line": _resolve(eq, "InLineMixer"),
            "inline": _resolve(eq, "InLineMixer"),
            "rotary": _resolve(eq, "RotaryMixer"),
        },
        prompt_gloss="mixer (static / in-line / rotary)",
        svg_fill="#fef3c7",                      # cream — blending
        svg_glyph="mixer",
        drawio_shape="mxgraph.pid.misc.mixer",
        drawio_natural_size=(50, 50),
    ),
    EquipmentSpec(
        key="transport_system",
        pydexpi_class=_resolve(eq, "StationaryTransportSystem"),
        subtype_hint_attr="transport_type",
        subtype_hints={
            "stationary": _resolve(eq, "StationaryTransportSystem"),
            "mobile": _resolve(eq, "MobileTransportSystem"),
            "loading": _resolve(eq, "LoadingUnloadingSystem"),
            "unloading": _resolve(eq, "LoadingUnloadingSystem"),
            "loading_unloading": _resolve(eq, "LoadingUnloadingSystem"),
        },
        prompt_gloss="conveyor / loading-unloading / mobile transport system",
        svg_fill="#fde68a",                      # mustard — moving solids
        svg_glyph="transport",
        drawio_shape="mxgraph.pid.conveyors.conveyor",
        drawio_natural_size=(80, 30),
    ),
    EquipmentSpec(
        key="burner",
        pydexpi_class=_resolve(eq, "Burner"),
        prompt_gloss="burner (gas/oil/duct burner)",
        svg_fill="#fca5a5",                      # rose — flame
        svg_glyph="burner",
        drawio_shape="mxgraph.pid.heat_exchangers.burner",
        drawio_natural_size=(40, 40),
    ),
    EquipmentSpec(
        key="air_cooler",
        pydexpi_class=_resolve(eq, "AirCoolingSystem"),
        prompt_gloss="air cooler / fin-fan cooler",
        svg_fill="#bfdbfe",                      # sky — air
        svg_glyph="air_cooler",
        drawio_shape="mxgraph.pid.heat_exchangers.air_cooler",
        drawio_natural_size=(80, 50),
    ),
)


_EQUIPMENT_SENTINELS: tuple[EquipmentSpec, ...] = (
    # The agent writes this key when no class fits. Always degrades to
    # CustomEquipment with the agent's structural description on typeName.
    EquipmentSpec(
        key="unclassified_equipment",
        pydexpi_class=None,
        prompt_gloss="unknown / non-standard symbol — describe in source_quote",
        svg_fill="#e5e7eb",
        svg_glyph="",                            # hatched rectangle fallback
    ),
)


EQUIPMENT_REGISTRY: tuple[EquipmentSpec, ...] = _EQUIPMENT_REAL + _EQUIPMENT_SENTINELS


# The "valve" equipment_class acts as a router into VALVE_REGISTRY. It's kept
# visible to the agent as an equipment_class for clarity in legend rendering;
# the builder sees valve_type and routes to ValveSpec instead.
EQUIPMENT_CLASS_ROUTER_VALVE_KEY = "valve"


# ---------------------------------------------------------------------------
# Valve registry
# ---------------------------------------------------------------------------


_VALVE_REAL: tuple[ValveSpec, ...] = (
    # -- v0 baseline --
    ValveSpec(
        key="gate",
        pydexpi_class=_resolve(pp, "GateValve"),
        prompt_gloss="gate valve — on/off; full-bore linear gate",
        svg_fill="#fbbf24",
        drawio_shape="mxgraph.pid2valves.valve;valveType=gate",
    ),
    ValveSpec(
        key="globe",
        pydexpi_class=_resolve(pp, "GlobeValve"),
        prompt_gloss="globe valve — throttling; rounded body",
        svg_fill="#f59e0b",
        drawio_shape="mxgraph.pid2valves.valve;valveType=globe",
    ),
    ValveSpec(
        key="check",
        pydexpi_class=_resolve(pp, "CheckValve"),
        prompt_gloss="check valve — flow in one direction only",
        svg_fill="#fb923c",
        drawio_shape="mxgraph.pid2valves.valve;valveType=check",
    ),
    ValveSpec(
        key="ball",
        pydexpi_class=_resolve(pp, "BallValve"),
        prompt_gloss="ball valve — quarter-turn; bore through a sphere",
        svg_fill="#f97316",
        drawio_shape="mxgraph.pid2valves.valve;valveType=ball",
    ),
    ValveSpec(
        key="butterfly",
        pydexpi_class=_resolve(pp, "ButterflyValve"),
        prompt_gloss="butterfly valve — quarter-turn disc",
        svg_fill="#eab308",
        drawio_shape="mxgraph.pid2valves.valve;valveType=butterfly",
    ),
    ValveSpec(
        # DEXPI 2.0 has no dedicated ControlValve class; OperatedValve + control-intent attr.
        key="control",
        pydexpi_class=_resolve(pp, "OperatedValve"),
        control_intent=True,
        prompt_gloss="control valve — actuated, modulating process variable",
        svg_fill="#f472b6",
        # No dedicated "control valve" stencil in drawio's Process Engineering
        # library — represent as a globe body with a pneumatic-diaphragm
        # actuator by default.
        drawio_shape="mxgraph.pid2valves.valve;valveType=globe",
        drawio_default_actuator="diaph",
    ),

    # -- v0.2 additions (P0): safety-critical valves --
    ValveSpec(
        key="safety_relief",
        pydexpi_class=_resolve(pp, "SafetyValveOrFitting"),
        prompt_gloss="safety / relief / PSV — spring-loaded over-pressure protection",
        svg_fill="#ef4444",                      # red — safety-critical
        # No ISA "PSV" stencil — closest match is an angle valve with a
        # spring actuator (matches the visual idiom of a relief valve).
        drawio_shape="mxgraph.pid2valves.valve;valveType=angle",
        drawio_default_actuator="spring",
    ),
    ValveSpec(
        # DEXPI 2.0 has no ThreeWayValve; CustomOperatedValve + typeName fallback.
        key="three_way",
        pydexpi_class=_resolve(pp, "ThreeWayValve"),
        prompt_gloss="three-way valve — diverting / mixing on a branch",
        svg_fill="#fda4af",
        drawio_shape="mxgraph.pid2valves.valve;valveType=threeWay",
    ),

    # -- v0.2 additions (P1): specialty valves --
    ValveSpec(
        key="needle",
        pydexpi_class=_resolve(pp, "NeedleValve"),
        prompt_gloss="needle valve — fine throttling, small-bore instrument service",
        svg_fill="#fdba74",
        drawio_shape="mxgraph.pid2valves.valve;valveType=needle",
    ),
    ValveSpec(
        key="plug",
        pydexpi_class=_resolve(pp, "PlugValve"),
        prompt_gloss="plug valve — quarter-turn tapered plug, gas service",
        svg_fill="#fde047",
        drawio_shape="mxgraph.pid2valves.valve;valveType=plug",
    ),
    ValveSpec(
        key="strainer",
        pydexpi_class=_resolve(pp, "Strainer"),
        prompt_gloss="in-line strainer (Y-type, T-type) — coarse particle catch",
        svg_fill="#a3e635",
        # Strainer is a fitting in drawio, not a valve type — emit as a
        # piping-library shape rather than via the parameterised valve.
        drawio_shape="mxgraph.pid.piping.basket_strainer",
    ),

    # -- v0.2 additions (P2) --
    ValveSpec(
        key="rupture_disc",
        pydexpi_class=_resolve(pp, "RuptureDisc"),
        prompt_gloss="rupture disc / bursting disc — one-shot over-pressure protection",
        svg_fill="#f87171",
        drawio_shape="mxgraph.pid.fittings.rupture_disc",
    ),
)


_VALVE_SENTINELS: tuple[ValveSpec, ...] = (
    ValveSpec(
        key="other",
        pydexpi_class=None,                      # routes to CustomOperatedValve
        prompt_gloss="valve not matching the above categories",
        svg_fill="#fcd34d",
        # Fall back to a plain gate body so the cell still renders.
        drawio_shape="mxgraph.pid2valves.valve;valveType=gate",
    ),
)


VALVE_REGISTRY: tuple[ValveSpec, ...] = _VALVE_REAL + _VALVE_SENTINELS


# ---------------------------------------------------------------------------
# Instrument function registry
# ---------------------------------------------------------------------------


_INSTRUMENT_REAL: tuple[InstrumentSpec, ...] = (
    InstrumentSpec(key="indicator", prompt_gloss="local or panel indicator (I, FI, PI, TI, LI)",
                   drawio_mounting="field"),
    InstrumentSpec(key="transmitter", prompt_gloss="transmitter (FT, PT, TT, LT) — sends signal to DCS",
                   drawio_mounting="field"),
    # ISA-5.1 controllers/recorders/alarms are typically panel-mounted —
    # drawio's "room" mounting draws the horizontal divider line.
    InstrumentSpec(key="controller", prompt_gloss="controller (FC, PC, TC, LC, FIC, …)",
                   drawio_mounting="room"),
    InstrumentSpec(key="recorder", prompt_gloss="recorder (FR, PR, TR, LR)",
                   drawio_mounting="room"),
    InstrumentSpec(key="element", prompt_gloss="primary element (FE, TE, LE, AE)",
                   drawio_mounting="field"),
    InstrumentSpec(key="switch", prompt_gloss="switch (FS, PS, TS, LS, PSH, LSL)",
                   drawio_mounting="field"),
    InstrumentSpec(key="alarm", prompt_gloss="alarm (FA, PA, TA, LA, PAH, LAL)",
                   drawio_mounting="room"),
    InstrumentSpec(key="valve_actuator", prompt_gloss="valve actuator / positioner loop",
                   drawio_mounting="field"),
)


_INSTRUMENT_SENTINELS: tuple[InstrumentSpec, ...] = (
    InstrumentSpec(
        key="unclassified_instrument",
        prompt_gloss="instrument with unrecognised function letters",
    ),
)


INSTRUMENT_REGISTRY: tuple[InstrumentSpec, ...] = _INSTRUMENT_REAL + _INSTRUMENT_SENTINELS


# ---------------------------------------------------------------------------
# Instrument class registry — outer-loop pydexpi class selection
# ---------------------------------------------------------------------------
#
# ``instrument_function`` (FIC / FT / PSH) classifies the role at the tag
# level. ``instrument_class`` is a separate, coarser hint the agent MAY emit
# to upgrade the outer pydexpi wrapper: a closed-loop control function gets
# ``inst.ProcessControlFunction`` instead of the generic
# ``inst.ProcessInstrumentationFunction``. Downstream consumers can dispatch
# on ``isinstance`` rather than parsing string attributes.
#
# When absent or unrecognised, the builder keeps the PIF default — so this
# is strictly opt-in and preserves v0 behaviour.


@dataclass(frozen=True)
class InstrumentClassSpec:
    """One outer-loop wrapper class the agent can opt into via ``instrument_class``."""

    key: str
    pydexpi_class: type | None                   # None never happens for instrumentation: always in pydexpi
    prompt_gloss: str = ""


INSTRUMENT_CLASS_REGISTRY: tuple[InstrumentClassSpec, ...] = (
    InstrumentClassSpec(
        key="control_loop",
        pydexpi_class=_resolve(inst, "ProcessControlFunction"),
        prompt_gloss="closed-loop control (has controller + final control element)",
    ),
    InstrumentClassSpec(
        key="instrumentation_loop",
        pydexpi_class=_resolve(inst, "ProcessInstrumentationFunction"),
        prompt_gloss="indicator / transmitter / read-only loop (default if omitted)",
    ),
)


_INSTRUMENT_CLASS_INDEX: dict[str, InstrumentClassSpec] = {
    s.key: s for s in INSTRUMENT_CLASS_REGISTRY
}

INSTRUMENT_CLASS_KEYS: tuple[str, ...] = tuple(s.key for s in INSTRUMENT_CLASS_REGISTRY)


def instrument_class_spec_for(key: str) -> InstrumentClassSpec | None:
    if not key:
        return None
    return _INSTRUMENT_CLASS_INDEX.get(key.strip().lower())


def render_instrument_class_slash_list() -> str:
    return "/".join(s.key for s in INSTRUMENT_CLASS_REGISTRY)


# ---------------------------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------------------------


_EQUIPMENT_INDEX: dict[str, EquipmentSpec] = {s.key: s for s in EQUIPMENT_REGISTRY}
_VALVE_INDEX: dict[str, ValveSpec] = {s.key: s for s in VALVE_REGISTRY}
_INSTRUMENT_INDEX: dict[str, InstrumentSpec] = {s.key: s for s in INSTRUMENT_REGISTRY}


EQUIPMENT_CLASS_KEYS: tuple[str, ...] = tuple(s.key for s in EQUIPMENT_REGISTRY)
VALVE_TYPE_KEYS: tuple[str, ...] = tuple(s.key for s in VALVE_REGISTRY)
INSTRUMENT_FUNCTION_KEYS: tuple[str, ...] = tuple(s.key for s in INSTRUMENT_REGISTRY)


def equipment_spec_for(key: str) -> EquipmentSpec | None:
    """Return the spec for ``key`` (case-insensitive), or ``None`` if unknown."""
    if not key:
        return None
    return _EQUIPMENT_INDEX.get(key.strip().lower())


def valve_spec_for(key: str) -> ValveSpec | None:
    if not key:
        return None
    return _VALVE_INDEX.get(key.strip().lower())


def instrument_spec_for(key: str) -> InstrumentSpec | None:
    if not key:
        return None
    return _INSTRUMENT_INDEX.get(key.strip().lower())


def nearest_equipment_key(value: str, max_distance: int = 3) -> str | None:
    """Return the registry key closest to ``value`` by Levenshtein distance.

    Used by the builder to suggest a correction when the agent emits a typo
    (e.g. ``equipment_class="reactr"``). Returns ``None`` if no key is within
    ``max_distance``.
    """
    return _nearest_key(value, EQUIPMENT_CLASS_KEYS, max_distance)


def nearest_valve_key(value: str, max_distance: int = 3) -> str | None:
    return _nearest_key(value, VALVE_TYPE_KEYS, max_distance)


def _nearest_key(value: str, keys: tuple[str, ...], max_distance: int) -> str | None:
    v = (value or "").strip().lower()
    if not v:
        return None
    best: tuple[int, str] | None = None
    for k in keys:
        d = _levenshtein(v, k)
        if d == 0:
            return None                          # exact match — caller handles it elsewhere
        if d <= max_distance and (best is None or d < best[0]):
            best = (d, k)
    return best[1] if best else None


def _levenshtein(a: str, b: str) -> int:
    """Classic DP Levenshtein. Registry keys are short (≤ ~25 chars) so O(n·m) is fine."""
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i] + [0] * len(b)
        for j, cb in enumerate(b, 1):
            curr[j] = min(
                prev[j] + 1,
                curr[j - 1] + 1,
                prev[j - 1] + (0 if ca == cb else 1),
            )
        prev = curr
    return prev[-1]


# ---------------------------------------------------------------------------
# Prompt rendering
# ---------------------------------------------------------------------------


def render_equipment_taxonomy_enum() -> str:
    """Render the equipment_class enum as a comma-separated brace-list.

    Output shape: ``{tank, vessel, column, heat_exchanger, pump, compressor,
    unclassified_equipment}`` — matches the pre-refactor prompt verbatim.
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
    # Preserve registry order; dedup while preserving order.
    seen: set[str] = set()
    deduped: list[str] = []
    for h in hints:
        assert h is not None                     # filtered above; placates type-checker
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
    rendered prefix bytes stay stable up to the new entry — minor cache hit
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
    keys.append(EQUIPMENT_CLASS_ROUTER_VALVE_KEY)    # "valve"
    keys.append("unclassified_equipment")
    return ", ".join(keys)


def render_legend_valve_list() -> str:
    return ", ".join(s.key for s in VALVE_REGISTRY)


def render_legend_instrument_list() -> str:
    return ", ".join(s.key for s in INSTRUMENT_REGISTRY)
