from __future__ import annotations

import json
from pathlib import Path

import fitz
import pytest

from diagex.review.core import (
    ReviewConflictError,
    ReviewIncompleteError,
    ReviewStore,
    _confirm_provisional_edge,
)
from diagex.review.render import prepare_page_assets
from diagex.vision.models import BBox, ReconciledEdge, ReconciledGraph, ReconciledNode


def test_human_confirmation_promotes_provisional_edge() -> None:
    edge = {
        "attributes": {
            "provisional_review_only": True,
            "requires_human_review": True,
            "review_conflict_type": "page_graph_uncertain_candidate",
            "review_reason": "uncertain",
            "original_line_type": "process",
        }
    }

    _confirm_provisional_edge(edge)

    assert edge["attributes"]["human_review_confirmed"] is True
    assert "provisional_review_only" not in edge["attributes"]
    assert edge["attributes"]["original_line_type"] == "process"


def _write_source(path: Path, *, pages: int = 1) -> None:
    document = fitz.open()
    for index in range(pages):
        page = document.new_page(width=240, height=160)
        page.insert_text((24, 30), f"P&ID page {index + 1}")
        page.draw_rect(fitz.Rect(30, 50, 90, 100))
    document.save(path)
    document.close()


def _write_run(path: Path, *, dangling: bool = False) -> Path:
    path.mkdir()
    graph = ReconciledGraph(
        source_path="sample.pdf",
        nodes=[
            ReconciledNode(
                id="n-a",
                kind="equipment",
                label="T-101",
                bbox_global=BBox(x=100, y=120, w=120, h=80),
                page_index=0,
                attributes={"equipment_class": "tank"},
                confidence="high",
            ),
            ReconciledNode(
                id="n-b",
                kind="equipment",
                label="P-101",
                bbox_global=BBox(x=500, y=120, w=100, h=80),
                page_index=0,
                attributes={"equipment_class": "pump"},
                confidence="medium",
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e-a",
                from_node="n-a",
                to_node="missing" if dangling else "n-b",
                line_type="process",
                polyline_global=[(220, 160), (500, 160)],
                confidence="high",
                attributes={"line_id": "L-101"},
            )
        ],
        conflicts=[{"type": "ambiguous_opc", "node_id": "n-b"}],
        per_page_status={0: "partial"},
    )
    (path / "graph.json").write_text(graph.model_dump_json(indent=2), encoding="utf-8")
    (path / "result.json").write_text(
        json.dumps({"dexpi_issues": ["node 'n-b': unclassified equipment"]}),
        encoding="utf-8",
    )
    return path


def _write_native_evidence(run: Path) -> None:
    evidence = run / "evidence"
    evidence.mkdir()
    (evidence / "page-0001.json").write_text(
        json.dumps(
            {
                "page_index": 0,
                "role": "pid",
                "text_spans": [
                    {
                        "id": "txt-tank",
                        "text": "T-101",
                        "bbox": {"x": 100, "y": 100, "w": 50, "h": 20},
                        "block_index": 0,
                        "line_index": 0,
                        "word_index": 0,
                    },
                    {
                        "id": "txt-pt-prefix",
                        "text": "PT",
                        "bbox": {"x": 300, "y": 100, "w": 20, "h": 20},
                        "block_index": 1,
                        "line_index": 0,
                        "word_index": 0,
                    },
                    {
                        "id": "txt-pt-number",
                        "text": "102",
                        "bbox": {"x": 325, "y": 100, "w": 35, "h": 20},
                        "block_index": 1,
                        "line_index": 0,
                        "word_index": 1,
                    },
                    {
                        "id": "txt-line",
                        "text": "50-GA-00302-M15B-N",
                        "bbox": {"x": 100, "y": 300, "w": 150, "h": 20},
                        "block_index": 2,
                        "line_index": 0,
                        "word_index": 0,
                    },
                ],
            }
        ),
        encoding="utf-8",
    )


