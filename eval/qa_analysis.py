"""Per-(fixture, query) debug spreadsheet for Phase 1.

Walks the cached ``runs/<stem>/<id>/result.json`` files (same source as
``eval/rescore.py``), joins them against the truth file, and emits an Excel
workbook with one row per query containing:

  fixture | query_id | family | scoring | question | expected | recorded |
  parsed_actual | score | detail | analysis

The ``analysis`` column tries to give a one-line root-cause hypothesis for
deviations. It is heuristic — meant to seed manual review, not replace it.
"""

from __future__ import annotations

import datetime as dt
import json
import sys
from pathlib import Path
from typing import Any

import pandas as pd
import typer
from openpyxl.styles import Alignment, Font, PatternFill
from rich.console import Console

_THIS = Path(__file__).resolve()
_ROOT = _THIS.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval._loader import (  # noqa: E402
    FixtureTruth,
    TruthQuery,
    load_fixture_truth,
    load_manifest,
)
from eval.rescore import (  # noqa: E402
    _coerce_actual,
    _match_query,
    _parse_run_ts,
)
from eval.scoring import score_query  # noqa: E402


def _is_error_run(data: dict[str, Any]) -> bool:
    """An extractor failure leaves the answer prefixed with
    ``error during extraction:``. Treat such runs as if they didn't exist
    so a later targeted rerun (``scripts/rerun_one_query.py``) takes their
    trial slot in timestamp ordering."""
    answers = data.get("answers") or [{}]
    raw = str(answers[0].get("answer", ""))
    return raw.startswith("error during extraction:")


def _collect_runs_per_trial(
    *, fixture: FixtureTruth, runs_root: Path, since: dt.datetime,
) -> dict[str, list[Path]]:
    """Return ``{query_id: [run_dirs sorted by timestamp ascending]}``.

    The eval harness runs trials sequentially per (fixture, query) — see
    ``eval/run_paper_eval.py``'s ``for trial in range(...)`` loop nested
    inside the per-query loop. Within a single fixture, run-dir timestamps
    therefore line up with trial indices: index 0 = trial 0, etc.

    Run dirs whose ``result.json`` carries an extractor-error answer are
    dropped so a later targeted rerun cleanly takes the failed trial's slot.
    """
    fix_root = runs_root / fixture.spec.stem
    if not fix_root.exists():
        return {}
    by_query: dict[str, list[tuple[dt.datetime, Path]]] = {}
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
        if _is_error_run(data):
            continue
        question = str(data.get("question", ""))
        q = _match_query(question, list(fixture.queries))
        if q is None:
            continue
        by_query.setdefault(q.id, []).append((ts, child))
    return {
        qid: [p for _, p in sorted(items, key=lambda x: x[0])]
        for qid, items in by_query.items()
    }

console = Console()
app = typer.Typer(no_args_is_help=False, add_completion=False)


# ---------------------------------------------------------------------------
# Heuristic analysis: per-row root-cause hypothesis
# ---------------------------------------------------------------------------


def _norm_simple(s: str) -> str:
    return "".join(ch for ch in s.lower() if ch.isalnum())


def _set_match_analysis(query: TruthQuery, parsed: list[str], score: float) -> str:
    expected = list(query.expected_answer)
    if score >= 1.0:
        return "match"
    exp_norm = {_norm_simple(t): t for t in expected}
    pred_norm_to_raw: dict[str, str] = {}
    for raw in parsed:
        pred_norm_to_raw.setdefault(_norm_simple(raw), raw)
    matched_keys = set(exp_norm) & set(pred_norm_to_raw)
    missed = [exp_norm[k] for k in exp_norm if k not in matched_keys]
    extra = [pred_norm_to_raw[k] for k in pred_norm_to_raw
             if k and k not in exp_norm]
    parts: list[str] = []
    if score == 0.0:
        parts.append("zero overlap")
    else:
        parts.append("partial match")
    if missed:
        parts.append(f"missed: {', '.join(missed[:5])}")
    if extra:
        parts.append(f"extra: {', '.join(extra[:5])}")
    if score == 0.0 and missed and extra:
        parts.append("model may use a different tag scheme; "
                     "verify normalization and prompt phrasing")
    return " · ".join(parts)


