"""Re-score the existing N=3 Phase-1 ``results.csv`` in place after a
parser/scorer change, without re-running the API.

Pulls each row's cached ``runs/<stem>/<id>/result.json`` via the same
timestamp-ordered mapping ``qa_analysis._collect_runs_per_trial`` uses, so
``trial=k`` maps to the k-th surviving (non-error) run dir for the query.
Only ``score`` and ``detail`` are mutated — cost, tokens, wall-clock, tool
counts are left untouched.
"""

from __future__ import annotations

import csv
import datetime as dt
import json
import sys
from pathlib import Path

import typer
from rich.console import Console

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval._loader import load_fixture_truth, load_manifest  # noqa: E402
from eval.qa_analysis import _collect_runs_per_trial  # noqa: E402
from eval.rescore import _coerce_actual  # noqa: E402
from eval.scoring import score_query  # noqa: E402

console = Console()
app = typer.Typer(no_args_is_help=False, add_completion=False)


@app.command()
def main(
    csv_path: Path = typer.Option(
        Path("out/diagex-phase1/results.csv"), "--csv",
    ),
    manifest_dir: Path = typer.Option(
        Path("eval/datasets"), "--fixtures",
    ),
    runs_root: Path = typer.Option(Path("runs"), "--runs-root"),
    progress_path: Path = typer.Option(
        Path("out/diagex-phase1/progress.json"), "--progress",
        help="Source for the --since cutoff timestamp.",
    ),
) -> None:
    since = dt.datetime.fromisoformat(
        json.loads(progress_path.read_text(encoding="utf-8"))["started_at"]
    )
    console.print(f"[dim]since={since.isoformat()}[/dim]")

    manifest = load_manifest(manifest_dir / "manifest.yaml")
    truths = {s.stem: load_fixture_truth(manifest_dir / s.stem, s)
              for s in manifest.fixtures}
    runs_per_query: dict[tuple[str, str], list[Path]] = {}
    for stem, truth in truths.items():
        for qid, dirs in _collect_runs_per_trial(
            fixture=truth, runs_root=runs_root, since=since,
        ).items():
            runs_per_query[(stem, qid)] = dirs

    rows = list(csv.DictReader(csv_path.open()))
    fieldnames = list(rows[0].keys())
    changed = 0
    missing = 0
    for row in rows:
        if row.get("phase") != "1" and row.get("metric_kind") != "phase1_query":
            continue
        truth = truths.get(row["fixture"])
        if truth is None:
            continue
        query = next(
            (q for q in truth.queries if q.id == row["query_id"]), None,
        )
        if query is None:
            continue
        dirs = runs_per_query.get((row["fixture"], row["query_id"]), [])
        trial_idx = int(row["trial"])
        if trial_idx >= len(dirs):
            missing += 1
            console.print(
                f"[yellow]missing run dir for "
                f"{row['fixture']}/{row['query_id']} trial={trial_idx}[/yellow]"
            )
            continue
        run_dir = dirs[trial_idx]
        data = json.loads(
            (run_dir / "result.json").read_text(encoding="utf-8"),
        )
        raw = str((data.get("answers") or [{}])[0].get("answer", ""))
        actual = _coerce_actual(query, raw)
        score = score_query(
            scoring=query.scoring, expected=query.expected_answer,
            actual=actual, params=query.scoring_params,
            graph=None, question=query.question,
        )
        new_score = f"{float(score.score)}"
        new_detail = score.detail
        if row["score"] != new_score or row["detail"] != new_detail:
            row["score"] = new_score
            row["detail"] = new_detail
            changed += 1

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    console.print(
        f"[green]rescored {changed} row(s); "
        f"{missing} missing; total {len(rows)} → {csv_path}[/green]"
    )


if __name__ == "__main__":
    app()
