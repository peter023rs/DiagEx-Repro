"""Tests for eval/scoring.py — pure scorers, no I/O."""

from __future__ import annotations

import pytest

from diagex.vision.models import (
    BBox,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)
from eval.scoring import (
    edge_f1,
    node_f1,
    parse_bool_answer,
    parse_connectivity_endpoints,
    parse_int_answer,
    parse_list_answer,
    score_contains,
    score_exact,
    score_graph_reachability,
    score_numeric_tolerance,
    score_query,
    score_set_match,
    tag_ocr_exact_match,
)


def _node(nid: str, kind: str, label: str, x=0, y=0, w=10, h=10) -> ReconciledNode:
    return ReconciledNode(
        id=nid, kind=kind, label=label,
        bbox_global=BBox(x=x, y=y, w=w, h=h), page_index=0,
        confidence="high",
    )


def _edge(eid: str, a: str, b: str, line_type: str = "process") -> ReconciledEdge:
    return ReconciledEdge(
        id=eid, from_node=a, to_node=b, line_type=line_type,
        polyline_global=[(0, 0), (1, 1)], confidence="high",
    )


# ---- parsers -----------------------------------------------------------------


def test_parse_list_answer_strips_bullets_and_numbers():
    text = "- TT-1\n* TT-2\n1. TT-3\n2) TT-4\nFIC-102."
    assert parse_list_answer(text) == ["TT-1", "TT-2", "TT-3", "TT-4", "FIC-102"]


def test_parse_list_answer_extracts_xml_answer_block():
    """Models commonly wrap the bare-tag list in <answer>...</answer> after
    a prose justification. The parser must use only the inner block when
    present — observed on dexpi-reference-q1 (2026-04-27)."""
    text = (
        "P4711 and P4712 are pumps (confirmed by data tables).\n\n"
        "<answer>\nP4711\nP4712\n</answer>"
    )
    assert parse_list_answer(text) == ["P4711", "P4712"]


def test_parse_list_answer_drops_triple_backtick_fences():
    """Markdown code-fence wrapping is common with chatty models — observed
    on open100-3-q1 (2026-04-27). Bare and language-tagged fences both."""
    assert parse_list_answer("```\nP-101\nP-102\n```") == ["P-101", "P-102"]
    assert parse_list_answer("```text\nP-101\nP-102\n```") == ["P-101", "P-102"]


def test_parse_list_answer_strips_single_char_label_prefix():
    """Models sometimes echo question labels like 'streams A, D, E, C' as
    "A: V-1001, D: V-1002, ..." — observed on tennessee1-q1 (2026-04-27).
    A leading single-char + colon prefix is treated as a list label, not
    part of the tag. Multi-char prefixes are left alone (likely real tags)."""
    out = parse_list_answer("A: V-1001, D: V-1002, E: V-1003, C: V-1004.")
    assert out == ["V-1001", "V-1002", "V-1003", "V-1004"]
    # Multi-char prefix preserved.
    assert parse_list_answer("AA: V-1001") == ["AA: V-1001"]


def test_parse_int_answer_finds_first_int():
    assert parse_int_answer("There are 5 transmitters.") == 5
    assert parse_int_answer("none") is None


def test_parse_bool_answer_yes_no_variants():
    assert parse_bool_answer("Yes.") is True
    assert parse_bool_answer("no, see edge 0") is False
    assert parse_bool_answer("maybe") is None


def test_parse_connectivity_endpoints_handles_backticks():
    src, dst = parse_connectivity_endpoints("Is there a process flow path from `P-207` to `T-211`?")
    assert (src, dst) == ("P-207", "T-211")
    assert parse_connectivity_endpoints("How many pumps?") is None


# ---- scorers -----------------------------------------------------------------


def test_score_exact_normalises_case_and_whitespace():
    assert score_exact("tank", "  Tank ").score == 1.0
    assert score_exact("tank", "tower").score == 0.0


def test_score_contains_case_insensitive_default():
    assert score_contains("tank", "T-411 Hot PUW2 TANK").score == 1.0
    assert score_contains("pump", "tank centre").score == 0.0