def _numeric_analysis(query: TruthQuery, parsed: Any, score: float) -> str:
    if score >= 1.0:
        return "match"
    truth = float(query.expected_answer)
    if parsed is None:
        return "parser returned None — answer text contained no integer"
    pred = float(parsed)
    diff = pred - truth
    rel = abs(diff) / abs(truth) if truth else float("inf")
    tol = float((query.scoring_params or {}).get("tolerance_frac", 0.05))
    if abs(diff) == 1:
        return (f"off-by-one (truth={truth:g} pred={pred:g}); model may "
                f"double-count or miss one item — open the run's answer.md "
                f"and check what was enumerated")
    if rel <= tol * 1.5:
        return (f"near-miss vs {tol:.0%} tolerance (rel_err={rel:.1%}); "
                f"either bump tolerance or re-author truth")
    if pred < 0:
        return (f"negative count (pred={pred:g}); likely parser still mis-"
                f"reading a hyphen — verify parse_int_answer guard")
    if pred > 100 and truth < 100:
        return (f"large overcount (pred={pred:g} vs truth={truth:g}); "
                f"first-int regex may have grabbed a tag-internal digit run "
                f"like H1007 — check answer text")
    return (f"substantive disagreement (truth={truth:g} pred={pred:g}, "
            f"rel_err={rel:.1%}); not a parser issue")


def _bool_analysis(query: TruthQuery, parsed: Any, score: float, raw: str) -> str:
    if score >= 1.0:
        return "match"
    if parsed is None:
        return ("parser returned None — answer didn't start or end with "
                "yes/no; inspect the raw answer for a buried verdict")
    truth = bool(query.expected_answer)
    pred = bool(parsed)
    if truth != pred:
        return (f"substantive disagreement: truth={truth} pred={pred}; "
                f"either model genuinely traces (or doesn't trace) the path, "
                f"or endpoint labels in the question don't match graph nodes")
    return "match"


def _contains_analysis(query: TruthQuery, raw: str, score: float) -> str:
    if score >= 1.0:
        return "match"
    needle = str(query.expected_answer).lower()
    haystack = raw.lower()
    if "none" in haystack or "blank" in haystack or "no equipment" in haystack:
        return ("model says no equipment at the truth coordinates; either "
                "truth coords don't fall on the symbol (re-author q4) or "
                "model is missing the symbol — open the diagram and verify")
    if needle in haystack[:200]:
        return ("expected term appears in answer but somewhere outside the "
                "matched window — likely fine; consider broadening scoring "
                "or shortening answer")
    return (f"model returned different equipment kind: "
            f"answer={raw[:120]!r}... — substantive disagreement, not parser")


def _row_analysis(
    *, query: TruthQuery, parsed: Any, raw_answer: str, score: float,
) -> str:
    kind = query.scoring
    if kind == "set_match":
        return _set_match_analysis(query, parsed if isinstance(parsed, list) else [], score)
    if kind == "numeric_tolerance":
        return _numeric_analysis(query, parsed, score)
    if kind == "graph_reachability":
        return _bool_analysis(query, parsed, score, raw_answer)
    if kind == "contains":
        return _contains_analysis(query, raw_answer, score)
    if kind == "exact":
        return "match" if score >= 1.0 else "exact-match failure"
    return ""


# ---------------------------------------------------------------------------
# Workbook assembly
# ---------------------------------------------------------------------------


def _truncate(s: str, n: int) -> str:
    return s if len(s) <= n else s[: n - 1] + "…"


def _build_rows(
    *, manifest_dir: Path, runs_root: Path, since: dt.datetime,
    only: set[str],
) -> list[dict[str, Any]]:
    manifest = load_manifest(manifest_dir / "manifest.yaml")
    out_rows: list[dict[str, Any]] = []
    for spec in manifest.fixtures:
        if only and spec.stem not in only:
            continue
        truth = load_fixture_truth(manifest_dir / spec.stem, spec)
        by_query = _collect_runs_per_trial(
            fixture=truth, runs_root=runs_root, since=since,
        )
        for q in truth.queries:
            run_dirs = by_query.get(q.id) or []
            if not run_dirs:
                out_rows.append({
                    "fixture": spec.stem, "query_id": q.id, "trial": "",
                    "family": q.family, "scoring": q.scoring,
                    "question": q.question,
                    "expected": _format_expected(q),
                    "recorded": "(no cached run)", "parsed_actual": "",
                    "score": float("nan"), "detail": "",
                    "analysis": "no run dir matched — re-run live or "
                                "widen --since",
                })
                continue
            for trial_idx, run_dir in enumerate(run_dirs):
                data = json.loads(
                    (run_dir / "result.json").read_text(encoding="utf-8")
                )
                answers = data.get("answers") or [{}]
                raw = str(answers[0].get("answer", ""))
                parsed = _coerce_actual(q, raw)
                score = score_query(
                    scoring=q.scoring, expected=q.expected_answer,
                    actual=parsed, params=q.scoring_params,
                    graph=None, question=q.question,
                )
                analysis = _row_analysis(
                    query=q, parsed=parsed, raw_answer=raw, score=score.score,
                )
                out_rows.append({
                    "fixture": spec.stem, "query_id": q.id,
                    "trial": trial_idx,
                    "family": q.family, "scoring": q.scoring,
                    "question": q.question,
                    "expected": _format_expected(q),
                    "recorded": _truncate(raw.strip(), 1500),
                    "parsed_actual": _format_parsed(parsed),
                    "score": float(score.score), "detail": score.detail,
                    "analysis": analysis,
                })
    return out_rows


