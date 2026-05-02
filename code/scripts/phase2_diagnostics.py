"""Phase 2 diagnostic workbook.

Reads truth and predicted graphs for every fixture in a phase-2 run directory,
re-applies the same node/edge matching logic used by ``eval/scoring.py``, and
emits a single Excel workbook with:

* a top-level summary row per fixture (truth / pred / tp / fp / fn for
  equipment, instrument, other; edge tp/fp/fn for full-truth fixtures;
  cost, tokens, wall-clock);
* one sheet per fixture listing every truth and predicted node side-by-side
  with match status (TP / FP / FN), normalised label, IoU, bbox;
* one edge sheet per full-truth fixture;
* an "fp_fn_summary" sheet collecting all false positives and false negatives
  across fixtures so common LLM error patterns are easy to scan.

Usage:
    python scripts/phase2_diagnostics.py \\
        --run out/diagex-phase2 \\
        --condition baseline \\
        --datasets eval/datasets \\
        --xlsx out/diagex-phase2/diagnostics/phase2_diagnostics.xlsx
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import pandas as pd
from openpyxl.styles import Alignment, Font, PatternFill
from openpyxl.utils import get_column_letter

# Use the live scorer's helpers so the workbook never drifts from the eval.
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from eval.scoring import _norm_tag, _node_match  # noqa: E402


def _bbox_iou(a: dict, b: dict) -> float:
    ax1, ay1 = a["x"], a["y"]
    ax2, ay2 = ax1 + a["w"], ay1 + a["h"]
    bx1, by1 = b["x"], b["y"]
    bx2, by2 = bx1 + b["w"], by1 + b["h"]
    iw = max(0, min(ax2, bx2) - max(ax1, bx1))
    ih = max(0, min(ay2, by2) - max(ay1, by1))
    inter = iw * ih
    if inter == 0:
        return 0.0
    union = a["w"] * a["h"] + b["w"] * b["h"] - inter
    return inter / union if union > 0 else 0.0


@dataclass
class MatchedPair:
    truth: dict | None
    pred: dict | None
    iou: float
    label_match: bool
    status: str   # TP / FP / FN


class _NodeShim:
    """Minimal duck-typed adapter so eval.scoring._node_match accepts dicts."""

    def __init__(self, d: dict):
        self.kind = d["kind"]
        self.label = d.get("label", "")


def match_nodes(truth: list[dict], pred: list[dict], iou_threshold: float = 0.30) -> tuple[list[MatchedPair], dict[str, str]]:
    """Greedy 1-1 matching using eval/scoring.py's match rule.

    Returns (rows, mapping truth_id -> pred_id).
    """
    used: set[int] = set()
    pairs: list[MatchedPair] = []
    mapping: dict[str, str] = {}
    for tn in truth:
        best_idx, best_iou = -1, -1.0
        best_label_eq = False
        ts = _NodeShim(tn)
        for j, pn in enumerate(pred):
            if j in used or pn["kind"] != tn["kind"]:
                continue
            iou = _bbox_iou(tn["bbox_global"], pn["bbox_global"])
            ps = _NodeShim(pn)
            if not _node_match(ts, ps, iou, iou_threshold):
                continue
            label_eq = bool(tn.get("label")) and _norm_tag(tn["label"]) == _norm_tag(pn["label"])
            if iou > best_iou or (label_eq and best_idx == -1):
                best_idx, best_iou, best_label_eq = j, iou, label_eq
        if best_idx >= 0:
            used.add(best_idx)
            pairs.append(MatchedPair(truth=tn, pred=pred[best_idx],
                                     iou=max(best_iou, 0.0),
                                     label_match=best_label_eq, status="TP"))
            mapping[tn["id"]] = pred[best_idx]["id"]
        else:
            pairs.append(MatchedPair(truth=tn, pred=None, iou=0.0,
                                     label_match=False, status="FN"))
    for j, pn in enumerate(pred):
        if j not in used:
            pairs.append(MatchedPair(truth=None, pred=pn, iou=0.0,
                                     label_match=False, status="FP"))
    return pairs, mapping


def match_edges(truth_g: dict, pred_g: dict, mapping: dict[str, str]) -> dict[str, list[dict]]:
    """Mirror eval/scoring.py:edge_f1 to produce TP / FP / FN edge rows."""
    def key(e: dict, m: dict[str, str] | None = None) -> tuple:
        a, b = e["from_node"], e["to_node"]
        if m:
            a, b = m.get(a, a), m.get(b, b)
        return (tuple(sorted((a, b))), e.get("line_type", ""))

    tkeys = {key(e, mapping): e for e in truth_g.get("edges", [])}
    pkeys = {key(e): e for e in pred_g.get("edges", [])}
    out = {"TP": [], "FP": [], "FN": []}
    for k, te in tkeys.items():
        if k in pkeys:
            out["TP"].append({"truth": te, "pred": pkeys[k]})
        else:
            out["FN"].append({"truth": te, "pred": None})
    for k, pe in pkeys.items():
        if k not in tkeys:
            out["FP"].append({"truth": None, "pred": pe})
    return out


def _read_graph(path: Path) -> dict:
    if not path.exists():
        return {"nodes": [], "edges": []}
    return json.loads(path.read_text())


def _annotations_to_truth(jsonl: Path) -> dict:
    nodes: list[dict] = []
    if not jsonl.exists():
        return {"nodes": [], "edges": []}
    for line in jsonl.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        a = json.loads(line)
        nodes.append({
            "id": a["id"],
            "kind": a["kind"],
            "label": a.get("label", ""),
            "bbox_global": a["bbox_global"],
            "page_index": a.get("page_index", 0),
            "attributes": a.get("attributes", {}),
            "confidence": a.get("confidence", ""),
        })
    return {"nodes": nodes, "edges": []}


def _kind_counts(pairs: list[MatchedPair], kind: str) -> dict[str, int]:
    tp = sum(1 for p in pairs if p.status == "TP" and (p.truth or p.pred)["kind"] == kind)
    fn = sum(1 for p in pairs if p.status == "FN" and p.truth and p.truth["kind"] == kind)
    fp = sum(1 for p in pairs if p.status == "FP" and p.pred and p.pred["kind"] == kind)
    return {"tp": tp, "fp": fp, "fn": fn}


def _prf(tp: int, fp: int, fn: int) -> tuple[float, float, float]:
    p = tp / (tp + fp) if (tp + fp) else 0.0
    r = tp / (tp + fn) if (tp + fn) else 0.0
    f = 2 * p * r / (p + r) if (p + r) else 0.0
    return p, r, f


def _bbox_str(b: dict | None) -> str:
    if not b:
        return ""
    return f"({b['x']},{b['y']},{b['w']}x{b['h']})"


def _node_row(p: MatchedPair) -> dict:
    t = p.truth or {}
    pr = p.pred or {}
    kind = (t.get("kind") or pr.get("kind") or "")
    return {
        "status": p.status,
        "kind": kind,
        "truth_label": t.get("label", ""),
        "pred_label": pr.get("label", ""),
        "label_norm_match": "✓" if p.label_match else "",
        "iou": round(p.iou, 3) if p.iou else "",
        "truth_bbox": _bbox_str(t.get("bbox_global")),
        "pred_bbox": _bbox_str(pr.get("bbox_global")),
        "truth_eq_class": (t.get("attributes", {}) or {}).get("equipment_class", ""),
        "pred_eq_class": (pr.get("attributes", {}) or {}).get("equipment_class", ""),
        "truth_id": t.get("id", ""),
        "pred_id": pr.get("id", ""),
    }


def _edge_row(category: str, item: dict,
              truth_node_labels: dict[str, str] | None = None,
              pred_node_labels: dict[str, str] | None = None) -> dict:
    t = item.get("truth") or {}
    pr = item.get("pred") or {}
    truth_node_labels = truth_node_labels or {}
    pred_node_labels = pred_node_labels or {}
    return {
        "status": category,
        "truth_from": t.get("from_node", ""),
        "truth_from_label": truth_node_labels.get(t.get("from_node", ""), ""),
        "truth_to": t.get("to_node", ""),
        "truth_to_label": truth_node_labels.get(t.get("to_node", ""), ""),
        "truth_line_type": t.get("line_type", ""),
        "truth_attr_label": (t.get("attributes", {}) or {}).get("label", ""),
        "pred_from": pr.get("from_node", ""),
        "pred_from_label": pred_node_labels.get(pr.get("from_node", ""), ""),
        "pred_to": pr.get("to_node", ""),
        "pred_to_label": pred_node_labels.get(pr.get("to_node", ""), ""),
        "pred_line_type": pr.get("line_type", ""),
    }


def _autosize(ws, max_w: int = 60) -> None:
    for col_idx, col in enumerate(ws.columns, start=1):
        try:
            length = max((len(str(c.value)) for c in col if c.value is not None), default=10)
        except ValueError:
            length = 10
        ws.column_dimensions[get_column_letter(col_idx)].width = min(max(length + 2, 8), max_w)


_FILLS = {
    "TP": PatternFill("solid", fgColor="C6EFCE"),
    "FP": PatternFill("solid", fgColor="FFC7CE"),
    "FN": PatternFill("solid", fgColor="FFEB9C"),
}


def _colour_status_column(ws, status_col_letter: str = "A") -> None:
    for cell in ws[status_col_letter][1:]:  # skip header
        if cell.value in _FILLS:
            cell.fill = _FILLS[cell.value]


_TAG_PATTERN = re.compile(r"\b([A-Z]{1,4}[-/][A-Z0-9\-/]*\d[A-Z0-9\-/]*)\b")


def _extract_tag_root(label: str) -> str:
    """Pull a leading tag-shaped substring from a verbose label.

    "XV-2151 (shutdown valve, left feed-gas inlet)" -> "XV-2151"
    "Sea Water Strainer SP-1106A" -> "SP-1106A"
    "" if no tag-shape found.
    """
    if not label:
        return ""
    m = _TAG_PATTERN.search(label)
    return m.group(1) if m else ""


def _near_miss_pairs(pairs: list[MatchedPair]) -> list[dict]:
    """For every FN, find FP candidates of the same kind whose label shares a
    normalised prefix / substring or extracted tag-root, OR whose bbox IoU is
    in (0, 0.30). These are pairs scoring rejected but a human would call a
    match — useful for deciding whether scoring or the LLM is the cause.
    """
    fns = [p for p in pairs if p.status == "FN"]
    fps = [p for p in pairs if p.status == "FP"]
    rows: list[dict] = []
    for fn in fns:
        if not fn.truth:
            continue
        tn = fn.truth
        tn_lbl = _norm_tag(tn.get("label", ""))
        tn_root = _norm_tag(_extract_tag_root(tn.get("label", "")))
        for fp in fps:
            if not fp.pred:
                continue
            pn = fp.pred
            if pn["kind"] != tn["kind"]:
                continue
            pn_lbl = _norm_tag(pn.get("label", ""))
            pn_root = _norm_tag(_extract_tag_root(pn.get("label", "")))
            iou = _bbox_iou(tn["bbox_global"], pn["bbox_global"])
            reason: list[str] = []
            if tn_lbl and pn_lbl and (tn_lbl == pn_lbl):
                reason.append("exact-label")
            elif tn_lbl and pn_lbl and (tn_lbl in pn_lbl or pn_lbl in tn_lbl) and \
                    len(min(tn_lbl, pn_lbl, key=len)) >= 4:
                reason.append("label-substring")
            if tn_root and pn_root and tn_root == pn_root:
                reason.append("shared-tag-root")
            if 0 < iou < 0.30:
                reason.append(f"iou={iou:.2f}")
            if not reason:
                continue
            rows.append({
                "kind": tn["kind"],
                "reason": "+".join(reason),
                "iou": round(iou, 3),
                "truth_label": tn.get("label", ""),
                "pred_label": pn.get("label", ""),
                "truth_root": _extract_tag_root(tn.get("label", "")),
                "pred_root": _extract_tag_root(pn.get("label", "")),
                "truth_bbox": _bbox_str(tn["bbox_global"]),
                "pred_bbox": _bbox_str(pn["bbox_global"]),
                "truth_eq_class": (tn.get("attributes", {}) or {}).get("equipment_class", ""),
                "pred_eq_class": (pn.get("attributes", {}) or {}).get("equipment_class", ""),
            })
    return rows


def build(run_root: Path, condition: str, datasets: Path, xlsx: Path,
          results_csv: Path | None) -> None:
    runs_root = run_root / condition / "runs"
    fixtures = sorted(p.name for p in runs_root.iterdir() if p.is_dir())

    summary_rows: list[dict] = []
    fp_fn_rows: list[dict] = []
    per_fixture_pairs: dict[str, list[MatchedPair]] = {}
    per_fixture_edges: dict[str, dict[str, list[dict]]] = {}
    per_fixture_node_labels: dict[str, tuple[dict[str, str], dict[str, str]]] = {}

    # cost / wall-clock from results.csv if given
    cost_lookup: dict[str, dict[str, float]] = {}
    if results_csv and results_csv.exists():
        df = pd.read_csv(results_csv)
        runrow = df[df["metric_kind"] == "phase2_run"]
        for _, r in runrow.iterrows():
            cost_lookup[r["fixture"]] = {
                "cost_usd": float(r.get("cost_usd", 0.0) or 0.0),
                "input_tokens": int(r.get("input_tokens", 0) or 0),
                "output_tokens": int(r.get("output_tokens", 0) or 0),
                "wall_clock_s": float(r.get("wall_clock_s", 0.0) or 0.0),
                "source_type": r.get("source_type", ""),
                "domain": r.get("domain", ""),
                "entity_count_truth": int(r.get("entity_count_truth", 0) or 0),
            }

    for fix in fixtures:
        fix_dir = runs_root / fix
        ts_runs = sorted(p for p in fix_dir.iterdir() if p.is_dir())
        if not ts_runs:
            continue
        run_dir = ts_runs[-1]
        pred_g = _read_graph(run_dir / "graph.json")
        ds_dir = datasets / fix
        truth_graph_path = ds_dir / "graph.truth.json"
        truth_g = _read_graph(truth_graph_path)
        has_full_truth = bool(truth_g.get("nodes"))
        if not has_full_truth:
            truth_g = _annotations_to_truth(ds_dir / "annotations.truth.jsonl")

        pairs, mapping = match_nodes(truth_g["nodes"], pred_g["nodes"])
        per_fixture_pairs[fix] = pairs

        # Cache id->label maps for the edge sheets.
        per_fixture_node_labels[fix] = (
            {n["id"]: n.get("label", "") for n in truth_g["nodes"]},
            {n["id"]: n.get("label", "") for n in pred_g["nodes"]},
        )

        edges = (match_edges(truth_g, pred_g, mapping)
                 if has_full_truth and truth_g.get("edges") else None)
        if edges is not None:
            per_fixture_edges[fix] = edges

        eq = _kind_counts(pairs, "equipment")
        inst = _kind_counts(pairs, "instrument")
        all_kinds = {(p.truth or p.pred)["kind"] for p in pairs}
        other_kinds = all_kinds - {"equipment", "instrument"}
        other = {"tp": 0, "fp": 0, "fn": 0}
        for k in other_kinds:
            for sub in ("tp", "fp", "fn"):
                other[sub] += _kind_counts(pairs, k)[sub]

        ep, er, ef = _prf(eq["tp"], eq["fp"], eq["fn"])
        ip, ir, if_ = _prf(inst["tp"], inst["fp"], inst["fn"])
        op, or_, of = _prf(other["tp"], other["fp"], other["fn"])

        edge_p = edge_r = edge_f = None
        edge_tp = edge_fp = edge_fn = None
        if edges is not None:
            edge_tp = len(edges["TP"])
            edge_fp = len(edges["FP"])
            edge_fn = len(edges["FN"])
            edge_p, edge_r, edge_f = _prf(edge_tp, edge_fp, edge_fn)

        # tag OCR EM (label exact match among matched pairs, divided by truth count)
        truth_count = sum(1 for p in pairs if p.truth)
        tag_em_count = sum(1 for p in pairs if p.status == "TP" and p.label_match)
        tag_em = tag_em_count / truth_count if truth_count else 0.0

        cinfo = cost_lookup.get(fix, {})
        summary_rows.append({
            "fixture": fix,
            "source_type": cinfo.get("source_type", ""),
            "domain": cinfo.get("domain", ""),
            "truth_kind": "graph" if has_full_truth else "annotations",
            "truth_total": len(truth_g["nodes"]),
            "pred_total": len(pred_g["nodes"]),
            "eq_truth": eq["tp"] + eq["fn"],
            "eq_pred": eq["tp"] + eq["fp"],
            "eq_tp": eq["tp"], "eq_fp": eq["fp"], "eq_fn": eq["fn"],
            "eq_P": round(ep, 3), "eq_R": round(er, 3), "eq_F1": round(ef, 3),
            "inst_truth": inst["tp"] + inst["fn"],
            "inst_pred": inst["tp"] + inst["fp"],
            "inst_tp": inst["tp"], "inst_fp": inst["fp"], "inst_fn": inst["fn"],
            "inst_P": round(ip, 3), "inst_R": round(ir, 3), "inst_F1": round(if_, 3),
            "other_truth": other["tp"] + other["fn"],
            "other_pred": other["tp"] + other["fp"],
            "other_tp": other["tp"], "other_fp": other["fp"], "other_fn": other["fn"],
            "other_F1": round(of, 3),
            "tag_OCR_EM": round(tag_em, 3),
            "edge_tp": edge_tp, "edge_fp": edge_fp, "edge_fn": edge_fn,
            "edge_P": (round(edge_p, 3) if edge_p is not None else None),
            "edge_R": (round(edge_r, 3) if edge_r is not None else None),
            "edge_F1": (round(edge_f, 3) if edge_f is not None else None),
            "cost_usd": round(cinfo.get("cost_usd", 0.0), 3),
            "input_tokens": cinfo.get("input_tokens", 0),
            "output_tokens": cinfo.get("output_tokens", 0),
            "wall_clock_s": round(cinfo.get("wall_clock_s", 0.0), 1),
        })
        for p in pairs:
            if p.status in ("FP", "FN"):
                row = _node_row(p)
                row["fixture"] = fix
                fp_fn_rows.append(row)

    near_rows: list[dict] = []
    for fix, pairs in per_fixture_pairs.items():
        for r in _near_miss_pairs(pairs):
            r["fixture"] = fix
            near_rows.append(r)

    summary_df = pd.DataFrame(summary_rows)
    fp_fn_df = pd.DataFrame(fp_fn_rows)
    near_df = pd.DataFrame(near_rows)

    # Add a per-fixture column to summary that estimates how many FN/FP could
    # be reclaimed if matching also accepted shared tag-roots / label
    # substrings. This is the "scoring ceiling" if the LLM output is
    # accepted as-is.
    if not near_df.empty:
        ceil = (near_df.groupby("fixture")
                       .apply(lambda d: d.drop_duplicates(subset=["truth_label"]).shape[0])
                       .rename("recoverable_with_label_relax"))
        summary_df = summary_df.merge(ceil, left_on="fixture", right_index=True, how="left")
        summary_df["recoverable_with_label_relax"] = (
            summary_df["recoverable_with_label_relax"].fillna(0).astype(int)
        )

    xlsx.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(xlsx, engine="openpyxl") as w:
        summary_df.to_excel(w, sheet_name="summary", index=False)
        # Per-fixture node sheets — kind sorted so equipment/instrument grouped
        for fix, pairs in per_fixture_pairs.items():
            rows = [_node_row(p) for p in pairs]
            df = pd.DataFrame(rows)
            df.sort_values(by=["kind", "status", "truth_label", "pred_label"],
                           inplace=True)
            df.to_excel(w, sheet_name=f"nodes_{fix}"[:31], index=False)
        for fix, edges in per_fixture_edges.items():
            tlab, plab = per_fixture_node_labels.get(fix, ({}, {}))
            rows = []
            for cat in ("TP", "FN", "FP"):
                for item in edges[cat]:
                    rows.append(_edge_row(cat, item, tlab, plab))
            pd.DataFrame(rows).to_excel(w, sheet_name=f"edges_{fix}"[:31], index=False)
        if not fp_fn_df.empty:
            fp_fn_df.sort_values(by=["fixture", "kind", "status"], inplace=True)
            fp_fn_df.to_excel(w, sheet_name="fp_fn_all", index=False)
        if not near_df.empty:
            near_df.sort_values(by=["fixture", "kind", "reason"], inplace=True)
            near_df.to_excel(w, sheet_name="near_miss_pairs", index=False)

    # post-process: freeze headers, apply colour fills, autosize
    from openpyxl import load_workbook
    wb = load_workbook(xlsx)
    for name in wb.sheetnames:
        ws = wb[name]
        ws.freeze_panes = "A2"
        for cell in ws[1]:
            cell.font = Font(bold=True)
            cell.alignment = Alignment(horizontal="center")
        if name == "summary":
            _autosize(ws, max_w=22)
            continue
        # colour status column for node/edge sheets
        if "status" in [c.value for c in ws[1]]:
            status_col_idx = next(i for i, c in enumerate(ws[1], start=1)
                                  if c.value == "status")
            _colour_status_column(ws, get_column_letter(status_col_idx))
        _autosize(ws, max_w=55)
    wb.save(xlsx)
    print(f"wrote {xlsx} ({len(per_fixture_pairs)} fixtures)")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path,
                    help="phase-2 output root, e.g. out/diagex-phase2")
    ap.add_argument("--condition", default="baseline")
    ap.add_argument("--datasets", required=True, type=Path,
                    help="datasets dir (eval/datasets)")
    ap.add_argument("--xlsx", required=True, type=Path)
    ap.add_argument("--results-csv", type=Path, default=None)
    args = ap.parse_args()

    results_csv = args.results_csv or (args.run / "results.csv")
    build(args.run, args.condition, args.datasets, args.xlsx, results_csv)


if __name__ == "__main__":
    main()