def test_score_set_match_f1_partial():
    res = score_set_match(["TT-1", "TT-2", "TT-3"], ["TT-1", "TT-2", "TT-9"])
    # 2/3 precision == 0.667, 2/3 recall == 0.667, F1 == 0.667
    assert pytest.approx(res.score, rel=1e-3) == 0.6667


def test_score_set_match_normalises_punctuation():
    res = score_set_match(["FIC-102"], ["fic 102"])
    assert res.score == 1.0


def test_score_numeric_tolerance_5_percent():
    assert score_numeric_tolerance(20, 21).score == 1.0
    assert score_numeric_tolerance(20, 22).score == 0.0


def test_score_graph_reachability_actual_bool_path():
    res = score_graph_reachability(True, True)
    assert res.score == 1.0


def test_score_graph_reachability_falls_back_to_graph():
    g = ReconciledGraph(
        source_path="x.pdf",
        nodes=[_node("a", "equipment", "P-207"), _node("b", "equipment", "T-211")],
        edges=[_edge("e1", "a", "b", "process")],
    )
    res = score_graph_reachability(
        expected=True, actual=None,
        params={"line_types": ["process"]},
        graph=g,
        question="Is there a process flow path from `P-207` to `T-211`?",
    )
    assert res.score == 1.0


def test_score_graph_reachability_endpoint_missing():
    g = ReconciledGraph(source_path="x.pdf", nodes=[_node("a", "equipment", "P-207")], edges=[])
    res = score_graph_reachability(
        expected=True, actual=None,
        params={"line_types": ["process"]},
        graph=g,
        question="Is there a process flow path from `P-207` to `T-999`?",
    )
    assert res.score == 0.0
    assert "endpoint not found" in res.detail


def test_score_query_dispatches_by_kind():
    res = score_query(scoring="exact", expected="tank", actual="Tank", params=None)
    assert res.score == 1.0
    with pytest.raises(ValueError):
        score_query(scoring="bogus", expected="x", actual="x", params=None)


# ---- node / edge F1 ----------------------------------------------------------


def test_node_f1_label_match_ignores_iou():
    truth = [_node("t1", "equipment", "P-207", 0, 0, 10, 10)]
    pred = [_node("p1", "equipment", "P-207", 100, 100, 10, 10)]  # disjoint bbox
    res = node_f1(truth, pred)
    assert res.tp == 1 and res.fp == 0 and res.fn == 0
    assert res.f1 == 1.0


def test_node_f1_iou_match_with_kind_filter():
    truth = [_node("t1", "equipment", "Pump-A", 0, 0, 100, 100)]
    pred = [_node("p1", "equipment", "Pump-B", 10, 10, 100, 100)]  # high IoU
    res = node_f1(truth, pred, kind_filter={"equipment"})
    assert res.tp == 1


def test_node_f1_kind_mismatch_no_match():
    truth = [_node("t1", "equipment", "Foo")]
    pred = [_node("p1", "instrument", "Foo")]
    res = node_f1(truth, pred)
    assert res.tp == 0


def test_node_f1_label_match_wins_over_iou_only_candidate():
    """Regression: when truth has two adjacent bubbles VSHH-2901B and
    HS-2901A1 LOCAL/REMOTE, and pred has the same two labels at slightly
    shifted positions, every truth must match its label-twin in pred
    even if a wrong-label pred has a higher IoU with it.
    """
    # Two truth bubbles in the same neighbourhood.
    truth = [
        _node("tA", "instrument", "VSHH-2901B",
              x=1620, y=2185, w=90, h=90),
        _node("tB", "instrument", "HS-2901A1 LOCAL/REMOTE",
              x=1625, y=2190, w=90, h=90),  # very close to tA
    ]
    # Pred: same two labels, slightly shifted. Each pred has IoU > threshold
    # with BOTH truth bboxes — the matcher must use labels to disambiguate.
    pred = [
        _node("pA", "instrument", "VSHH-2901B",
              x=1622, y=2187, w=90, h=90),
        _node("pB", "instrument", "HS-2901A1 LOCAL/REMOTE",
              x=1627, y=2192, w=90, h=90),
    ]
    res = node_f1(truth, pred)
    # Both must match by label — 2 TP, 0 FP, 0 FN.
    assert res.tp == 2 and res.fp == 0 and res.fn == 0