def _format_expected(q: TruthQuery) -> str:
    e = q.expected_answer
    if isinstance(e, list):
        return ", ".join(str(x) for x in e)
    return str(e)


def _format_parsed(parsed: Any) -> str:
    if parsed is None:
        return "(None)"
    if isinstance(parsed, list):
        return _truncate(", ".join(str(x) for x in parsed), 400)
    return _truncate(str(parsed), 400)


def _write_excel(rows: list[dict[str, Any]], out_path: Path) -> None:
    columns = [
        "fixture", "query_id", "trial", "family", "scoring", "question",
        "expected", "recorded", "parsed_actual", "score", "detail", "analysis",
    ]
    df = pd.DataFrame(rows, columns=columns)
    score_col_idx = columns.index("score") + 1  # 1-based for openpyxl
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with pd.ExcelWriter(out_path, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="phase1_qa")
        ws = writer.sheets["phase1_qa"]

        widths = {
            "A": 18, "B": 22, "C": 6, "D": 15, "E": 20, "F": 60,
            "G": 35, "H": 80, "I": 35, "J": 8, "K": 40, "L": 70,
        }
        for col, w in widths.items():
            ws.column_dimensions[col].width = w

        wrap = Alignment(wrap_text=True, vertical="top")
        header_font = Font(bold=True)
        red = PatternFill("solid", fgColor="FFE0E0")
        amber = PatternFill("solid", fgColor="FFF2CC")
        green = PatternFill("solid", fgColor="E2EFDA")

        for cell in ws[1]:
            cell.font = header_font
            cell.alignment = Alignment(wrap_text=True, vertical="top")

        for row_idx in range(2, ws.max_row + 1):
            score_cell = ws.cell(row=row_idx, column=score_col_idx)
            try:
                s = float(score_cell.value)
            except (TypeError, ValueError):
                s = float("nan")
            fill = green if s >= 0.999 else (amber if s > 0.0 else red)
            for col_idx in range(1, ws.max_column + 1):
                c = ws.cell(row=row_idx, column=col_idx)
                c.alignment = wrap
                c.fill = fill

        ws.freeze_panes = "A2"


@app.command()
def run(
    fixtures: Path = typer.Option(Path("eval/datasets"), "--fixtures"),
    runs_root: Path = typer.Option(Path("runs"), "--runs-root"),
    out: Path = typer.Option(
        Path("out/diagex/qa_analysis.xlsx"), "--out",
        help="Excel output path.",
    ),
    since: str = typer.Option(
        "", "--since",
        help="ISO datetime cutoff. Defaults to progress.json/started_at.",
    ),
    only: str = typer.Option("", "--only",
                             help="Comma-separated fixture stems."),
) -> None:
    if since:
        since_dt = dt.datetime.fromisoformat(since)
    else:
        prog = Path("out/diagex/progress.json")
        if prog.exists():
            since_dt = dt.datetime.fromisoformat(
                json.loads(prog.read_text(encoding="utf-8"))["started_at"]
            )
            console.print(f"[dim]using --since={since_dt.isoformat()} from {prog}[/dim]")
        else:
            since_dt = dt.datetime.fromtimestamp(0)
    only_set = {s.strip() for s in only.split(",") if s.strip()}
    rows = _build_rows(
        manifest_dir=fixtures, runs_root=runs_root,
        since=since_dt, only=only_set,
    )
    _write_excel(rows, out)
    console.print(f"[green]wrote {len(rows)} rows → {out}[/green]")


if __name__ == "__main__":
    app()