@pytest.fixture
def review(tmp_path: Path) -> ReviewStore:
    source = tmp_path / "source.pdf"
    _write_source(source)
    run = _write_run(tmp_path / "run")
    return ReviewStore.open(run, source_path=source, rater="Ada", out_dir=tmp_path / "review")


def _action(
    store: ReviewStore,
    target_type: str,
    target_id: str,
    operation: str,
    after: dict | None = None,
    reason: str = "",
) -> dict:
    return store.append_action(
        {
            "expected_revision": store.state["revision"],
            "target_type": target_type,
            "target_id": target_id,
            "operation": operation,
            "after": after or {},
            "reason": reason,
        }
    )


def test_session_renders_both_frames_and_prioritises_risk(review: ReviewStore):
    state = review.public_state()
    assert (review.out_dir / "pages" / "p0000.source.png").is_file()
    assert (review.out_dir / "pages" / "p0000.inference.png").is_file()
    assert state["queue"][0]["tier"] == 0
    assert "partial page" in state["queue"][0]["reasons"]
    assert state["session"]["build_issues"][0]["target_id"] == "n-b"
    assert "solenoid" in state["taxonomy"]["actuation_types"]


def test_public_conflicts_include_compact_review_candidates(tmp_path: Path) -> None:
    source = tmp_path / "source.pdf"
    _write_source(source)
    run = _write_run(tmp_path / "run")
    graph_path = run / "graph.json"
    graph = json.loads(graph_path.read_text(encoding="utf-8"))
    graph["conflicts"] = [
        {
            "type": "ambiguous_opc_evidence",
            "node_id": "n-b",
            "edge_id": "e-a",
            "labels": ["P-101", "P-101A"],
            "kinds": {"equipment": 2, "opc": 1},
            "candidate_pairs": [
                {
                    "node_ids": ["n-a", "n-b"],
                    "score": 0.86,
                    "left_service": "feed",
                    "right_service": "feed",
                }
            ],
        }
    ]
    graph_path.write_text(json.dumps(graph), encoding="utf-8")
    store = ReviewStore.open(
        run,
        source_path=source,
        rater="Ada",
        out_dir=tmp_path / "review",
    )

    conflict = next(iter(store.public_state()["reviews"]["conflicts"].values()))
    candidates = conflict["candidates"]
    assert [node["id"] for node in candidates["nodes"]] == ["n-b", "n-a"]
    assert [edge["id"] for edge in candidates["edges"]] == ["e-a"]
    assert candidates["labels"] == ["P-101", "P-101A"]
    assert candidates["kinds"] == ["equipment", "opc"]
    assert candidates["pairs"][0]["score"] == 0.86
    assert (
        "candidates"
        not in store.state["conflict_reviews"][next(iter(store.state["conflict_reviews"]))]
    )


def test_resolved_model_conflict_does_not_require_human_disposition(
    tmp_path: Path,
) -> None:
    source = tmp_path / "source.pdf"
    _write_source(source)
    run = _write_run(tmp_path / "run")
    graph_path = run / "graph.json"
    graph = json.loads(graph_path.read_text())
    graph["conflicts"][0]["status"] = "resolved"
    graph["conflicts"][0]["reason"] = "deterministically excluded"
    graph_path.write_text(json.dumps(graph), encoding="utf-8")

    store = ReviewStore.open(
        run,
        source_path=source,
        rater="Ada",
        out_dir=tmp_path / "review",
    )

    conflict = next(iter(store.state["conflict_reviews"].values()))
    assert conflict["status"] == "resolved"
    assert store.completion()["unresolved_conflicts"] == []


