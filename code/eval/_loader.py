"""Load fixtures, manifests, and ground-truth files for the eval driver.

Internal helpers — public surface lives on ``run_paper_eval.py``.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from diagex.vision.models import Annotation, ReconciledGraph

# ---------------------------------------------------------------------------
# Fixture descriptors
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class FixtureSpec:
    stem: str
    pdf: str
    domain: str
    source_type: str
    annotation_level: str           # full | partial
    role: str
    page_size_pts: tuple[int, int]
    draughting_tool: str
    notable_flags: tuple[str, ...]


@dataclass(frozen=True)
class Manifest:
    dataset_version: str
    pdf_root: Path
    fixtures: tuple[FixtureSpec, ...]


def load_manifest(path: Path) -> Manifest:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    defaults = raw.get("defaults") or {}
    pdf_root = Path(defaults.get("pdf_root", "tests/p-ids-public"))

    fixtures: list[FixtureSpec] = []
    for f in raw.get("fixtures") or []:
        size = f.get("page_size_pts") or [0, 0]
        fixtures.append(
            FixtureSpec(
                stem=str(f["stem"]),
                pdf=str(f["pdf"]),
                domain=str(f.get("domain", "")),
                source_type=str(f.get("source_type", defaults.get("source_type", "vector"))),
                annotation_level=str(f.get("annotation_level", defaults.get("annotation_level", "partial"))),
                role=str(f.get("role", "")),
                page_size_pts=(int(size[0]), int(size[1])) if len(size) >= 2 else (0, 0),
                draughting_tool=str(f.get("draughting_tool", "")),
                notable_flags=tuple(str(x) for x in (f.get("notable_flags") or [])),
            )
        )
    return Manifest(
        dataset_version=str(raw.get("dataset_version", "unknown")),
        pdf_root=pdf_root,
        fixtures=tuple(fixtures),
    )


# ---------------------------------------------------------------------------
# Per-fixture truth loaders
# ---------------------------------------------------------------------------


@dataclass
class TruthQuery:
    id: str
    family: str
    question: str
    expected_answer: Any
    expected_kind: str
    scoring: str
    scoring_params: dict[str, Any] = field(default_factory=dict)


@dataclass
class FixtureTruth:
    spec: FixtureSpec
    fixture_dir: Path
    queries: list[TruthQuery]
    graph_truth: ReconciledGraph | None
    annotations_truth: list[Annotation]
    meta: dict[str, Any]


def load_fixture_truth(fixture_dir: Path, spec: FixtureSpec) -> FixtureTruth:
    queries_path = fixture_dir / "queries.truth.yaml"
    queries: list[TruthQuery] = []
    if queries_path.exists():
        doc = yaml.safe_load(queries_path.read_text(encoding="utf-8")) or {}
        for q in doc.get("queries") or []:
            queries.append(
                TruthQuery(
                    id=str(q.get("id", "")),
                    family=str(q.get("family", "")),
                    question=str(q.get("question", "")),
                    expected_answer=q.get("expected_answer"),
                    expected_kind=str(q.get("expected_kind", "")),
                    scoring=str(q.get("scoring", "")),
                    scoring_params=dict(q.get("scoring_params") or {}),
                )
            )

    graph_truth_path = fixture_dir / "graph.truth.json"
    graph_truth: ReconciledGraph | None = None
    if graph_truth_path.exists():
        graph_truth = ReconciledGraph.model_validate(
            json.loads(graph_truth_path.read_text(encoding="utf-8"))
        )

    ann_truth: list[Annotation] = []
    ann_path = fixture_dir / "annotations.truth.jsonl"
    if ann_path.exists():
        for line in ann_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            ann_truth.append(Annotation.model_validate(json.loads(line)))

    meta: dict[str, Any] = {}
    meta_path = fixture_dir / "meta.yaml"
    if meta_path.exists():
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}

    return FixtureTruth(
        spec=spec,
        fixture_dir=fixture_dir,
        queries=queries,
        graph_truth=graph_truth,
        annotations_truth=ann_truth,
        meta=meta,
    )


def load_predicted_graph(graph_path: Path) -> ReconciledGraph:
    """Load a ReconciledGraph from any path emitted by the pipeline
    (graph.json, graph.bootstrap.json, graph.truth.json)."""
    return ReconciledGraph.model_validate(
        json.loads(graph_path.read_text(encoding="utf-8"))
    )


# ---------------------------------------------------------------------------
# Cassette mode — pre-canned per-(condition, fixture) artefacts
# ---------------------------------------------------------------------------


@dataclass
class Phase1Cassette:
    """Canned per-query Phase 1 result. Mirrors a slice of `result.json`
    plus a per-query cost slice. The cassette file is a JSON list of dicts
    keyed by `query_id`."""
    answers_by_query: dict[str, dict[str, Any]]


@dataclass
class Phase2Cassette:
    """Canned Phase 2 outputs for a fixture: a graph + cost + run stats."""
    graph: ReconciledGraph
    cost_usd: float
    wall_clock_s: float
    dexpi_validates: bool
    input_tokens: int = 0
    output_tokens: int = 0


def load_phase1_cassette(path: Path) -> Phase1Cassette:
    raw = json.loads(path.read_text(encoding="utf-8"))
    answers = {str(item["query_id"]): item for item in raw.get("answers", [])}
    return Phase1Cassette(answers_by_query=answers)


def load_phase2_cassette(cassette_dir: Path) -> Phase2Cassette:
    graph = load_predicted_graph(cassette_dir / "graph.json")
    summary = json.loads((cassette_dir / "summary.json").read_text(encoding="utf-8"))
    return Phase2Cassette(
        graph=graph,
        cost_usd=float(summary.get("cost_usd", 0.0)),
        wall_clock_s=float(summary.get("wall_clock_s", 0.0)),
        dexpi_validates=bool(summary.get("dexpi_validates", False)),
        input_tokens=int(summary.get("input_tokens", 0)),
        output_tokens=int(summary.get("output_tokens", 0)),
    )
