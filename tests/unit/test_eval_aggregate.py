"""Tests for eval/aggregate.py — pandas pipelines."""

from __future__ import annotations

import math

import pandas as pd

from eval import aggregate as agg
from eval.aggregate import diff_runs


def _row(**overrides):
    base = {
        "run_id": "r0",
        "condition": "baseline",
        "fixture": "fA",
        "phase": 1,
        "metric_kind": "phase1_query",
        "family": "inventory",
        "query_id": "fA-q1",
        "scoring": "set_match",
        "score": 1.0,
        "detail": "",
        "trial": 0,
        "cost_usd": 0.10,
        "input_tokens": 100,
        "output_tokens": 20,
        "wall_clock_s": 12.0,
        "source_type": "vector",
        "domain": "synthetic",
        "entity_count_truth": "",
    }
    base.update(overrides)
    return base


def _phase2_row(**overrides):
    base = _row(
        phase=2, family="", query_id="", scoring="", trial=0,
        metric_kind="phase2_equipment_f1", score=0.85,
        cost_usd=0.0, wall_clock_s=0.0, entity_count_truth=20,
    )
    base.update(overrides)
    return base


def test_phase1_per_fixture_wide_includes_macro_row():
    rows = [
        _row(fixture="fA", family="inventory",     score=1.0, query_id="fA-q1", scoring="set_match"),
        _row(fixture="fA", family="counting",      score=1.0, query_id="fA-q2", scoring="numeric_tolerance"),
        _row(fixture="fA", family="connectivity",  score=0.0, query_id="fA-q3", scoring="graph_reachability"),
        _row(fixture="fA", family="identification", score=1.0, query_id="fA-q4", scoring="contains"),
        _row(fixture="fB", family="inventory",     score=0.5, query_id="fB-q1", scoring="set_match"),
        _row(fixture="fB", family="counting",      score=1.0, query_id="fB-q2", scoring="numeric_tolerance"),
        _row(fixture="fB", family="connectivity",  score=1.0, query_id="fB-q3", scoring="graph_reachability"),
        _row(fixture="fB", family="identification", score=1.0, query_id="fB-q4", scoring="contains"),
    ]
    df = pd.DataFrame(rows)
    wide = agg.phase1_per_fixture_wide(df)
    assert "macro" in wide["fixture"].values
    fa = wide[wide["fixture"] == "fA"].iloc[0]
    assert fa["overall"] == (1 + 1 + 0 + 1) / 4
    macro = wide[wide["fixture"] == "macro"].iloc[0]
    assert math.isclose(macro["overall"], (fa["overall"] + 0.875) / 2, rel_tol=1e-6)


def test_phase2_per_fixture_attaches_run_summary():
    rows = [
        _phase2_row(fixture="fA", metric_kind="phase2_equipment_f1", score=0.9),
        _phase2_row(fixture="fA", metric_kind="phase2_instrument_f1", score=0.8),
        _phase2_row(fixture="fA", metric_kind="phase2_tag_ocr_em", score=0.85),
        _phase2_row(fixture="fA", metric_kind="phase2_edge_f1", score=0.7),
        _phase2_row(fixture="fA", metric_kind="phase2_dexpi_validates", score=1.0),
        _phase2_row(fixture="fA", metric_kind="phase2_run", score=1.0,
                    cost_usd=2.5, wall_clock_s=180.0, entity_count_truth=20),
    ]
    df = pd.DataFrame(rows)
    out = agg.phase2_per_fixture(df)
    assert len(out) == 1
    row = out.iloc[0]
    assert row["phase2_equipment_f1"] == 0.9
    assert row["cost_usd"] == 2.5
    assert math.isclose(row["wall_clock_min"], 3.0, rel_tol=1e-6)
    assert row["entity_count_truth"] == 20


def test_diff_runs_flags_two_sigma_movement():
    prev_rows = [_row(score=0.50, trial=t, query_id=f"q-{t}") for t in range(5)]
    curr_rows = [_row(score=0.95, trial=t, query_id=f"q-{t}") for t in range(5)]
    flagged = diff_runs(pd.DataFrame(prev_rows), pd.DataFrame(curr_rows),
                        sigma_threshold=2.0)
    # Within each (q, fixture, ...) bucket there's only one trial each → sd=0,
    # which exercises the "sd == 0 and Δ != 0 → flag" branch.
    assert not flagged.empty
    assert (flagged["delta"] > 0).all()