def test_actions_are_persistent_and_stale_revisions_are_rejected(review: ReviewStore):
    _action(review, "page", "0", "approve", {"role": "pid"})
    _action(review, "node", "n-a", "approve")
    _action(review, "node", "n-b", "modify", {"label": "P-101A"})

    with pytest.raises(ReviewConflictError, match="stale review revision"):
        review.append_action(
            {
                "expected_revision": 0,
                "target_type": "edge",
                "target_id": "e-a",
                "operation": "approve",
            }
        )

    resumed = ReviewStore.open(
        review.graph_path,
        source_path=review.source_path,
        rater="Ada",
        out_dir=review.out_dir,
    )
    assert resumed.state["revision"] == 3
    assert next(n for n in resumed.state["graph"]["nodes"] if n["id"] == "n-b")["label"] == "P-101A"
    assert len((review.out_dir / "events.jsonl").read_text().splitlines()) == 3


def test_native_text_inventory_links_matches_and_audits_missing_tags(tmp_path: Path):
    source = tmp_path / "source.pdf"
    _write_source(source)
    run = _write_run(tmp_path / "run")
    _write_native_evidence(run)
    store = ReviewStore.open(
        run, source_path=source, rater="Ada", out_dir=tmp_path / "review"
    )

    state = store.public_state()
    candidates = state["inventory"]["evidence"]
    tank = next(item for item in candidates if item["normalised_text"] == "T101")
    missing = next(item for item in candidates if item["normalised_text"] == "PT102")
    line = next(item for item in candidates if item["candidate_kind"] == "line_number")
    assert tank["review"]["status"] == "linked"
    assert tank["review"]["linked_node_id"] == "n-a"
    assert missing["review"]["status"] == "unreviewed"
    assert line["blocking"] is False
    assert store.completion()["unreviewed_evidence"] == [missing["id"]]

    _action(
        store,
        "evidence",
        missing["id"],
        "link",
        {"node_id": "n-b"},
        "same printed tag",
    )
    assert store.completion()["unreviewed_evidence"] == []
    assert store.state["evidence_reviews"][missing["id"]]["linked_node_id"] == "n-b"

    _action(
        store,
        "evidence",
        line["id"],
        "dismiss",
        {"disposition": "line_number"},
    )
    resumed = ReviewStore.open(
        run, source_path=source, rater="Ada", out_dir=tmp_path / "review"
    )
    assert resumed.state["evidence_reviews"][line["id"]]["status"] == "dismissed"


def test_reject_and_undo_append_a_compensating_event(review: ReviewStore):
    _action(review, "node", "n-a", "reject", reason="false positive")
    assert review.state["node_reviews"]["n-a"] == "rejected"
    review.append_action({"expected_revision": 1, "operation": "undo"})
    assert review.state["node_reviews"]["n-a"] == "unreviewed"
    events = [json.loads(line) for line in review.events_path.read_text().splitlines()]
    assert events[-1]["operation"] == "undo"
    assert events[-1]["undo_of"] == 1


def test_add_node_and_edge_then_edit_geometry(review: ReviewStore):
    added_node = _action(
        review,
        "node",
        "",
        "add",
        {
            "kind": "instrument",
            "label": "PI-101",
            "bbox_global": {"x": 300, "y": 250, "w": 60, "h": 60},
            "page_index": 0,
            "attributes": {"instrument_function": "indicator"},
            "confidence": "medium",
        },
    )["event"]["target_id"]
    added_edge = _action(
        review,
        "edge",
        "",
        "add",
        {
            "from_node": "n-a",
            "to_node": added_node,
            "line_type": "signal_electric",
            "polyline_global": [[160, 160], [330, 280]],
            "confidence": "medium",
        },
    )["event"]["target_id"]
    _action(review, "edge", added_edge, "modify", {"polyline_global": [[160, 160], [330, 260]]})
    graph = review.state["graph"]
    assert next(n for n in graph["nodes"] if n["id"] == added_node)["label"] == "PI-101"
    assert next(e for e in graph["edges"] if e["id"] == added_edge)["polyline_global"][-1] == [
        330,
        260,
    ]
    assert review.state["node_reviews"][added_node] == "modified"


