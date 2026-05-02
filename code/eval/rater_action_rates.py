"""Compute rater confirm/revise/reject/add rates from existing ground-truth audit logs.

Reads `graph.truth.history.json` (post-VIA walk-through) and
`via_correction.summary.json` (initial bbox/label correction stage) for each
full-truth fixture and emits a single aggregate report. Used by the paper to
quantify self-grading bias in the bootstrap-then-correct workflow.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).resolve().parent.parent
FIXTURES = ("dexpi-reference", "butane1", "tennessee1")


def _load(stem: str) -> tuple[dict[str, Any], dict[str, Any]]:
    base = REPO_ROOT / "eval" / "datasets" / stem
    with (base / "graph.truth.history.json").open() as f:
        history = json.load(f)
    with (base / "via_correction.summary.json").open() as f:
        via = json.load(f)
    return history, via


def _per_fixture(history: dict[str, Any], via: dict[str, Any]) -> dict[str, Any]:
    h = history["summary"]

    via_reviewable = via["bootstrap_reviewable_nodes"]
    via_matched = via["matched"]
    via_dropped = via["dropped"]
    via_added = via["added"]
    via_bbox_edited = via["bbox_edited"]
    via_label_edited = via["label_edited"]

    return {
        "nodes": {
            "via_reviewable": via_reviewable,
            "via_matched": via_matched,
            "via_dropped": via_dropped,
            "via_added": via_added,
            "via_bbox_edited": via_bbox_edited,
            "via_label_edited": via_label_edited,
            "history_bootstrap_v2": h["bootstrap_nodes"],
            "history_kept": h["kept"],
            "history_revised": h["revised"],
            "history_dropped": h["dropped"],
            "history_added": h["added"],
            "final": h["final_nodes"],
        },
        "edges": {
            "via_kept": via["edges_kept"],
            "via_auto_dropped": via["edges_auto_dropped"],
            "history_bootstrap": h["bootstrap_edges"],
            "history_kept": h["edge_kept"],
            "history_revised": h["edge_revised"],
            "history_dropped": h["edge_dropped"],
            "history_added": h["edge_added"],
            "final": h["final_edges"],
        },
    }


def _sum(parts: list[dict[str, Any]], key: str, sub: str) -> int:
    return sum(p[key][sub] for p in parts)


def main() -> None:
    parts: dict[str, dict[str, Any]] = {}
    for stem in FIXTURES:
        history, via = _load(stem)
        parts[stem] = _per_fixture(history, via)

    fixtures = list(parts.values())

    n_via_reviewable = _sum(fixtures, "nodes", "via_reviewable")
    n_via_matched = _sum(fixtures, "nodes", "via_matched")
    n_via_dropped = _sum(fixtures, "nodes", "via_dropped")
    n_via_added = _sum(fixtures, "nodes", "via_added")
    n_via_bbox_edited = _sum(fixtures, "nodes", "via_bbox_edited")
    n_via_label_edited = _sum(fixtures, "nodes", "via_label_edited")
    n_hist_dropped = _sum(fixtures, "nodes", "history_dropped")
    n_hist_added = _sum(fixtures, "nodes", "history_added")
    n_final = _sum(fixtures, "nodes", "final")

    n_confirmed = n_via_matched - n_hist_dropped
    n_revised_lower = max(n_via_bbox_edited, n_via_label_edited)
    n_revised_upper = n_via_bbox_edited + n_via_label_edited
    n_dropped_total = n_via_dropped + n_hist_dropped
    n_added_total = n_via_added + n_hist_added

    e_via_kept = _sum(fixtures, "edges", "via_kept")
    e_via_auto_dropped = _sum(fixtures, "edges", "via_auto_dropped")
    e_hist_bootstrap = _sum(fixtures, "edges", "history_bootstrap")
    e_hist_kept = _sum(fixtures, "edges", "history_kept")
    e_hist_revised = _sum(fixtures, "edges", "history_revised")
    e_hist_dropped = _sum(fixtures, "edges", "history_dropped")
    e_hist_added = _sum(fixtures, "edges", "history_added")
    e_final = _sum(fixtures, "edges", "final")

    def pct(n: int, d: int) -> float:
        return round(100.0 * n / d, 1) if d else 0.0

    aggregate = {
        "fixtures": list(FIXTURES),
        "nodes": {
            "model_proposed_reviewable": n_via_reviewable,
            "rater_added_beyond_bootstrap": n_added_total,
            "final_ground_truth": n_final,
            "confirm_unchanged": n_via_matched - n_revised_upper,
            "confirm_count": n_confirmed,
            "revise_count_lower": n_revised_lower,
            "revise_count_upper": n_revised_upper,
            "reject_count": n_dropped_total,
            "add_count": n_added_total,
            "confirm_pct": pct(n_confirmed, n_via_reviewable),
            "reject_pct": pct(n_dropped_total, n_via_reviewable),
            "revise_pct_lower": pct(n_revised_lower, n_via_reviewable),
            "revise_pct_upper": pct(n_revised_upper, n_via_reviewable),
            "add_pct_of_final": pct(n_added_total, n_final),
        },
        "edges": {
            "rater_added_beyond_bootstrap": e_hist_added,
            "final_ground_truth": e_final,
            "history_kept": e_hist_kept,
            "history_revised": e_hist_revised,
            "history_dropped": e_hist_dropped,
            "history_added": e_hist_added,
            "history_bootstrap_total": e_hist_bootstrap,
            "history_confirm_pct": pct(e_hist_kept, e_hist_bootstrap),
            "history_revise_pct": pct(e_hist_revised, e_hist_bootstrap),
            "history_reject_pct": pct(e_hist_dropped, e_hist_bootstrap),
            "add_pct_of_final": pct(e_hist_added, e_final),
        },
        "per_fixture": parts,
    }

    out_path = REPO_ROOT / "out" / "diagex-phase2" / "rater_action_rates.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w") as f:
        json.dump(aggregate, f, indent=2)
    print(json.dumps(aggregate, indent=2))
    print(f"\nWrote {out_path}")


if __name__ == "__main__":
    main()
