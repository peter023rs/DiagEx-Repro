"""Rescore existing Phase-2 runs against current eval/scoring.py.

Walks ``<run-root>/<condition>/runs/<fixture>/<ts>/graph.json`` and the
matching ``eval/datasets/<fixture>/`` truth, recomputes equipment_f1,
instrument_f1, edge_f1, tag_OCR_EM and writes a new ``results.csv`` and
``report.md``. The original ``results.csv`` is preserved as ``results.prev.csv``.

Usage:
    python scripts/rescore_phase2.py \\
        --run out/diagex-phase2 \\
        --datasets eval/datasets \\
        --condition baseline
"""

from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "src"))

from diagex.vision.models import (  # noqa: E402
    BBox, ReconciledEdge, ReconciledGraph, ReconciledNode,
)
from eval.scoring import (  # noqa: E402
    edge_f1,
    node_f1,
    tag_ocr_exact_match,
)


def _load_graph(path: Path) -> ReconciledGraph:
    if not path.exists():
        return ReconciledGraph(source_path="", nodes=[], edges=[])
    raw = json.loads(path.read_text())

    def _node(d: dict) -> ReconciledNode:
        b = d["bbox_global"]
        return ReconciledNode(
            id=d["id"], kind=d["kind"], label=d.get("label", ""),
            bbox_global=BBox(x=b["x"], y=b["y"], w=b["w"], h=b["h"]),
            page_index=d.get("page_index", 0),
            attributes=d.get("attributes", {}),
            confidence=d.get("confidence", "high"),
        )

    def _edge(d: dict) -> ReconciledEdge:
        return ReconciledEdge(
            id=d["id"], from_node=d["from_node"], to_node=d["to_node"],
            line_type=d.get("line_type", "process"),
            polyline_global=[tuple(p) for p in d.get("polyline_global", [])],
            confidence=d.get("confidence", "high"),
            cross_sheet=d.get("cross_sheet", False),
            attributes=d.get("attributes", {}),
        )

    return ReconciledGraph(
        source_path=raw.get("source_path", ""),
        nodes=[_node(n) for n in raw.get("nodes", [])],
        edges=[_edge(e) for e in raw.get("edges", [])],
    )


def _annotations_to_nodes(jsonl: Path) -> list[ReconciledNode]:
    if not jsonl.exists():
        return []
    out: list[ReconciledNode] = []
    for line in jsonl.read_text().splitlines():
        line = line.strip()
        if not line:
            continue
        a = json.loads(line)
        b = a["bbox_global"]
        out.append(ReconciledNode(
            id=a["id"], kind=a["kind"], label=a.get("label", ""),
            bbox_global=BBox(x=b["x"], y=b["y"], w=b["w"], h=b["h"]),
            page_index=a.get("page_index", 0),
            attributes=a.get("attributes", {}),
            confidence=a.get("confidence", "high"),
        ))
    return out


