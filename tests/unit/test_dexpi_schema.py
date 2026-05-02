"""Well-formedness tests for the DEXPI registry (:mod:`diagex.dexpi_schema`)."""

from __future__ import annotations

import pytest

from diagex import dexpi_schema as ds

# ---------------------------------------------------------------------------
# Registry well-formedness
# ---------------------------------------------------------------------------


def test_equipment_registry_has_no_duplicate_keys():
    keys = [s.key for s in ds.EQUIPMENT_REGISTRY]
    assert len(keys) == len(set(keys)), f"duplicate keys in EQUIPMENT_REGISTRY: {keys}"


def test_valve_registry_has_no_duplicate_keys():
    keys = [s.key for s in ds.VALVE_REGISTRY]
    assert len(keys) == len(set(keys)), f"duplicate keys in VALVE_REGISTRY: {keys}"


def test_instrument_registry_has_no_duplicate_keys():
    keys = [s.key for s in ds.INSTRUMENT_REGISTRY]
    assert len(keys) == len(set(keys)), f"duplicate keys in INSTRUMENT_REGISTRY: {keys}"


def test_equipment_registry_keys_are_lowercase_snake():
    for s in ds.EQUIPMENT_REGISTRY:
        assert s.key == s.key.lower(), f"key {s.key!r} must be lowercase"
        assert " " not in s.key, f"key {s.key!r} must use underscores"


def test_equipment_registry_has_unclassified_sentinel():
    spec = ds.equipment_spec_for("unclassified_equipment")
    assert spec is not None
    # The sentinel must have no pydexpi_class so the builder always routes to CustomEquipment.
    assert spec.pydexpi_class is None


def test_instrument_registry_has_unclassified_sentinel():
    assert ds.instrument_spec_for("unclassified_instrument") is not None


# ---------------------------------------------------------------------------
# V0 baseline: confirm pre-refactor keys are present (regression guard)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "key", ["tank", "vessel", "column", "heat_exchanger", "pump", "compressor", "unclassified_equipment"]
)
def test_v0_equipment_keys_present(key: str):
    assert ds.equipment_spec_for(key) is not None, f"v0 equipment key {key!r} missing"


@pytest.mark.parametrize(
    "key", ["gate", "globe", "check", "ball", "butterfly", "control", "other"]
)
def test_v0_valve_keys_present(key: str):
    assert ds.valve_spec_for(key) is not None, f"v0 valve key {key!r} missing"


@pytest.mark.parametrize(
    "key",
    [
        "indicator", "transmitter", "controller", "recorder",
        "element", "switch", "alarm", "valve_actuator",
        "unclassified_instrument",
    ],
)
def test_v0_instrument_keys_present(key: str):
    assert ds.instrument_spec_for(key) is not None, f"v0 instrument key {key!r} missing"


# ---------------------------------------------------------------------------
# Subtype resolution
# ---------------------------------------------------------------------------


def test_pump_subtype_hint_resolves_centrifugal():
    spec = ds.equipment_spec_for("pump")
    cls, is_base = spec.resolve({"pump_type": "centrifugal"})
    assert cls is not None
    assert cls.__name__ == "CentrifugalPump"
    assert is_base is False


def test_pump_no_hint_uses_base():
    spec = ds.equipment_spec_for("pump")
    cls, is_base = spec.resolve({})
    assert cls.__name__ == "Pump"
    assert is_base is True


def test_heat_exchanger_aliases():
    spec = ds.equipment_spec_for("heat_exchanger")
    for alias in ("shell_tube", "shell-tube", "tubular"):
        cls, _ = spec.resolve({"heat_exchanger_type": alias})
        assert cls.__name__ == "TubularHeatExchanger", f"alias {alias!r} did not resolve"
    cls, _ = spec.resolve({"heat_exchanger_type": "plate"})
    assert cls.__name__ == "PlateHeatExchanger"


def test_unclassified_equipment_resolves_to_none():
    spec = ds.equipment_spec_for("unclassified_equipment")
    cls, _ = spec.resolve({})
    assert cls is None, "unclassified_equipment must signal fallback"


# ---------------------------------------------------------------------------
# Typo suggestions
# ---------------------------------------------------------------------------


