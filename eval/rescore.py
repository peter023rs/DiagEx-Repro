"""Re-grade an existing live run from cached ``runs/<stem>/<id>/result.json``
files, without calling the API again.

Use case: a parser bug or a scoring change is caught after a paid live pass.
The model's raw answers are already on disk under ``runs/`` (per spec §6 —
every run writes a full transcript). This script walks those, applies the
current ``eval.scoring`` parsers + scorers, and writes a fresh ``results.csv``
keyed under a new ``run_id`` (so you can σ-diff against the prior pass).

Scope: Phase 1 only. Phase 2 has its own scoring path and a different
on-disk layout; not handled here.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import typer
from rich.console import Console

_THIS = Path(__file__).resolve()
_ROOT = _THIS.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval import aggregate as agg  # noqa: E402
from eval import report_md  # noqa: E402
from eval._loader import (  # noqa: E402
    FixtureTruth,
    TruthQuery,
    load_fixture_truth,
    load_manifest,
)
from eval.scoring import (  # noqa: E402
    parse_bool_answer,
    parse_int_answer,
    parse_list_answer,
    score_query,
)

console = Console()
app = typer.Typer(no_args_is_help=False, add_completion=False)


def _coerce_actual(query: TruthQuery, answer_text: str) -> Any:
    kind = query.expected_kind.lower()
    if kind == "list":
        return parse_list_answer(answer_text)
    if kind == "integer":
        return parse_int_answer(answer_text)
    if kind == "boolean":
        return parse_bool_answer(answer_text)
    return answer_text


def _strip_format_suffix(question: str) -> str:
    """Strip harness-appended blocks (coord-frame hint, output-format suffix)
    so the bare question can be matched against truth.

    Both blocks are introduced by ``\\n\\n`` followed by a recognisable lead.
    Truncate at the earliest of those leads.
    """
    earliest = len(question)
    for marker in ("\n\nNote: page coordinates", "\n\nOutput format:"):
        i = question.find(marker)
        if i != -1 and i < earliest:
            earliest = i
    return question[:earliest].strip()


def _match_query(question: str, queries: list[TruthQuery]) -> TruthQuery | None:
    bare = _strip_format_suffix(question)
    for q in queries:
        if q.question.strip() == bare:
            return q
    # Fall back to a substring match in case of trailing whitespace differences.
    for q in queries:
        if bare.startswith(q.question.strip()) or q.question.strip().startswith(bare):
            return q
    return None


def _parse_run_ts(run_dir_name: str) -> dt.datetime | None:
    """Run dirs are named ``2026-04-25T19-01-06_r-c294``."""
    head = run_dir_name.split("_", 1)[0]
    try:
        return dt.datetime.strptime(head, "%Y-%m-%dT%H-%M-%S")
    except ValueError:
        return None


def _collect_runs(
    *, fixture: FixtureTruth, runs_root: Path, since: dt.datetime,
) -> dict[str, Path]:
    """Return ``{query_id: run_dir}`` — latest run per query at or after ``since``."""
    fix_root = runs_root / fixture.spec.stem
    if not fix_root.exists():
        return {}
    by_query: dict[str, tuple[dt.datetime, Path]] = {}
    for child in fix_root.iterdir():
        if not child.is_dir():
            continue
        ts = _parse_run_ts(child.name)
        if ts is None or ts < since:
            continue
        result_p = child / "result.json"
        if not result_p.exists():
            continue
        try:
            data = json.loads(result_p.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        question = str(data.get("question", ""))
        q = _match_query(question, list(fixture.queries))
        if q is None:
            continue
        prev = by_query.get(q.id)
        if prev is None or prev[0] < ts:
            by_query[q.id] = (ts, child)
    return {qid: p for qid, (_, p) in by_query.items()}


def _rescore_fixture(
    *, fixture: FixtureTruth, runs_root: Path, since: dt.datetime,
    run_id: str, condition: str,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    by_query = _collect_runs(fixture=fixture, runs_root=runs_root, since=since)
    for query in fixture.queries:
        run_dir = by_query.get(query.id)
        if run_dir is None:
            console.print(
                f"[yellow]skip {fixture.spec.stem}/{query.id}: no cached run found[/yellow]"
            )
            continue
        result = json.loads((run_dir / "result.json").read_text(encoding="utf-8"))
        cost = json.loads((run_dir / "cost.json").read_text(encoding="utf-8")) \
            if (run_dir / "cost.json").exists() else {}
        # Newer extractors write wall_clock_s / retries / tool_call_counts into
        # result.json; older runs lack them. Fall back to transcript.jsonl for
        # tool counts when result.json doesn't carry the breakdown.
        wall_from_result = float(result.get("wall_clock_s", 0.0) or 0.0)
        retries_from_result = int(result.get("retries", 0) or 0)
        tcc = result.get("tool_call_counts") or {}
        if not tcc:
            tpath = run_dir / "transcript.jsonl"
            if tpath.exists():
                derived: dict[str, int] = {}
                for line in tpath.read_text(encoding="utf-8").splitlines():
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("kind") == "tool_use":
                        nm = (rec.get("payload") or {}).get("name") or "unknown"
                        derived[nm] = derived.get(nm, 0) + 1
                tcc = derived
        n_tool_calls = sum(int(v or 0) for v in tcc.values())
        tool_call_counts_json = json.dumps(tcc, sort_keys=True) if tcc else ""
        answers = result.get("answers") or [{}]
        answer_text = str(answers[0].get("answer", ""))
        actual = _coerce_actual(query, answer_text)
        score = score_query(
            scoring=query.scoring,
            expected=query.expected_answer,
            actual=actual,
            params=query.scoring_params,
            graph=None,
            question=query.question,
        )
        rows.append({
            "run_id": run_id,
            "condition": condition,
            "fixture": fixture.spec.stem,
            "phase": 1,
            "metric_kind": "phase1_query",
            "family": query.family,
            "query_id": query.id,
            "scoring": query.scoring,
            "score": float(score.score),
            "detail": score.detail,
            "trial": 0,
            "cost_usd": float(cost.get("total_usd", 0.0)),
            "input_tokens": int(cost.get("input_tokens", 0)),
            "output_tokens": int(cost.get("output_tokens", 0)),
            "cache_read_tokens": int(cost.get("cache_read_tokens", 0)),
            "cache_write_tokens": int(cost.get("cache_write_tokens", 0)),
            "image_tokens": int(cost.get("image_tokens", 0)),
            "n_steps": len(cost.get("steps", []) or []),
            "n_tool_calls": n_tool_calls,
            "tool_call_counts_json": tool_call_counts_json,
            "retries": retries_from_result,
            "wall_clock_s": wall_from_result,
            "source_type": fixture.spec.source_type,
            "domain": fixture.spec.domain,
            "entity_count_truth": "",
        })
    return rows


@app.command()
def run(
    fixtures: Path = typer.Option(
        Path("eval/datasets"), "--fixtures",
        help="Dataset root containing the manifest.",
    ),
    runs_root: Path = typer.Option(
        Path("runs"), "--runs-root", help="Root of per-fixture run dirs.",
    ),
    out: Path = typer.Option(
        Path("out/diagex"), "--out", help="Output directory.",
    ),
    since: str = typer.Option(
        "", "--since",
        help="ISO datetime filter; only runs at or after this timestamp are "
             "considered. Defaults to progress.json's started_at if present, "
             "else the epoch.",
    ),
    condition: str = typer.Option(
        "baseline", "--condition", help="Condition label for the new rows.",
    ),
    only: str = typer.Option(
        "", "--only", help="Comma-separated fixture stems to restrict to.",
    ),
) -> None:
    manifest_path = fixtures / "manifest.yaml"
    manifest = load_manifest(manifest_path)

    if since:
        since_dt = dt.datetime.fromisoformat(since)
    else:
        prog = out / "progress.json"
        if prog.exists():
            since_dt = dt.datetime.fromisoformat(
                json.loads(prog.read_text(encoding="utf-8"))["started_at"]
            )
            console.print(f"[dim]using --since={since_dt.isoformat()} from {prog}[/dim]")
        else:
            since_dt = dt.datetime.fromtimestamp(0)

    only_set = {s.strip() for s in only.split(",") if s.strip()}
    rows: list[dict[str, Any]] = []
    run_id = dt.datetime.now().strftime("%Y%m%dT%H%M%S") + "-rescore"
    for spec in manifest.fixtures:
        if only_set and spec.stem not in only_set:
            continue
        fixture_dir = fixtures / spec.stem
        truth = load_fixture_truth(fixture_dir, spec)
        rows.extend(_rescore_fixture(
            fixture=truth, runs_root=runs_root, since=since_dt,
            run_id=run_id, condition=condition,
        ))

    if not rows:
        console.print("[red]no rescorable runs found[/red]")
        raise typer.Exit(1)

    df = pd.DataFrame(rows)
    csv_path = out / "results.csv"
    if csv_path.exists():
        out_prev = out / "results.prev.csv"
        out_prev.write_bytes(csv_path.read_bytes())
    agg.write_results(df, csv_path)
    df_prev = pd.read_csv(out / "results.prev.csv") if (out / "results.prev.csv").exists() else None
    report_md.write_report(
        out / "report.md",
        df_curr=df, df_prev=df_prev,
        run_id=run_id, invocation=" ".join(sys.argv),
    )
    console.print(f"[green]rescored {len(rows)} rows → {csv_path}[/green]")
    console.print(f"[green]report → {out / 'report.md'}[/green]")


if __name__ == "__main__":
    app()