def test_completion_gate_and_export(review: ReviewStore):
    with pytest.raises(ReviewIncompleteError):
        review.finish()
    _action(review, "page", "0", "approve", {"role": "pid"})
    _action(review, "node", "n-a", "approve")
    _action(review, "node", "n-b", "approve")
    _action(review, "edge", "e-a", "approve")
    conflict_id = next(iter(review.state["conflict_reviews"]))
    _action(review, "conflict", conflict_id, "waive", reason="source is ambiguous")

    assert review.completion()["complete"] is True
    report = review.finish()
    assert report["finished"] is True
    assert (review.out_dir / "graph.reviewed.json").is_file()
    assert (review.out_dir / "pid.reviewed.dexpi.json").is_file()
    assert (review.out_dir / "pid.reviewed.dexpi.xml").is_file()
    assert json.loads((review.out_dir / "review.report.json").read_text())["finished"] is True


def test_dangling_active_edge_blocks_completion(tmp_path: Path):
    source = tmp_path / "source.pdf"
    _write_source(source)
    run = _write_run(tmp_path / "run", dangling=True)
    store = ReviewStore.open(run, source_path=source, rater="Ada")
    _action(store, "page", "0", "approve", {"role": "pid"})
    _action(store, "node", "n-a", "approve")
    _action(store, "node", "n-b", "approve")
    _action(store, "edge", "e-a", "approve")
    conflict_id = next(iter(store.state["conflict_reviews"]))
    _action(store, "conflict", conflict_id, "resolve")
    assert store.completion()["dangling_edges"] == ["e-a"]


def test_malformed_audit_line_is_reported_without_losing_valid_events(review: ReviewStore):
    _action(review, "node", "n-a", "approve")
    with review.events_path.open("a", encoding="utf-8") as handle:
        handle.write("{broken")
    resumed = ReviewStore.open(
        review.graph_path,
        source_path=review.source_path,
        rater="Ada",
        out_dir=review.out_dir,
    )
    assert resumed.state["revision"] == 1
    assert any("malformed" in warning for warning in resumed.state["warnings"])
    _action(resumed, "node", "n-b", "approve")
    lines = resumed.events_path.read_text().splitlines()
    assert json.loads(lines[-1])["revision"] == 2


def test_source_or_graph_hash_mismatch_refuses_resume(review: ReviewStore):
    review.source_path.write_bytes(review.source_path.read_bytes() + b"changed")
    with pytest.raises(ReviewConflictError, match="source diagram changed"):
        ReviewStore.open(
            review.graph_path,
            source_path=review.source_path,
            rater="Ada",
            out_dir=review.out_dir,
        )


def test_page_assets_support_multipage_and_persisted_coordinate_frames(tmp_path: Path):
    source = tmp_path / "source.pdf"
    _write_source(source, pages=2)
    inferred = prepare_page_assets(source, tmp_path / "inferred")
    assert [page["page_index"] for page in inferred] == [0, 1]

    expected = {
        "scan": {"deskew": False, "contrast": False, "despeckle": False},
        "pages": [
            {
                "page_index": 0,
                "width": 240,
                "height": 160,
                "dpi": 72.0,
                "effective_dpi": 72.0,
                "is_scanned": False,
                "rotation_deg": 0.0,
                "source_ref": "source#page=1",
            },
            {
                "page_index": 1,
                "width": 240,
                "height": 160,
                "dpi": 72.0,
                "effective_dpi": 72.0,
                "is_scanned": False,
                "rotation_deg": 0.0,
                "source_ref": "source#page=2",
            },
        ],
    }
    restored = prepare_page_assets(source, tmp_path / "restored", expected=expected)
    assert [(page["width"], page["height"], page["dpi"]) for page in restored] == [
        (240, 160, 72.0),
        (240, 160, 72.0),
    ]
