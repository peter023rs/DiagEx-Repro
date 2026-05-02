"""Targeted single-(fixture, query, trial) re-run for Phase 1 results.

Use case: a transient API failure (e.g. the 5 MiB inline-image cap that hit
``two-tanks-q2 trial=2`` on 2026-04-27) leaves one bad row in an otherwise
clean ``results.csv``. Rerunning the whole corpus to fix one row is wasteful;
this script reruns just the target query through the same Phase-1 plumbing
the harness uses, then overwrites the matching row in the CSV in place.

The CSV row schema is identical to ``run_paper_eval.py``'s output. The new
row inherits the original ``run_id`` so downstream tooling (qa_analysis,
report_md, table emitters) treats it as part of the same run.
"""

from __future__ import annotations

import csv
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
from eval.conditions import ALL_CONDITIONS  # noqa: E402
from eval.run_paper_eval import _run_phase1_query_live  # noqa: E402
from eval.scoring import score_query  # noqa: E402

console = Console()
app = typer.Typer(no_args_is_help=True, add_completion=False)


@app.command()
def main(
    fixture: str = typer.Option(..., "--fixture", help="Fixture stem, e.g. two-tanks."),
    query_id: str = typer.Option(..., "--query-id", help="e.g. two-tanks-q2."),
    trial: int = typer.Option(..., "--trial", help="Trial index to overwrite."),
    csv_path: Path = typer.Option(
        Path("out/diagex-phase1/results.csv"), "--csv",
        help="Phase-1 results.csv to patch.",
    ),
    manifest_dir: Path = typer.Option(
        Path("eval/datasets"), "--fixtures",
        help="Dataset root containing manifest.yaml.",
    ),
    pdf_root: Path = typer.Option(
        Path("tests/p-ids-public"), "--pdf-root",
    ),
    condition: str = typer.Option("baseline", "--condition"),
) -> None:
    manifest = load_manifest(manifest_dir / "manifest.yaml")
    spec = next((s for s in manifest.fixtures if s.stem == fixture), None)
    if spec is None:
        raise typer.Exit(f"fixture {fixture!r} not in manifest")
    truth = load_fixture_truth(manifest_dir / fixture, spec)
    query = next((q for q in truth.queries if q.id == query_id), None)
    if query is None:
        raise typer.Exit(f"query {query_id!r} not in truth file")

    console.print(f"[bold]rerunning[/bold] {fixture}/{query_id} trial={trial}")
    pdf_path = pdf_root / spec.pdf
    cond = ALL_CONDITIONS[condition]
    outcome, actual = _run_phase1_query_live(
        fixture=truth, query=query, condition=cond,
        pdf_path=pdf_path, console=console,
    )
    score = score_query(
        scoring=query.scoring,
        expected=query.expected_answer,
        actual=actual,
        params=query.scoring_params,
        graph=None,
        question=query.question,
    )
    console.print(
        f"  score={score.score:.3f} :: {score.detail}\n"
        f"  cost=${outcome.cost_usd:.4f} wall={outcome.wall_clock_s:.1f}s"
    )

    rows = list(csv.DictReader(csv_path.open()))
    fieldnames = list(rows[0].keys())
    matched = False
    for row in rows:
        if (
            row["fixture"] == fixture
            and row["query_id"] == query_id
            and int(row["trial"]) == trial
            and row["condition"] == condition
        ):
            row["score"] = f"{float(score.score)}"
            row["detail"] = score.detail
            row["cost_usd"] = f"{outcome.cost_usd}"
            row["input_tokens"] = str(outcome.input_tokens)
            row["output_tokens"] = str(outcome.output_tokens)
            row["cache_read_tokens"] = str(outcome.cache_read_tokens)
            row["cache_write_tokens"] = str(outcome.cache_write_tokens)
            row["image_tokens"] = str(outcome.image_tokens)
            row["wall_clock_s"] = f"{outcome.wall_clock_s}"
            row["n_steps"] = str(outcome.n_steps)
            row["n_tool_calls"] = str(outcome.n_tool_calls)
            row["retries"] = str(outcome.retries)
            row["tool_call_counts_json"] = (
                json.dumps(outcome.tool_call_counts, sort_keys=True)
                if outcome.tool_call_counts else ""
            )
            matched = True
            break
    if not matched:
        raise typer.Exit(
            f"no matching row in {csv_path} for "
            f"({fixture}, {query_id}, trial={trial}, condition={condition})"
        )

    with csv_path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)
    console.print(f"[green]patched {csv_path}[/green]")


if __name__ == "__main__":
    app()
