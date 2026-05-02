"""End-to-end round-trip test for eval/run_paper_eval.py in cassette mode.

Builds a tiny synthetic dataset (one fixture, two queries, a graph), drops
matching cassette files into a temp dir, then invokes the typer command.
Asserts:

* ``results.csv`` is written and matches the expected schema.
* ``table2.tex`` and ``table3.tex`` round-trip (re-parsing the CSV and
  re-rendering produces identical bytes).
* ``report.md`` is non-empty.
* Phase 1 set_match scores end up correct given the canned answer.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import pytest
import yaml

from diagex.vision.models import BBox, ReconciledGraph, ReconciledNode
from eval import aggregate as agg
from eval import latex_tables
from eval.conditions import resolve_conditions
from eval.run_paper_eval import HarnessConfig, _run


def _node(nid, kind, label, x=0, y=0, w=10, h=10) -> ReconciledNode:
    return ReconciledNode(
        id=nid, kind=kind, label=label,
        bbox_global=BBox(x=x, y=y, w=w, h=h), page_index=0,
        confidence="high",
    )


def _build_synthetic_dataset(tmp_path: Path) -> tuple[Path, Path]:
    """Return (dataset_root, cassettes_root)."""
    dataset_root = tmp_path / "datasets"
    fixture_dir = dataset_root / "synth1"
    fixture_dir.mkdir(parents=True)

    manifest = {
        "dataset_version": "test.v0.1",
        "schema_version": 1,
        "defaults": {
            "pdf_root": "tests/p-ids-public",
            "queries_per_diagram": 2,
            "annotation_level": "full",
            "symbol_standard": "iso-10628",
            "source_type": "vector",
        },
        "fixtures": [
            {
                "stem": "synth1",
                "pdf": "synth1.pdf",
                "domain": "synthetic",
                "source_type": "vector",
                "page_size_pts": [100, 100],
                "draughting_tool": "test",
                "annotation_level": "full",
                "role": "synthetic round-trip fixture",
                "notable_flags": [],
            },
        ],
    }
    (dataset_root / "manifest.yaml").write_text(yaml.safe_dump(manifest))

    queries_doc = {
        "schema_version": 1,
        "dataset_version": "test.v0.1",
        "fixture": "synth1",
        "authoring": {"rater_1": "test", "overall_status": "rater_1_locked"},
        "queries": [
            {
                "id": "synth1-q1",
                "family": "inventory",
                "question": "List every pump in this drawing with its tag number.",
                "expected_answer": ["P-1", "P-2"],
                "expected_kind": "list",
                "scoring": "set_match",
                "scoring_params": {"case_sensitive": False},
                "status": "rater_1_locked",
            },
            {
                "id": "synth1-q2",
                "family": "counting",
                "question": "How many pumps are shown?",
                "expected_answer": 2,
                "expected_kind": "integer",
                "scoring": "numeric_tolerance",
                "scoring_params": {"tolerance_frac": 0.05},
                "status": "rater_1_locked",
            },
        ],
    }
    (fixture_dir / "queries.truth.yaml").write_text(yaml.safe_dump(queries_doc))

    truth_graph = ReconciledGraph(
        source_path="synth1.pdf",
        nodes=[
            _node("t1", "equipment", "P-1", 0, 0, 20, 20),
            _node("t2", "equipment", "P-2", 50, 50, 20, 20),
        ],
        edges=[],
    )
    (fixture_dir / "graph.truth.json").write_text(truth_graph.model_dump_json(indent=2))

    meta = {
        "stem": "synth1",
        "dataset_version": "test.v0.1",
        "source_type": "vector",
        "symbol_standard": "iso-10628",
        "domain": "synthetic",
    }
    (fixture_dir / "meta.yaml").write_text(yaml.safe_dump(meta))

    # Cassette: phase1 answers + phase2 graph + summary
    cassettes_root = tmp_path / "cassettes"
    cas_dir = cassettes_root / "baseline" / "synth1"
    cas_dir.mkdir(parents=True)

    phase1 = {
        "answers": [
            {
                "query_id": "synth1-q1",
                "answer": "- P-1\n- P-2\n",
                "cost_usd": 0.10,
                "wall_clock_s": 12.3,
                "input_tokens": 100,
                "output_tokens": 20,
            },
            {
                "query_id": "synth1-q2",
                "answer": "There are 2 pumps.",
                "cost_usd": 0.08,
                "wall_clock_s": 9.5,
                "input_tokens": 90,
                "output_tokens": 10,
            },
        ],
    }
    (cas_dir / "phase1.json").write_text(json.dumps(phase1, indent=2))

    pred_graph = ReconciledGraph(
        source_path="synth1.pdf",
        nodes=[
            _node("p1", "equipment", "P-1", 0, 0, 20, 20),
            _node("p2", "equipment", "P-2", 50, 50, 20, 20),
        ],
        edges=[],
    )
    (cas_dir / "graph.json").write_text(pred_graph.model_dump_json(indent=2))
    summary = {
        "cost_usd": 1.42,
        "wall_clock_s": 220.0,
        "dexpi_validates": True,
        "input_tokens": 12000,
        "output_tokens": 800,
    }
    (cas_dir / "summary.json").write_text(json.dumps(summary, indent=2))

    return dataset_root, cassettes_root


def _harness(tmp_path: Path, dataset_root: Path, cassettes_root: Path) -> HarnessConfig:
    return HarnessConfig(
        out_dir=tmp_path / "out",
        cassettes_dir=cassettes_root,
        use_cassettes=True,
        parallel=1,
        n_replicates=1,
        fixtures_filter=None,
        dataset_root=dataset_root,
        pdf_root=tmp_path / "no-such-pdfs",  # unused in cassette mode
        emit_tables=True,
        emit_figures=False,
        emit_artifacts=True,
    )


def test_cassette_round_trip_emits_csv_and_tables(tmp_path):
    dataset_root, cassettes_root = _build_synthetic_dataset(tmp_path)
    harness = _harness(tmp_path, dataset_root, cassettes_root)
    conditions = resolve_conditions(["baseline"])

    csv_path = _run(
        harness=harness, phase="both", conditions=conditions,
        invocation="pytest cassette",
    )
    assert csv_path.exists()
    df = pd.read_csv(csv_path)

    # Schema present, no rows missing required columns
    for col in agg.RESULTS_COLUMNS:
        assert col in df.columns, f"missing column: {col}"

    # Phase 1: 2 queries × 1 trial = 2 rows
    p1 = df[df["phase"] == 1]
    assert len(p1) == 2
    assert (p1["score"] == 1.0).all(), p1[["query_id", "score", "detail"]].to_string()

    # Phase 2: ≥ 4 metric rows (eq, inst, tag_em, dexpi_validates) + 1 phase2_run row
    p2 = df[df["phase"] == 2]
    metric_kinds = set(p2["metric_kind"])
    assert "phase2_equipment_f1" in metric_kinds
    assert "phase2_tag_ocr_em" in metric_kinds
    assert "phase2_dexpi_validates" in metric_kinds
    assert "phase2_run" in metric_kinds
    # Equipment F1 must be 1.0 since pred mirrors truth
    eq = p2[p2["metric_kind"] == "phase2_equipment_f1"]
    assert eq["score"].iloc[0] == 1.0

    # Tables exist and are non-empty
    table2 = (harness.out_dir / "tables" / "table2.tex").read_text()
    table3 = (harness.out_dir / "tables" / "table3.tex").read_text()
    assert "synth1" in table2
    assert "synth1" in table3
    assert "\\begin{table}" in table2
    assert "\\begin{table*}" in table3

    # Report
    report = (harness.out_dir / "report.md").read_text()
    assert "synth1" in report

    # Round-trip: re-render tables from the same CSV bytes — must be byte-identical.
    df2 = pd.read_csv(csv_path)
    wide = agg.phase1_per_fixture_wide(df2)
    per_fixture = agg.phase2_per_fixture(df2)
    table2_again = latex_tables.render_table2(wide)
    table3_again = latex_tables.render_table3(per_fixture)
    assert table2_again == table2
    assert table3_again == table3


def test_use_cassettes_raises_when_phase1_cassette_missing(tmp_path):
    """Strict cassette mode: missing phase1.json → CassetteMissingError, not
    silent fall-through to live API. Regression for the footgun where
    --use-cassettes was paying real money on missing cells.
    """
    from diagex.vision.models import BBox, ReconciledGraph, ReconciledNode
    from eval._loader import FixtureSpec, FixtureTruth, TruthQuery
    from eval.run_paper_eval import (
        CassetteMissingError, HarnessConfig, _resolve_cassette_phase1,
    )

    cassettes_root = tmp_path / "cassettes"
    cassettes_root.mkdir()
    harness = HarnessConfig(
        out_dir=tmp_path / "out",
        cassettes_dir=cassettes_root,
        use_cassettes=True,
        parallel=1,
        n_replicates=1,
        fixtures_filter=None,
        dataset_root=tmp_path / "datasets",
        pdf_root=tmp_path / "pdfs",
        emit_tables=False,
        emit_figures=False,
        emit_artifacts=False,
    )
    with pytest.raises(CassetteMissingError, match="phase1 cassette missing"):
        _resolve_cassette_phase1(harness, condition="baseline", fixture="missing")


def test_use_cassettes_raises_when_phase2_cassette_missing(tmp_path):
    from eval.run_paper_eval import (
        CassetteMissingError, HarnessConfig, _resolve_cassette_phase2,
    )

    cassettes_root = tmp_path / "cassettes"
    cassettes_root.mkdir()
    harness = HarnessConfig(
        out_dir=tmp_path / "out",
        cassettes_dir=cassettes_root,
        use_cassettes=True,
        parallel=1,
        n_replicates=1,
        fixtures_filter=None,
        dataset_root=tmp_path / "datasets",
        pdf_root=tmp_path / "pdfs",
        emit_tables=False,
        emit_figures=False,
        emit_artifacts=False,
    )
    with pytest.raises(CassetteMissingError, match="phase2 cassette missing"):
        _resolve_cassette_phase2(harness, condition="baseline", fixture="missing")


def test_allow_live_fallback_returns_none_for_missing_cassettes(tmp_path):
    """Opt-in live fallback: with allow_live_fallback=True, missing cassettes
    return None instead of raising — the runtime then routes to live."""
    from eval.run_paper_eval import (
        HarnessConfig, _resolve_cassette_phase1, _resolve_cassette_phase2,
    )

    cassettes_root = tmp_path / "cassettes"
    cassettes_root.mkdir()
    harness = HarnessConfig(
        out_dir=tmp_path / "out",
        cassettes_dir=cassettes_root,
        use_cassettes=True,
        parallel=1,
        n_replicates=1,
        fixtures_filter=None,
        dataset_root=tmp_path / "datasets",
        pdf_root=tmp_path / "pdfs",
        emit_tables=False,
        emit_figures=False,
        emit_artifacts=False,
        allow_live_fallback=True,
    )
    assert _resolve_cassette_phase1(harness, condition="b", fixture="x") is None
    assert _resolve_cassette_phase2(harness, condition="b", fixture="x") is None


def test_run_emits_invocation_log(tmp_path):
    dataset_root, cassettes_root = _build_synthetic_dataset(tmp_path)
    harness = _harness(tmp_path, dataset_root, cassettes_root)
    _run(
        harness=harness, phase="1",
        conditions=resolve_conditions(["baseline"]),
        invocation="pytest invocation",
    )
    inv_path = harness.out_dir / "invocation.txt"
    assert inv_path.exists()
    payload = json.loads(inv_path.read_text())
    assert payload["argv"] == ["pytest", "invocation"]
    assert "run_id" in payload