def test_nearest_key_suggests_close_match():
    assert ds.nearest_equipment_key("tnk") == "tank"
    assert ds.nearest_equipment_key("vessl") == "vessel"
    assert ds.nearest_valve_key("bal") == "ball"


def test_nearest_key_returns_none_for_exact_match():
    # Exact-match callers should not surface a "did you mean" hint.
    assert ds.nearest_equipment_key("tank") is None


def test_nearest_key_returns_none_for_distant_strings():
    assert ds.nearest_equipment_key("xyzzy") is None


# ---------------------------------------------------------------------------
# Prompt renderers — cache stability guarantees
# ---------------------------------------------------------------------------


def test_render_equipment_taxonomy_enum_deterministic():
    first = ds.render_equipment_taxonomy_enum()
    second = ds.render_equipment_taxonomy_enum()
    assert first == second


def test_render_equipment_taxonomy_enum_is_brace_delimited():
    rendered = ds.render_equipment_taxonomy_enum()
    assert rendered.startswith("{") and rendered.endswith("}")
    # All registry keys appear.
    for s in ds.EQUIPMENT_REGISTRY:
        assert s.key in rendered


def test_render_equipment_subtype_hints_dedups_and_preserves_order():
    rendered = ds.render_equipment_subtype_hints()
    parts = [p.strip() for p in rendered.split(",")]
    # No duplicates.
    assert len(parts) == len(set(parts))
    # Order follows registry iteration — v0 hints come first.
    assert parts[:3] == ["heat_exchanger_type", "pump_type", "compressor_type"]
    # All registry subtype_hint_attrs appear exactly once.
    expected = []
    seen: set[str] = set()
    for s in ds.EQUIPMENT_REGISTRY:
        if s.subtype_hint_attr and s.subtype_hint_attr not in seen:
            expected.append(s.subtype_hint_attr)
            seen.add(s.subtype_hint_attr)
    assert parts == expected


def test_render_equipment_subtype_values_lists_known_keys():
    """The per-attribute value enumerator drives the agent's prompt vocabulary
    so it can pick a specific subtype (e.g. floating_head) instead of inventing
    one. Output must list every key from the union of subtype_hints +
    drawio_subtype_shapes, deduped, in registry order."""
    rendered = ds.render_equipment_subtype_values()

    # heat_exchanger_type line includes the new visual variants.
    hx_line = next(line for line in rendered.splitlines() if "heat_exchanger_type" in line)
    for v in (
        "shell_and_tube", "floating_head", "u_tube", "plate",
        "plate_and_frame", "spiral", "hairpin", "finned_tubes", "air_cooler",
    ):
        assert v in hx_line, f"missing {v!r} from heat_exchanger_type values"

    # pump_type line lists the three subclasses we instantiate.
    pump_line = next(line for line in rendered.splitlines() if "pump_type" in line)
    for v in ("centrifugal", "reciprocating", "rotary"):
        assert v in pump_line

    # No attribute appears twice (dedup invariant — registry has only one
    # spec per subtype_hint_attr today, but the helper guards anyway).
    attr_names = [
        line.strip().split(" ")[0] for line in rendered.splitlines() if "∈" in line
    ]
    assert len(attr_names) == len(set(attr_names))


def test_phase2_prompt_contains_subtype_values_block():
    """Catches an integration regression where the new placeholder is added
    to the template but never substituted (would leave %%…%% verbatim in the
    cached prompt)."""
    from diagex.llm.prompts.phase2_pid import STARTER_PID_PROMPT
    assert "heat_exchanger_type ∈" in STARTER_PID_PROMPT
    assert "pump_type ∈" in STARTER_PID_PROMPT
    # No un-substituted placeholders left over.
    assert "%%EQUIPMENT_SUBTYPE_VALUES%%" not in STARTER_PID_PROMPT


def test_slash_renderers_use_forward_slashes():
    assert "/" in ds.render_equipment_slash_list()
    assert "/" in ds.render_valve_slash_list()
    assert "/" in ds.render_instrument_slash_list()
    # No braces in the slash form (they live in the brace-enum form).
    assert "{" not in ds.render_equipment_slash_list()