def test_edge_f1_through_node_mapping():
    truth = ReconciledGraph(
        source_path="x.pdf",
        nodes=[_node("ta", "equipment", "A"), _node("tb", "equipment", "B")],
        edges=[_edge("te", "ta", "tb", "process")],
    )
    pred = ReconciledGraph(
        source_path="x.pdf",
        nodes=[_node("pa", "equipment", "A"), _node("pb", "equipment", "B")],
        edges=[_edge("pe", "pa", "pb", "process")],
    )
    res = edge_f1(truth, pred)
    assert res.f1 == 1.0


def test_tag_ocr_exact_match_iou_only():
    truth = [_node("t1", "equipment", "FIC-102", 0, 0, 100, 100)]
    pred_match = [_node("p1", "equipment", "fic 102", 5, 5, 100, 100)]
    pred_miss = [_node("p1", "equipment", "FIC-I02", 5, 5, 100, 100)]
    assert tag_ocr_exact_match(truth, pred_match) == 1.0
    assert tag_ocr_exact_match(truth, pred_miss) == 0.0


# ---- relaxed-match rules (tag-root + OPC) -----------------------------------


def test_node_f1_matches_on_shared_tag_root():
    """Verbose LLM label sharing the leading tag with bare-tag truth."""
    truth = [_node("t1", "equipment", "XV-2151", 0, 0, 10, 10)]
    pred = [_node("p1", "equipment",
                  "XV-2151 (shutdown valve, left feed-gas inlet)",
                  500, 500, 10, 10)]   # disjoint bbox, verbose label
    res = node_f1(truth, pred)
    assert res.tp == 1 and res.fp == 0 and res.fn == 0


def test_node_f1_matches_on_trailing_tag_root():
    """LLM emits 'Sea Water Strainer SP-1106A' for truth 'SP-1106A'."""
    truth = [_node("t1", "equipment", "SP-1106A", 0, 0, 10, 10)]
    pred = [_node("p1", "equipment", "Sea Water Strainer SP-1106A",
                  500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 1


def test_node_f1_opc_loose_match_on_first_token():
    """OPCs tolerate directional-suffix disagreement."""
    truth = [_node("t1", "opc", "Feed A inlet", 0, 0, 10, 10)]
    pred = [_node("p1", "opc", "Feed A", 500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 1


def test_node_f1_opc_match_strips_opc_marker_prefix():
    """Customer-style truth ('OPC IN: <desc>') matches simple LLM label."""
    truth = [_node("t1", "opc",
                   "OPC IN: Spent Butane from V-234-002A~D "
                   "(P-234-03016-F3D-8\"-Is)",
                   0, 0, 10, 10)]
    pred = [_node("p1", "opc", "Spent Butane inlet", 500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 1


def test_node_f1_opc_match_handles_id_encoded_truth():
    """DEXPI-style truth ('OPC-IN-MNb47121') matches LLM label 'MNb'."""
    truth = [_node("t1", "opc", "OPC-IN-MNb47121", 0, 0, 10, 10)]
    pred = [_node("p1", "opc", "MNb inlet", 500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 1


def test_node_f1_opc_no_match_when_identity_differs():
    truth = [_node("t1", "opc", "OPC IN: Spent Butane", 0, 0, 10, 10)]
    pred = [_node("p1", "opc", "Sea Water Supply inlet", 500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 0


def test_node_f1_no_root_match_when_roots_differ():
    truth = [_node("t1", "equipment", "XV-2151", 0, 0, 10, 10)]
    pred = [_node("p1", "equipment", "XV-2152", 500, 500, 10, 10)]
    res = node_f1(truth, pred)
    assert res.tp == 0


def test_tag_ocr_remains_strict_on_verbose_labels():
    """tag_ocr_exact_match is the literal-OCR metric — relaxed match must
    not leak into it."""
    truth = [_node("t1", "equipment", "XV-2151", 0, 0, 100, 100)]
    pred = [_node("p1", "equipment", "XV-2151 (shutdown valve)", 5, 5, 100, 100)]
    assert tag_ocr_exact_match(truth, pred) == 0.0