def _truth_for(fix_dir: Path) -> ReconciledGraph:
    g = _load_graph(fix_dir / "graph.truth.json")
    if g.nodes:
        return g
    return ReconciledGraph(
        source_path="",
        nodes=_annotations_to_nodes(fix_dir / "annotations.truth.jsonl"),
        edges=[],
    )


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", required=True, type=Path)
    ap.add_argument("--datasets", required=True, type=Path)
    ap.add_argument("--condition", default="baseline")
    args = ap.parse_args()

    runs_root = args.run / args.condition / "runs"
    csv_path = args.run / "results.csv"
    if csv_path.exists():
        shutil.copy(csv_path, args.run / "results.prev.csv")

    df = pd.read_csv(csv_path) if csv_path.exists() else pd.DataFrame()
    # Pull preserved fixture-level columns from the existing run rows.
    cost_lookup: dict[str, dict] = {}
    if not df.empty:
        runrow = df[df["metric_kind"] == "phase2_run"]
        for _, r in runrow.iterrows():
            cost_lookup[r["fixture"]] = {
                "cost_usd": float(r.get("cost_usd", 0.0) or 0.0),
                "input_tokens": int(r.get("input_tokens", 0) or 0),
                "output_tokens": int(r.get("output_tokens", 0) or 0),
                "wall_clock_s": float(r.get("wall_clock_s", 0.0) or 0.0),
                "source_type": r.get("source_type", ""),
                "domain": r.get("domain", ""),
                "run_id": r.get("run_id", ""),
            }

    new_rows: list[dict] = []
    summary: list[tuple[str, dict]] = []
    for fix_dir in sorted(p for p in runs_root.iterdir() if p.is_dir()):
        fix = fix_dir.name
        ts_dirs = sorted(p for p in fix_dir.iterdir() if p.is_dir())
        if not ts_dirs:
            continue
        run_dir = ts_dirs[-1]
        pred = _load_graph(run_dir / "graph.json")
        truth = _truth_for(args.datasets / fix)
        has_full = bool(truth.edges)

        eq = node_f1(truth.nodes, pred.nodes, kind_filter={"equipment"})
        inst = node_f1(truth.nodes, pred.nodes, kind_filter={"instrument"})
        # OPC F1 only meaningful when truth labels OPCs (full-graph fixtures).
        truth_has_opc = any(n.kind == "opc" for n in truth.nodes)
        opc = (node_f1(truth.nodes, pred.nodes, kind_filter={"opc"})
               if truth_has_opc else None)
        tag_em = tag_ocr_exact_match(truth.nodes, pred.nodes)
        edge = edge_f1(truth, pred) if has_full else None

        ci = cost_lookup.get(fix, {})
        base = {
            "run_id": ci.get("run_id", ""),
            "condition": args.condition,
            "fixture": fix,
            "phase": 2,
            "family": "", "query_id": "", "scoring": "",
            "trial": 0, "input_tokens": 0, "output_tokens": 0,
            "wall_clock_s": 0.0, "cost_usd": 0.0,
            "source_type": ci.get("source_type", ""),
            "domain": ci.get("domain", ""),
            "entity_count_truth": len(truth.nodes),
        }
        new_rows.append({**base, "metric_kind": "phase2_equipment_f1",
                         "score": eq.f1,
                         "detail": f"P={eq.precision:.2f} R={eq.recall:.2f} "
                                   f"tp={eq.tp} fp={eq.fp} fn={eq.fn}"})
        new_rows.append({**base, "metric_kind": "phase2_instrument_f1",
                         "score": inst.f1,
                         "detail": f"P={inst.precision:.2f} R={inst.recall:.2f} "
                                   f"tp={inst.tp} fp={inst.fp} fn={inst.fn}"})
        if opc is not None:
            new_rows.append({**base, "metric_kind": "phase2_opc_f1",
                             "score": opc.f1,
                             "detail": f"P={opc.precision:.2f} R={opc.recall:.2f} "
                                       f"tp={opc.tp} fp={opc.fp} fn={opc.fn}"})
        new_rows.append({**base, "metric_kind": "phase2_tag_ocr_em",
                         "score": tag_em, "detail": f"tag-OCR EM = {tag_em:.2f}"})
        if edge is not None:
            new_rows.append({**base, "metric_kind": "phase2_edge_f1",
                             "score": edge.f1,
                             "detail": f"edge F1 (full-truth fixture) "
                                       f"tp={edge.tp} fp={edge.fp} fn={edge.fn}"})
        # Carry over prior validation + run cost rows untouched.
        if not df.empty:
            for keep in ("phase2_dexpi_validates", "phase2_run"):
                rows = df[(df.fixture == fix) & (df.metric_kind == keep)]
                for _, r in rows.iterrows():
                    new_rows.append(r.to_dict())

        summary.append((fix, {
            "eq_F1": round(eq.f1, 3),
            "inst_F1": round(inst.f1, 3),
            "opc_F1": (round(opc.f1, 3) if opc is not None else None),
            "edge_F1": (round(edge.f1, 3) if edge else None),
            "tag_OCR_EM": round(tag_em, 3),
            "cost": round(ci.get("cost_usd", 0.0), 3),
        }))

    new_df = pd.DataFrame(new_rows)
    new_df.to_csv(csv_path, index=False)
    print(f"wrote {csv_path} ({len(new_df)} rows)")

    print(f"\n{'fixture':<18} {'eq_F1':>6} {'inst_F1':>7} {'opc_F1':>6} {'edge_F1':>7} {'tag_EM':>6} {'cost':>6}")
    for fix, s in summary:
        opc_str = "-" if s["opc_F1"] is None else f"{s['opc_F1']:.3f}"
        edge_str = "-" if s["edge_F1"] is None else f"{s['edge_F1']:.3f}"
        print(f"{fix:<18} {s['eq_F1']:>6.3f} {s['inst_F1']:>7.3f} "
              f"{opc_str:>6} {edge_str:>7} {s['tag_OCR_EM']:>6.3f} "
              f"{s['cost']:>6.2f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
