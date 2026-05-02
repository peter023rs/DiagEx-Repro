"""Record cassettes for the eval harness from known-good live runs.

Walks the live-run artefacts under ``runs/`` and ``out/diagex-*/`` and
copies them into ``eval/cassettes/<condition>/<stem>/`` in the layout
``{phase1.json, graph.json, summary.json}`` consumed by
``eval.run_paper_eval --use-cassettes``. See plan/etfa2026-evaluation-plan.md
§ 7.4 and § 10 step 16.

Usage:
    python scripts/record_cassettes.py
    python scripts/record_cassettes.py --conditions baseline
    python scripts/record_cassettes.py --dry-run
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import shutil
from dataclasses import dataclass
from pathlib import Path

import typer
from rich.console import Console

from eval._loader import (
    load_fixture_truth,
    load_manifest,
    load_predicted_graph,
)
from eval.qa_analysis import _collect_runs_per_trial
from eval.scoring import node_f1

REPO = Path(__file__).resolve().parent.parent
MANIFEST = REPO / "eval/datasets/manifest.yaml"
DATASET_ROOT = REPO / "eval/datasets"
RUNS_ROOT = REPO / "runs"
CASSETTES_ROOT = REPO / "eval/cassettes"

PHASE1_BASELINE_CSV = REPO / "out/diagex-phase1/results.csv"
PHASE2_BASELINE_CSV = REPO / "out/diagex-phase2/results.csv"
PHASE2_BASELINE_RUNS = REPO / "out/diagex-phase2/baseline/runs"
ABLATION_CSV = REPO / "out/diagex-ablation/results.csv"
ABLATION_RUNS = REPO / "out/diagex-ablation/ablation-no-tile/runs"

# Phase 1 baseline lived in out/diagex-phase1 (run on 2026-04-27); the
# Phase 1 cached run dirs sit in the global runs/ tree because the harness
# reuses the per-query cache. Filter to runs at-or-after this stamp so we
# don't pick up stale pre-eval queries.
PHASE1_SINCE = dt.datetime(2026, 4, 27, 0, 0, 0)

console = Console()
app = typer.Typer(no_args_is_help=False, add_completion=False)


@dataclass
class Phase2RunRow:
    """Slice of the `phase2_run` summary row from a results.csv."""
    run_id: str
    fixture: str
    cost_usd: float
    wall_clock_s: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int
    cache_write_tokens: int
    image_tokens: int
    n_steps: int
    n_tool_calls: int
    retries: int
    tool_call_counts_json: str
    dexpi_validates: bool
    # Equipment-F1 tp/fp/fn from the canonical row. Used to pick the run_dir
    # whose graph.json actually produced these numbers (the run_id alone is
    # ambiguous when targeted re-runs patch a fixture in place).
    equip_tp: int = -1
    equip_fp: int = -1
    equip_fn: int = -1


def _parse_run_id_ts(run_id: str) -> dt.datetime | None:
    """``20260427T144955-1dbc`` → 2026-04-27T14:49:55."""
    head = run_id.split("-", 1)[0]
    try:
        return dt.datetime.strptime(head, "%Y%m%dT%H%M%S")
    except ValueError:
        return None


def _parse_run_dir_ts(name: str) -> dt.datetime | None:
    head = name.split("_", 1)[0]
    try:
        return dt.datetime.strptime(head, "%Y-%m-%dT%H-%M-%S")
    except ValueError:
        return None


def _read_phase2_summary_rows(csv_path: Path, condition: str) -> dict[str, Phase2RunRow]:
    """Return ``{fixture: Phase2RunRow}`` from the `phase2_run` rows of a results.csv.

    Also reads the matching ``phase2_dexpi_validates`` row to populate
    ``dexpi_validates`` (the per-fixture phase2_run row stores cost/tokens but
    not the validation outcome — that's a separate metric_kind row)."""
    rows: dict[str, Phase2RunRow] = {}
    validates: dict[str, bool] = {}
    equip_prf: dict[str, tuple[int, int, int]] = {}
    if not csv_path.exists():
        return rows
    with csv_path.open() as f:
        for r in csv.DictReader(f):
            if r.get("condition") != condition:
                continue
            fixture = r.get("fixture", "")
            kind = r.get("metric_kind", "")
            if kind == "phase2_dexpi_validates":
                validates[fixture] = float(r.get("score") or 0) >= 1.0
                continue
            if kind == "phase2_equipment_f1":
                # detail = "P=0.90 R=0.90 tp=18 fp=2 fn=2"
                detail = r.get("detail", "") or ""
                tp = fp = fn = -1
                for tok in detail.split():
                    if tok.startswith("tp="):
                        tp = int(tok[3:])
                    elif tok.startswith("fp="):
                        fp = int(tok[3:])
                    elif tok.startswith("fn="):
                        fn = int(tok[3:])
                if tp >= 0 and fp >= 0 and fn >= 0:
                    equip_prf[fixture] = (tp, fp, fn)
                continue
            if kind != "phase2_run":
                continue

            def _f(k: str) -> float:
                v = r.get(k) or ""
                try:
                    return float(v)
                except ValueError:
                    return 0.0

            def _i(k: str) -> int:
                return int(_f(k))

            rows[fixture] = Phase2RunRow(
                run_id=r.get("run_id", ""),
                fixture=fixture,
                cost_usd=_f("cost_usd"),
                wall_clock_s=_f("wall_clock_s"),
                input_tokens=_i("input_tokens"),
                output_tokens=_i("output_tokens"),
                cache_read_tokens=_i("cache_read_tokens"),
                cache_write_tokens=_i("cache_write_tokens"),
                image_tokens=_i("image_tokens"),
                n_steps=_i("n_steps"),
                n_tool_calls=_i("n_tool_calls"),
                retries=_i("retries"),
                tool_call_counts_json=r.get("tool_call_counts_json") or "",
                dexpi_validates=False,  # filled below
            )
    for fix, row in rows.items():
        row.dexpi_validates = validates.get(fix, False)
        if fix in equip_prf:
            row.equip_tp, row.equip_fp, row.equip_fn = equip_prf[fix]
    return rows


def _pick_run_dir_for_fixture(
    *, runs_root: Path, fixture: str, run_id: str,
    target_prf: tuple[int, int, int] | None = None,
    truth_nodes: list | None = None,
) -> Path | None:
    """Find the ``runs_root/<fixture>/<timestamp>/`` whose timestamp best
    matches the given ``run_id``.

    The run_id (e.g. ``20260427T144955-1dbc``) marks when the harness invocation
    started; per-fixture run_dirs (e.g. ``2026-04-27T14-49-56_r-3a4b``) carry
    timestamps a few seconds later when the extractor begins. Pick the latest
    run_dir whose timestamp is ≥ the invocation start (with a small grace
    margin), falling back to the most recent dir if no match is found."""
    fix_root = runs_root / fixture
    if not fix_root.exists():
        return None

    inv_ts = _parse_run_id_ts(run_id)
    candidates: list[tuple[dt.datetime, Path]] = []
    for child in fix_root.iterdir():
        if not child.is_dir():
            continue
        ts = _parse_run_dir_ts(child.name)
        if ts is None:
            continue
        if not (child / "graph.json").exists():
            continue
        candidates.append((ts, child))
    if not candidates:
        return None
    candidates.sort(key=lambda x: x[0])

    # If we know the live equipment-F1 tp/fp/fn for this fixture, prefer the
    # graph.json whose F1 matches exactly — this picks up targeted re-runs
    # that patched results.csv without changing the row's run_id.
    if target_prf is not None and truth_nodes is not None:
        tp_t, fp_t, fn_t = target_prf
        for ts, p in reversed(candidates):  # newest first — usually patched
            try:
                g = load_predicted_graph(p / "graph.json")
            except Exception:
                continue
            prf = node_f1(truth_nodes, list(g.nodes), kind_filter={"equipment"})
            if (prf.tp, prf.fp, prf.fn) == (tp_t, fp_t, fn_t):
                return p

    if inv_ts is not None:
        # Grace of 60 seconds: invocation overhead before the per-fixture
        # extractor starts. Pick the *earliest* run_dir at-or-after the
        # invocation start — the run_id captures when *that* batch started,
        # and per-fixture run dirs are append-only, so a later dir belongs
        # to a different (later) invocation that did not produce this row.
        threshold = inv_ts - dt.timedelta(seconds=60)
        on_or_after = [(ts, p) for ts, p in candidates if ts >= threshold]
        if on_or_after:
            return on_or_after[0][1]
    return candidates[-1][1]


def _record_phase1_baseline(*, dry_run: bool) -> int:
    """Record per-fixture phase1.json cassettes for the baseline condition."""
    manifest = load_manifest(MANIFEST)
    written = 0
    for spec in manifest.fixtures:
        fixture_dir = DATASET_ROOT / spec.stem
        truth = load_fixture_truth(fixture_dir, spec)
        if not truth.queries:
            console.print(f"[yellow]skip {spec.stem}: no queries.truth.yaml[/yellow]")
            continue

        by_query_trials = _collect_runs_per_trial(
            fixture=truth, runs_root=RUNS_ROOT, since=PHASE1_SINCE,
        )

        answers: list[dict] = []
        missing: list[str] = []
        for q in truth.queries:
            # Pick trial 0 (earliest) per query so the cassette replays the
            # same answer the harness recorded as trial=0 in the live run.
            # _collect_runs_per_trial returns dirs sorted ascending by ts.
            trials = by_query_trials.get(q.id) or []
            if not trials:
                missing.append(q.id)
                continue
            run_dir = trials[0]
            result = json.loads(
                (run_dir / "result.json").read_text(encoding="utf-8")
            )
            cost = (
                json.loads((run_dir / "cost.json").read_text(encoding="utf-8"))
                if (run_dir / "cost.json").exists()
                else {}
            )
            answer_text = ""
            if result.get("answers"):
                answer_text = str(result["answers"][0].get("answer", ""))
            tcc = result.get("tool_call_counts") or {}
            answers.append({
                "query_id": q.id,
                "answer": answer_text,
                "cost_usd": float(cost.get("total_usd", 0.0)),
                "wall_clock_s": float(result.get("wall_clock_s", 0.0) or 0.0),
                "input_tokens": int(cost.get("input_tokens", 0)),
                "output_tokens": int(cost.get("output_tokens", 0)),
                "cache_read_tokens": int(cost.get("cache_read_tokens", 0)),
                "cache_write_tokens": int(cost.get("cache_write_tokens", 0)),
                "image_tokens": int(cost.get("image_tokens", 0)),
                "n_steps": len(cost.get("steps", []) or []),
                "n_tool_calls": sum(int(v or 0) for v in tcc.values()),
                "tool_call_counts": dict(tcc),
                "retries": int(result.get("retries", 0) or 0),
            })
        if missing:
            console.print(
                f"[red]baseline/{spec.stem}: missing answers for {missing}[/red]"
            )
            continue

        out = CASSETTES_ROOT / "baseline" / spec.stem
        if dry_run:
            console.print(
                f"[cyan]would write {out / 'phase1.json'} "
                f"({len(answers)} answers)[/cyan]"
            )
        else:
            out.mkdir(parents=True, exist_ok=True)
            (out / "phase1.json").write_text(
                json.dumps({"answers": answers}, indent=2)
            )
            console.print(
                f"[green]wrote {out / 'phase1.json'} ({len(answers)} answers)[/green]"
            )
        written += 1
    return written


def _record_phase2(
    *, condition: str, results_csv: Path, runs_root: Path, dry_run: bool,
) -> int:
    """Record graph.json + summary.json cassettes for a phase-2 condition."""
    manifest = load_manifest(MANIFEST)
    summary_rows = _read_phase2_summary_rows(results_csv, condition)
    if not summary_rows:
        console.print(
            f"[yellow]skip phase2/{condition}: "
            f"no phase2_run rows in {results_csv}[/yellow]"
        )
        return 0

    written = 0
    for spec in manifest.fixtures:
        if spec.stem not in summary_rows:
            continue  # condition didn't run this fixture
        srow = summary_rows[spec.stem]

        truth = load_fixture_truth(DATASET_ROOT / spec.stem, spec)
        truth_nodes_list: list = []
        if truth.graph_truth is not None:
            truth_nodes_list = list(truth.graph_truth.nodes)
        elif truth.annotations_truth:
            truth_nodes_list = list(truth.annotations_truth)

        target_prf: tuple[int, int, int] | None = None
        if srow.equip_tp >= 0:
            target_prf = (srow.equip_tp, srow.equip_fp, srow.equip_fn)

        run_dir = _pick_run_dir_for_fixture(
            runs_root=runs_root, fixture=spec.stem, run_id=srow.run_id,
            target_prf=target_prf, truth_nodes=truth_nodes_list,
        )
        if run_dir is None:
            console.print(
                f"[red]{condition}/{spec.stem}: no graph.json in {runs_root}[/red]"
            )
            continue

        out = CASSETTES_ROOT / condition / spec.stem
        graph_src = run_dir / "graph.json"
        summary_payload = {
            "cost_usd": srow.cost_usd,
            "wall_clock_s": srow.wall_clock_s,
            "dexpi_validates": srow.dexpi_validates,
            "input_tokens": srow.input_tokens,
            "output_tokens": srow.output_tokens,
            "cache_read_tokens": srow.cache_read_tokens,
            "cache_write_tokens": srow.cache_write_tokens,
            "image_tokens": srow.image_tokens,
            "n_steps": srow.n_steps,
            "n_tool_calls": srow.n_tool_calls,
            "retries": srow.retries,
            "source_run_dir": str(run_dir.relative_to(REPO)),
            "source_run_id": srow.run_id,
        }
        if dry_run:
            console.print(
                f"[cyan]would write {out}/{{graph.json,summary.json}} "
                f"← {run_dir.relative_to(REPO)}[/cyan]"
            )
        else:
            out.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(graph_src, out / "graph.json")
            (out / "summary.json").write_text(
                json.dumps(summary_payload, indent=2)
            )
            console.print(
                f"[green]wrote {out}/{{graph.json,summary.json}} "
                f"← {run_dir.relative_to(REPO)}[/green]"
            )
        written += 1
    return written


@app.command()
def main(
    conditions: list[str] = typer.Option(
        ["baseline", "ablation-no-tile"],
        "--conditions", "-c",
        help="Conditions to record. baseline records both phases; "
             "ablation-no-tile records phase 2 only.",
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
) -> None:
    total = 0
    if "baseline" in conditions:
        total += _record_phase1_baseline(dry_run=dry_run)
        total += _record_phase2(
            condition="baseline",
            results_csv=PHASE2_BASELINE_CSV,
            runs_root=PHASE2_BASELINE_RUNS,
            dry_run=dry_run,
        )
    if "ablation-no-tile" in conditions:
        total += _record_phase2(
            condition="ablation-no-tile",
            results_csv=ABLATION_CSV,
            runs_root=ABLATION_RUNS,
            dry_run=dry_run,
        )
    console.print(f"[bold]wrote {total} cassette artefact set(s)[/bold]")


if __name__ == "__main__":
    app()
