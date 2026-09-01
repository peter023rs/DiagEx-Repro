"""diagex evaluation driver — plan §7.

Reproduces every table and figure in the paper from a single command:

    python eval/run_paper_eval.py \\
        --fixtures eval/datasets/ \\
        --phase both \\
        --conditions baseline,ablation-no-tile \\
        --parallel 4 \\
        --out out/diagex/ \\
        --emit tables,figures,artifacts \\
        --use-cassettes

Live mode invokes ``diagex.extractors.query.run_query`` and
``diagex.extractors.pid.run_pid_extract``. Cassette mode reads pre-canned
per-(condition, fixture) artefacts from ``--cassettes-dir`` so the harness
can be exercised end-to-end without API spend (plan step 10's exit
criterion).

The driver is the only place that owns:

* fixture × condition × replicate enumeration
* per-condition ``Config`` mutation
* ``results.csv`` writing (the single source of truth)
* invocation logging (``out/diagex/invocation.txt``)
* aggregate / table / figure / report orchestration

Per spec §7.1, every Phase 1 query is logged with cost and latency; per
spec §7.2 every Phase 2 fixture is logged with stats and validation. The
``results.csv`` schema is documented in ``eval/aggregate.py``.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import secrets
import shutil
import sys
import threading
import time
from concurrent.futures import Future, ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import pandas as pd
import typer
from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    SpinnerColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)

# Make sibling imports work when invoked as a script.
_THIS = Path(__file__).resolve()
_ROOT = _THIS.parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval import aggregate as agg  # noqa: E402  (sys.path patched above)
from eval import latex_tables, report_md  # noqa: E402
from eval._loader import (  # noqa: E402
    FixtureTruth,
    Manifest,
    Phase1Cassette,
    Phase2Cassette,
    TruthQuery,
    load_fixture_truth,
    load_manifest,
    load_phase1_cassette,
    load_phase2_cassette,
)
from eval.conditions import (  # noqa: E402
    Condition,
    apply_config_overrides,
    resolve_conditions,
)
from eval.scoring import (  # noqa: E402
    ScoreResult,
    coord_frame_hint,
    edge_f1,
    format_suffix,
    needs_coord_frame_hint,
    node_f1,
    parse_bool_answer,
    parse_int_answer,
    parse_list_answer,
    score_query,
    tag_ocr_exact_match,
)

app = typer.Typer(
    name="run_paper_eval",
    help="diagex evaluation driver (plan §7).",
    no_args_is_help=False,
    add_completion=False,
)
console = Console()


# ---------------------------------------------------------------------------
# Run id / invocation logging
# ---------------------------------------------------------------------------


def _new_run_id() -> str:
    return dt.datetime.now().strftime("%Y%m%dT%H%M%S") + "-" + secrets.token_hex(2)


def _write_invocation(out_dir: Path, *, argv: list[str], run_id: str) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    p = out_dir / "invocation.txt"
    payload = {
        "run_id": run_id,
        "ts": dt.datetime.now().isoformat(timespec="seconds"),
        "argv": argv,
        "model_env": os.environ.get("DIAGEX_MODEL", "claude-opus-4-7"),
    }
    p.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return p


# ---------------------------------------------------------------------------
# Intermediate persistence: results.csv + progress.json + report.md
#
# Persisted after every completed (condition, fixture, phase) cell so a long
# run is observable mid-flight and crash-safe. The atomic-rename pattern keeps
# downstream readers (the operator's `watch -n 2 wc -l results.csv`, IDE
# previews, ...) from ever seeing a half-written file.
# ---------------------------------------------------------------------------


# argv flags that change the planned job set or the meaning of cells already
# computed. Resume refuses to mix old and new rows when any of these differ.
_RESUME_GATED_FLAGS = (
    "--conditions", "--phase", "--only", "--n-replicates", "--use-cassettes",
)


def _atomic_write_csv(df: pd.DataFrame, csv_path: Path) -> None:
    """Atomically rewrite results.csv via tmp+rename, preserving column order."""
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = df.reindex(columns=agg.RESULTS_COLUMNS)
    tmp = csv_path.with_suffix(csv_path.suffix + ".tmp")
    df.to_csv(tmp, index=False)
    os.replace(tmp, csv_path)


def _write_progress_json(out_dir: Path, state: dict[str, Any]) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    tmp = out_dir / "progress.json.tmp"
    tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
    os.replace(tmp, out_dir / "progress.json")


def _persist_tick(
    *, out_dir: Path, df: pd.DataFrame, progress_state: dict[str, Any],
) -> None:
    """Atomic CSV write + progress.json after each completed cell.

    report.md regeneration is deliberately deferred to the final pass — it
    runs full pandas aggregations and the operator already has results.csv
    and progress.json for live observability.
    """
    csv_path = out_dir / "results.csv"
    _atomic_write_csv(df, csv_path)

    state = dict(progress_state)
    state["last_update"] = dt.datetime.now().isoformat(timespec="seconds")
    state["elapsed_s"] = round(time.time() - state["_started_monotonic"], 1)
    persisted = {k: v for k, v in state.items() if not k.startswith("_")}
    _write_progress_json(out_dir, persisted)


def _is_billable_row(row: dict[str, Any]) -> bool:
    """Phase-2 metric rows carry score-only data with cost=0; they would
    double-count if summed alongside ``phase2_run`` rows."""
    return not (row.get("phase") == 2 and row.get("metric_kind") != "phase2_run")


def _load_progress(out_dir: Path) -> dict[str, Any] | None:
    p = out_dir / "progress.json"
    if not p.exists():
        return None
    try:
        return json.loads(p.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError):
        return None


def _extract_gated_argv(argv: list[str]) -> dict[str, str]:
    """Pull the subset of argv that must match between original and resume.

    Tolerates both ``--flag value`` and ``--flag=value`` forms. Boolean flags
    map to ``"<set>"``.
    """
    out: dict[str, str] = {}
    i = 0
    while i < len(argv):
        tok = argv[i]
        for flag in _RESUME_GATED_FLAGS:
            if tok == flag:
                if i + 1 < len(argv) and not argv[i + 1].startswith("--"):
                    out[flag] = argv[i + 1]
                    i += 1
                else:
                    out[flag] = "<set>"
                break
            if tok.startswith(flag + "="):
                out[flag] = tok[len(flag) + 1:]
                break
        i += 1
    return out


def _check_resume_compatibility(
    prior_argv: list[str], curr_argv: list[str],
) -> list[str]:
    """Return a list of human-readable mismatches; empty list = compatible."""
    prior = _extract_gated_argv(prior_argv)
    curr = _extract_gated_argv(curr_argv)
    diffs: list[str] = []
    for flag in _RESUME_GATED_FLAGS:
        a, b = prior.get(flag), curr.get(flag)
        if a != b:
            diffs.append(f"  {flag}: prior={a!r}  current={b!r}")
    return diffs


def _done_cells_from_csv(csv_path: Path) -> tuple[set[tuple[str, str, int]], pd.DataFrame]:
    """Read prior results.csv. Returns (done_cells, df).

    A cell is ``(condition, fixture, phase_int)``. Membership = "this cell has
    at least one row in the CSV"; we don't try to validate row counts.
    """
    if not csv_path.exists():
        return set(), pd.DataFrame(columns=agg.RESULTS_COLUMNS)
    df = pd.read_csv(csv_path)
    keyed = df[["condition", "fixture", "phase"]].dropna()
    done = set(zip(
        keyed["condition"].astype(str),
        keyed["fixture"].astype(str),
        keyed["phase"].astype(int),
    ))
    return done, df


# ---------------------------------------------------------------------------
# Phase 1 — per-query scoring
# ---------------------------------------------------------------------------


@dataclass
class QueryRunOutcome:
    answer: str
    cost_usd: float
    wall_clock_s: float
    input_tokens: int
    output_tokens: int
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    image_tokens: int = 0
    n_steps: int = 0
    n_tool_calls: int = 0
    retries: int = 0
    tool_call_counts: dict[str, int] = field(default_factory=dict)


def _coerce_actual_for_scoring(query: TruthQuery, answer_text: str) -> Any:
    """Turn a free-text Phase-1 answer into the type the scorer expects."""
    kind = query.expected_kind.lower()
    if kind == "list":
        return parse_list_answer(answer_text)
    if kind == "integer":
        return parse_int_answer(answer_text)
    if kind == "boolean":
        return parse_bool_answer(answer_text)
    return answer_text  # 'string' falls through


def _run_phase1_query_live(
    *, fixture: FixtureTruth, query: TruthQuery, condition: Condition,
    pdf_path: Path, console: Console,
) -> tuple[QueryRunOutcome, Any]:
    """Run a single query against the live extractor. Imports are deferred
    because the extractor pulls in pymupdf/anthropic — we don't want to load
    those in cassette-only mode."""
    from diagex.config import load_config
    from diagex.extractors.query import run_query

    cfg = load_config()
    apply_config_overrides(cfg, condition.config_overrides)
    qkw = dict(condition.query_kwargs)

    parts: list[str] = [query.question]
    if needs_coord_frame_hint(query.question):
        parts.append(coord_frame_hint(fixture.spec.page_size_pts))
    suffix = format_suffix(query.expected_kind)
    if suffix:
        parts.append(suffix)
    question = "\n\n".join(parts)

    backend = qkw.pop("backend", None)
    if backend == "gpt41-singleshot":
        return _run_phase1_query_gpt41(
            query=query, pdf_path=pdf_path, question_text=question,
        )

    start = time.perf_counter()
    result = run_query(
        diagram=pdf_path,
        question=question,
        page_spec=qkw.pop("page_spec", "1"),
        effort=qkw.pop("effort", "high"),
        config=cfg,
        persist=True,
        console=console,
    )
    wall = time.perf_counter() - start

    answer_text = result.answers[0].answer if result.answers else ""
    cs = result.cost_summary
    # Prefer the extractor's wall_clock (it brackets the actual run, including
    # the persistence step); fall back to the harness's outer measurement.
    extractor_wall = float(cs.get("wall_clock_s", 0.0) or 0.0)
    outcome = QueryRunOutcome(
        answer=answer_text,
        cost_usd=float(cs.get("total_usd", 0.0)),
        wall_clock_s=extractor_wall if extractor_wall > 0 else wall,
        input_tokens=int(cs.get("input_tokens", 0)),
        output_tokens=int(cs.get("output_tokens", 0)),
        cache_read_tokens=int(cs.get("cache_read_tokens", 0)),
        cache_write_tokens=int(cs.get("cache_write_tokens", 0)),
        image_tokens=int(cs.get("image_tokens", 0)),
        n_steps=len(cs.get("steps", []) or []),
        n_tool_calls=int(cs.get("n_tool_calls", 0)),
        retries=int(cs.get("retries", 0)),
        tool_call_counts=dict(cs.get("tool_call_counts") or {}),
    )
    actual = _coerce_actual_for_scoring(query, answer_text)
    return outcome, actual


def _run_phase1_query_gpt41(
    *, query: TruthQuery, pdf_path: Path, question_text: str,
) -> tuple[QueryRunOutcome, Any]:
    """GPT-4.1 single-shot Phase 1 (plan §6 item 2). One chat-completions
    call, no tools, no ReAct. Lives in `eval/gpt_singleshot.py`."""
    from eval.gpt_singleshot import run_singleshot

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF missing: {pdf_path}")

    out = run_singleshot(pdf_path=pdf_path, question_text=question_text)
    outcome = QueryRunOutcome(
        answer=out.answer,
        cost_usd=out.cost_usd,
        wall_clock_s=out.wall_clock_s,
        input_tokens=out.input_tokens,
        output_tokens=out.output_tokens,
        cache_read_tokens=out.cached_input_tokens,
        cache_write_tokens=0,
        image_tokens=out.image_tokens,
        n_steps=1,
        n_tool_calls=0,
        retries=0,
        tool_call_counts={},
    )
    actual = _coerce_actual_for_scoring(query, out.answer)
    return outcome, actual


def _run_phase1_query_cassette(
    *, query: TruthQuery, cassette: Phase1Cassette,
) -> tuple[QueryRunOutcome, Any]:
    item = cassette.answers_by_query.get(query.id)
    if item is None:
        outcome = QueryRunOutcome("", 0.0, 0.0, 0, 0)
        return outcome, _coerce_actual_for_scoring(query, "")
    answer_text = str(item.get("answer", ""))
    outcome = QueryRunOutcome(
        answer=answer_text,
        cost_usd=float(item.get("cost_usd", 0.0)),
        wall_clock_s=float(item.get("wall_clock_s", 0.0)),
        input_tokens=int(item.get("input_tokens", 0)),
        output_tokens=int(item.get("output_tokens", 0)),
        cache_read_tokens=int(item.get("cache_read_tokens", 0)),
        cache_write_tokens=int(item.get("cache_write_tokens", 0)),
        image_tokens=int(item.get("image_tokens", 0)),
        n_steps=int(item.get("n_steps", 0)),
        n_tool_calls=int(item.get("n_tool_calls", 0)),
        retries=int(item.get("retries", 0)),
        tool_call_counts=dict(item.get("tool_call_counts") or {}),
    )
    # Cassette can override the parsed actual (useful when the canned answer
    # is, e.g., a list and the parser wouldn't recover it).
    if "actual" in item:
        actual = item["actual"]
    else:
        actual = _coerce_actual_for_scoring(query, answer_text)
    return outcome, actual


# ---------------------------------------------------------------------------
# Phase 2 — per-fixture extraction + scoring
# ---------------------------------------------------------------------------


@dataclass
class Phase2Outcome:
    graph_path: Path | None
    cost_usd: float
    wall_clock_s: float
    input_tokens: int
    output_tokens: int
    dexpi_validates: bool
    cache_read_tokens: int = 0
    cache_write_tokens: int = 0
    image_tokens: int = 0
    n_steps: int = 0
    n_tool_calls: int = 0
    retries: int = 0
    tool_call_counts: dict[str, int] = field(default_factory=dict)


def _run_phase2_live(
    *, fixture: FixtureTruth, condition: Condition,
    pdf_path: Path, run_dir_root: Path, console: Console,
) -> tuple[Phase2Outcome, Any]:
    from diagex.config import load_config
    from diagex.extractors.pid import run_pid_extract

    cfg = load_config()
    apply_config_overrides(cfg, condition.config_overrides)
    cfg.runs_dir = run_dir_root
    pkw = dict(condition.pid_kwargs)

    start = time.perf_counter()
    result = run_pid_extract(
        diagram=pdf_path,
        symbol_standard=pkw.pop("symbol_standard", "isa-5.1"),
        no_legend=bool(pkw.pop("no_legend", False)),
        effort=pkw.pop("effort", "xhigh"),
        engine=pkw.pop("engine", None),
        config=cfg,
        persist=True,
        console=console,
    )
    wall = time.perf_counter() - start

    graph_path = (result.run_dir / "graph.json") if result.run_dir else None
    cs = result.cost_summary
    extractor_wall = float(cs.get("wall_clock_s", 0.0) or 0.0)
    outcome = Phase2Outcome(
        graph_path=graph_path,
        cost_usd=float(cs.get("total_usd", 0.0)),
        wall_clock_s=extractor_wall if extractor_wall > 0 else wall,
        input_tokens=int(cs.get("input_tokens", 0)),
        output_tokens=int(cs.get("output_tokens", 0)),
        dexpi_validates=(
            not bool(result.validation_issues)
            and result.quality_status not in {"error"}
        ),
        cache_read_tokens=int(cs.get("cache_read_tokens", 0)),
        cache_write_tokens=int(cs.get("cache_write_tokens", 0)),
        image_tokens=int(cs.get("image_tokens", 0)),
        n_steps=len(cs.get("steps", []) or []),
        n_tool_calls=int(cs.get("n_tool_calls", 0)),
        retries=int(cs.get("retries", 0)),
        tool_call_counts=dict(cs.get("tool_call_counts") or {}),
    )
    return outcome, result.graph


def _run_phase2_cassette(*, cassette: Phase2Cassette) -> tuple[Phase2Outcome, Any]:
    outcome = Phase2Outcome(
        graph_path=None,
        cost_usd=cassette.cost_usd,
        wall_clock_s=cassette.wall_clock_s,
        input_tokens=cassette.input_tokens,
        output_tokens=cassette.output_tokens,
        dexpi_validates=cassette.dexpi_validates,
        cache_read_tokens=int(getattr(cassette, "cache_read_tokens", 0) or 0),
        cache_write_tokens=int(getattr(cassette, "cache_write_tokens", 0) or 0),
        image_tokens=int(getattr(cassette, "image_tokens", 0) or 0),
        n_steps=int(getattr(cassette, "n_steps", 0) or 0),
        n_tool_calls=int(getattr(cassette, "n_tool_calls", 0) or 0),
        retries=int(getattr(cassette, "retries", 0) or 0),
    )
    return outcome, cassette.graph


# ---------------------------------------------------------------------------
# Per-fixture orchestration
# ---------------------------------------------------------------------------


@dataclass
class HarnessConfig:
    out_dir: Path
    cassettes_dir: Path | None
    use_cassettes: bool
    parallel: int
    n_replicates: int
    fixtures_filter: tuple[str, ...] | None
    dataset_root: Path
    pdf_root: Path
    emit_tables: bool
    emit_figures: bool
    emit_artifacts: bool
    # When --use-cassettes is on but a (condition, fixture) cassette is
    # missing, the default behaviour is to ERROR. Set this to True to fall
    # back to live API calls for the missing cells (rarely what you want;
    # opting in is an explicit acknowledgement of API spend).
    allow_live_fallback: bool = False


class CassetteMissingError(RuntimeError):
    """Raised when --use-cassettes is on and a required cassette file is absent.

    Surfaces the path so the operator knows where to drop the cassette. Does
    not auto-fall-back to live, which would silently spend API budget.
    """


def _resolve_cassette_phase1(
    cfg: HarnessConfig, *, condition: str, fixture: str,
) -> Phase1Cassette | None:
    if not cfg.use_cassettes or cfg.cassettes_dir is None:
        return None
    p = cfg.cassettes_dir / condition / fixture / "phase1.json"
    if not p.exists():
        if cfg.allow_live_fallback:
            return None
        raise CassetteMissingError(
            f"phase1 cassette missing: {p}  "
            f"(--use-cassettes is strict; pass --allow-live-fallback to "
            f"call the live API for missing cells)"
        )
    return load_phase1_cassette(p)


def _resolve_cassette_phase2(
    cfg: HarnessConfig, *, condition: str, fixture: str,
) -> Phase2Cassette | None:
    if not cfg.use_cassettes or cfg.cassettes_dir is None:
        return None
    p = cfg.cassettes_dir / condition / fixture
    graph_p = p / "graph.json"
    summary_p = p / "summary.json"
    if not graph_p.exists() or not summary_p.exists():
        if cfg.allow_live_fallback:
            return None
        missing = [str(f) for f in (graph_p, summary_p) if not f.exists()]
        raise CassetteMissingError(
            f"phase2 cassette missing in {p}: {missing}  "
            f"(--use-cassettes is strict; pass --allow-live-fallback to "
            f"call the live API for missing cells)"
        )
    return load_phase2_cassette(p)


def _phase1_rows(
    *, harness: HarnessConfig, run_id: str, condition: Condition,
    truth: FixtureTruth, worker_console: Console,
) -> list[dict[str, Any]]:
    """Produce one row per (query, trial) for the fixture + condition."""
    rows: list[dict[str, Any]] = []
    cassette = _resolve_cassette_phase1(harness,
                                        condition=condition.name,
                                        fixture=truth.spec.stem)
    pdf_path = harness.pdf_root / truth.spec.pdf

    for query in truth.queries:
        for trial in range(harness.n_replicates):
            try:
                if cassette is not None:
                    outcome, actual = _run_phase1_query_cassette(
                        query=query, cassette=cassette,
                    )
                    pred_graph = None
                else:
                    if not pdf_path.exists():
                        raise FileNotFoundError(f"PDF missing: {pdf_path}")
                    outcome, actual = _run_phase1_query_live(
                        fixture=truth, query=query, condition=condition,
                        pdf_path=pdf_path, console=worker_console,
                    )
                    pred_graph = None  # Phase 1 grader only needs the graph
                                       # for connectivity; live mode skips
                                       # the fallback to keep the row simple.
                score: ScoreResult = score_query(
                    scoring=query.scoring,
                    expected=query.expected_answer,
                    actual=actual,
                    params=query.scoring_params,
                    graph=pred_graph,
                    question=query.question,
                )
                detail = score.detail
                score_value = float(score.score)
            except Exception as exc:  # noqa: BLE001
                console.print(f"[red]phase1 {truth.spec.stem}/{query.id} trial={trial}: {exc}[/red]")
                outcome = QueryRunOutcome("", 0.0, 0.0, 0, 0)
                detail = f"error: {exc}"
                score_value = 0.0

            rows.append({
                "run_id": run_id,
                "condition": condition.name,
                "fixture": truth.spec.stem,
                "phase": 1,
                "metric_kind": "phase1_query",
                "family": query.family,
                "query_id": query.id,
                "scoring": query.scoring,
                "score": score_value,
                "detail": detail,
                "trial": trial,
                "cost_usd": outcome.cost_usd,
                "input_tokens": outcome.input_tokens,
                "output_tokens": outcome.output_tokens,
                "cache_read_tokens": outcome.cache_read_tokens,
                "cache_write_tokens": outcome.cache_write_tokens,
                "image_tokens": outcome.image_tokens,
                "n_steps": outcome.n_steps,
                "n_tool_calls": outcome.n_tool_calls,
                "tool_call_counts_json": (
                    json.dumps(outcome.tool_call_counts, sort_keys=True)
                    if outcome.tool_call_counts else ""
                ),
                "retries": outcome.retries,
                "wall_clock_s": outcome.wall_clock_s,
                "source_type": truth.spec.source_type,
                "domain": truth.spec.domain,
                "entity_count_truth": "",
            })
    return rows


def _phase2_rows(
    *, harness: HarnessConfig, run_id: str, condition: Condition,
    truth: FixtureTruth, worker_console: Console,
) -> list[dict[str, Any]]:
    """Produce one fixture-level row plus per-metric rows for Phase 2."""
    rows: list[dict[str, Any]] = []
    cassette = _resolve_cassette_phase2(harness,
                                        condition=condition.name,
                                        fixture=truth.spec.stem)
    pdf_path = harness.pdf_root / truth.spec.pdf
    run_dir_root = harness.out_dir / condition.name / "runs"

    try:
        if cassette is not None:
            outcome, pred_graph = _run_phase2_cassette(cassette=cassette)
        else:
            if not pdf_path.exists():
                raise FileNotFoundError(f"PDF missing: {pdf_path}")
            outcome, pred_graph = _run_phase2_live(
                fixture=truth, condition=condition, pdf_path=pdf_path,
                run_dir_root=run_dir_root, console=worker_console,
            )
    except Exception as exc:  # noqa: BLE001
        console.print(f"[red]phase2 {truth.spec.stem}/{condition.name}: {exc}[/red]")
        # Emit a single error row so the fixture appears in tables as failed.
        rows.append({
            "run_id": run_id,
            "condition": condition.name,
            "fixture": truth.spec.stem,
            "phase": 2,
            "metric_kind": "phase2_run",
            "family": "",
            "query_id": "",
            "scoring": "",
            "score": 0.0,
            "detail": f"error: {exc}",
            "trial": 0,
            "cost_usd": 0.0,
            "input_tokens": 0,
            "output_tokens": 0,
            "wall_clock_s": 0.0,
            "source_type": truth.spec.source_type,
            "domain": truth.spec.domain,
            "entity_count_truth": 0,
        })
        return rows

    # Score against truth (graph or annotations-only).
    pred_nodes = list(pred_graph.nodes) if pred_graph is not None else []

    has_full_truth = (
        truth.graph_truth is not None and len(truth.graph_truth.nodes) > 0
    )
    truth_nodes = (
        list(truth.graph_truth.nodes) if has_full_truth
        else _annotations_to_nodes(truth.annotations_truth)
    )
    entity_count_truth = len(truth_nodes)

    eq_prf = node_f1(truth_nodes, pred_nodes, kind_filter={"equipment"})
    inst_prf = node_f1(truth_nodes, pred_nodes, kind_filter={"instrument"})
    tag_em = tag_ocr_exact_match(truth_nodes, pred_nodes)

    # OPC F1 only makes sense when truth actually labels OPCs — inventory-only
    # fixtures (annotations.truth.jsonl) never do, so the metric is N/A there.
    truth_has_opc = any(n.kind == "opc" for n in truth_nodes)
    opc_prf = (node_f1(truth_nodes, pred_nodes, kind_filter={"opc"})
               if truth_has_opc else None)

    edge_score: float | None
    if has_full_truth and truth.graph_truth is not None and pred_graph is not None:
        edge_prf = edge_f1(truth.graph_truth, pred_graph)
        edge_score = edge_prf.f1
    else:
        edge_score = None  # rendered as N/A in the table

    base = {
        "run_id": run_id,
        "condition": condition.name,
        "fixture": truth.spec.stem,
        "phase": 2,
        "family": "",
        "query_id": "",
        "scoring": "",
        "trial": 0,
        "input_tokens": 0,
        "output_tokens": 0,
        "cache_read_tokens": 0,
        "cache_write_tokens": 0,
        "image_tokens": 0,
        "n_steps": 0,
        "n_tool_calls": 0,
        "tool_call_counts_json": "",
        "retries": 0,
        "wall_clock_s": 0.0,
        "cost_usd": 0.0,
        "source_type": truth.spec.source_type,
        "domain": truth.spec.domain,
        "entity_count_truth": entity_count_truth,
    }

    rows.append({**base, "metric_kind": "phase2_equipment_f1",
                 "score": eq_prf.f1,
                 "detail": f"P={eq_prf.precision:.2f} R={eq_prf.recall:.2f} "
                           f"tp={eq_prf.tp} fp={eq_prf.fp} fn={eq_prf.fn}"})
    rows.append({**base, "metric_kind": "phase2_instrument_f1",
                 "score": inst_prf.f1,
                 "detail": f"P={inst_prf.precision:.2f} R={inst_prf.recall:.2f} "
                           f"tp={inst_prf.tp} fp={inst_prf.fp} fn={inst_prf.fn}"})
    if opc_prf is not None:
        rows.append({**base, "metric_kind": "phase2_opc_f1",
                     "score": opc_prf.f1,
                     "detail": f"P={opc_prf.precision:.2f} R={opc_prf.recall:.2f} "
                               f"tp={opc_prf.tp} fp={opc_prf.fp} fn={opc_prf.fn}"})
    rows.append({**base, "metric_kind": "phase2_tag_ocr_em",
                 "score": tag_em, "detail": f"tag-OCR EM = {tag_em:.2f}"})
    if edge_score is not None:
        rows.append({**base, "metric_kind": "phase2_edge_f1",
                     "score": edge_score, "detail": "edge F1 (full-truth fixture)"})
    rows.append({**base, "metric_kind": "phase2_dexpi_validates",
                 "score": 1.0 if outcome.dexpi_validates else 0.0,
                 "detail": "dexpi validates" if outcome.dexpi_validates else "validation issues"})

    # Run-level summary row carrying cost / wall-clock / token totals.
    rows.append({
        **base,
        "metric_kind": "phase2_run",
        "score": 1.0 if outcome.dexpi_validates else 0.0,
        "detail": "fixture run",
        "cost_usd": outcome.cost_usd,
        "input_tokens": outcome.input_tokens,
        "output_tokens": outcome.output_tokens,
        "cache_read_tokens": outcome.cache_read_tokens,
        "cache_write_tokens": outcome.cache_write_tokens,
        "image_tokens": outcome.image_tokens,
        "n_steps": outcome.n_steps,
        "n_tool_calls": outcome.n_tool_calls,
        "tool_call_counts_json": (
            json.dumps(outcome.tool_call_counts, sort_keys=True)
            if outcome.tool_call_counts else ""
        ),
        "retries": outcome.retries,
        "wall_clock_s": outcome.wall_clock_s,
    })
    return rows


def _annotations_to_nodes(annotations: list) -> list:
    """Inventory-only fixtures store truth as Annotations; node_f1 wants
    ReconciledNodes. The two share kind / label / bbox_global, so synthesise
    a thin wrapper. Keep ids unique so 1-1 matching works."""
    from diagex.vision.models import ReconciledNode

    nodes: list[ReconciledNode] = []
    for a in annotations:
        nodes.append(ReconciledNode(
            id=a.id,
            kind=a.kind,
            label=a.label,
            bbox_global=a.bbox_global,
            page_index=a.page_index,
            attributes=dict(a.attributes),
            confidence=a.confidence,
            source_annotation_ids=[a.id],
        ))
    return nodes


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def _enumerate_fixtures(harness: HarnessConfig, manifest: Manifest) -> list[FixtureTruth]:
    out: list[FixtureTruth] = []
    for spec in manifest.fixtures:
        if harness.fixtures_filter and spec.stem not in harness.fixtures_filter:
            continue
        fixture_dir = harness.dataset_root / spec.stem
        out.append(load_fixture_truth(fixture_dir, spec))
    return out


def _job_summary(rows: list[dict[str, Any]], phase_int: int) -> str:
    """Compact one-liner summarising a just-finished (condition, fixture, phase) cell."""
    if not rows:
        return "no rows"
    if phase_int == 1:
        cost = sum(float(r.get("cost_usd", 0.0) or 0.0) for r in rows)
        in_t = sum(int(r.get("input_tokens", 0) or 0) for r in rows)
        out_t = sum(int(r.get("output_tokens", 0) or 0) for r in rows)
        cache_t = sum(int(r.get("cache_read_tokens", 0) or 0) for r in rows)
        scores = [float(r["score"]) for r in rows if r.get("metric_kind") == "phase1_query"]
        mean = sum(scores) / len(scores) if scores else float("nan")
        return (
            f"phase=1 mean={mean:.2f} (n={len(scores)})  "
            f"${cost:.4f}  in={in_t:,} out={out_t:,} cache={cache_t:,}"
        )
    # Phase 2: cost/tokens live on the phase2_run row; metric rows are 0-cost.
    run_rows = [r for r in rows if r.get("metric_kind") == "phase2_run"]
    cost = sum(float(r.get("cost_usd", 0.0) or 0.0) for r in run_rows)
    in_t = sum(int(r.get("input_tokens", 0) or 0) for r in run_rows)
    out_t = sum(int(r.get("output_tokens", 0) or 0) for r in run_rows)
    cache_t = sum(int(r.get("cache_read_tokens", 0) or 0) for r in run_rows)
    steps = sum(int(r.get("n_steps", 0) or 0) for r in run_rows)
    by_kind = {r["metric_kind"]: float(r["score"])
               for r in rows if r.get("metric_kind") in {
                   "phase2_equipment_f1", "phase2_instrument_f1", "phase2_edge_f1",
               }}
    parts = [f"{k.replace('phase2_', '')}={v:.2f}" for k, v in by_kind.items()]
    return (
        f"phase=2 " + " ".join(parts) +
        f"  ${cost:.4f}  in={in_t:,} out={out_t:,} cache={cache_t:,} steps={steps}"
    )


def _build_jobs(
    *, conditions: list[Condition], fixtures: list[FixtureTruth], phase: str,
) -> list[tuple[Condition, FixtureTruth, int]]:
    """One entry per (condition, fixture, phase_int) cell. Phase=both → two entries."""
    jobs: list[tuple[Condition, FixtureTruth, int]] = []
    want_p1 = phase in ("1", "both")
    want_p2 = phase in ("2", "both")
    for c in conditions:
        for t in fixtures:
            if want_p1 and t.queries:
                jobs.append((c, t, 1))
            if want_p2 and not getattr(c, "phase1_only", False):
                jobs.append((c, t, 2))
    return jobs


def _run(
    *, harness: HarnessConfig,
    phase: str, conditions: list[Condition],
    invocation: str,
    resume_mode: str = "auto",   # "auto" | "resume" | "fresh"
    resume_force: bool = False,
) -> Path:
    out_run_dir = harness.out_dir
    out_run_dir.mkdir(parents=True, exist_ok=True)

    manifest_path = harness.dataset_root / "manifest.yaml"
    manifest = load_manifest(manifest_path)
    if not harness.pdf_root.is_absolute():
        # Manifests typically have a workspace-relative pdf_root.
        harness_pdf_root = (manifest_path.parent.parent.parent / manifest.pdf_root)
        harness = HarnessConfig(**{**harness.__dict__, "pdf_root": harness_pdf_root})

    fixtures = _enumerate_fixtures(harness, manifest)
    all_jobs = _build_jobs(conditions=conditions, fixtures=fixtures, phase=phase)

    # ----- resume / fresh decision -----------------------------------------
    prior_progress = _load_progress(out_run_dir)
    prior_incomplete = (
        prior_progress is not None
        and int(prior_progress.get("jobs_done", 0)) < int(prior_progress.get("jobs_total", 0))
    )
    pending_jobs: list[tuple[Condition, FixtureTruth, int]] = list(all_jobs)
    seed_rows: list[dict[str, Any]] = []
    run_id: str
    csv_path = out_run_dir / "results.csv"

    if resume_mode == "resume":
        if not prior_incomplete:
            console.print(
                "[red]--resume passed but no incomplete run found in "
                f"{out_run_dir} (progress.json missing or already complete).[/red]"
            )
            raise typer.Exit(2)
        diffs = _check_resume_compatibility(
            list(prior_progress.get("argv", [])), invocation.split(),
        )
        if diffs and not resume_force:
            console.print(
                "[red]--resume incompatible: gated flags differ from prior run.[/red]"
            )
            for line in diffs:
                console.print(f"[red]{line}[/red]")
            console.print(
                "[red]Pass --resume-force to override (results from old + new "
                "rows will be mixed in the same CSV).[/red]"
            )
            raise typer.Exit(2)
        run_id = str(prior_progress["run_id"])
        done_cells, df_existing = _done_cells_from_csv(csv_path)
        seed_rows = df_existing.to_dict("records") if not df_existing.empty else []
        pending_jobs = [
            j for j in all_jobs
            if (j[0].name, j[1].spec.stem, j[2]) not in done_cells
        ]
        skipped = len(all_jobs) - len(pending_jobs)
        console.print(
            f"[bold]resume[/bold] run_id={run_id}  skipping {skipped} "
            f"completed cells, running {len(pending_jobs)} remaining"
        )
    elif resume_mode == "fresh":
        run_id = _new_run_id()
        # Wipe progress.json so the next "auto" check doesn't see the old one.
        (out_run_dir / "progress.json").unlink(missing_ok=True)
    else:  # "auto"
        if prior_incomplete:
            console.print(
                f"[red]Found incomplete run {prior_progress.get('run_id')!r} "
                f"({prior_progress.get('jobs_done')}/{prior_progress.get('jobs_total')} "
                f"jobs done) in {out_run_dir}.[/red]"
            )
            console.print(
                "[red]Pass --resume to continue it, or --fresh to start over "
                "(existing results.csv will be overwritten).[/red]"
            )
            raise typer.Exit(2)
        run_id = _new_run_id()

    _write_invocation(out_run_dir, argv=invocation.split(), run_id=run_id)
    console.print(
        f"[bold]run_id[/bold]={run_id}, fixtures={len(fixtures)}, "
        f"conditions={[c.name for c in conditions]}, phase={phase}, "
        f"cassettes={harness.use_cassettes}, parallel={harness.parallel}, "
        f"jobs={len(pending_jobs)}"
    )

    # ----- in-flight bookkeeping ------------------------------------------
    rows: list[dict[str, Any]] = list(seed_rows)
    in_flight: set[str] = set()
    in_flight_lock = threading.Lock()

    def _running_totals() -> dict[str, Any]:
        """Derive cost/token/wall totals from the current ``rows`` list.

        Reads through ``_is_billable_row`` so Phase-2 metric rows don't
        double-count. Computed on demand instead of accumulated, so concurrent
        completions can't race on the totals.
        """
        cost = inp = outp = cache = 0.0
        wall = 0.0
        for r in rows:
            if not _is_billable_row(r):
                continue
            cost += float(r.get("cost_usd", 0.0) or 0.0)
            inp += int(r.get("input_tokens", 0) or 0)
            outp += int(r.get("output_tokens", 0) or 0)
            cache += int(r.get("cache_read_tokens", 0) or 0)
            wall += float(r.get("wall_clock_s", 0.0) or 0.0)
        return {
            "total_cost_usd": round(cost, 4),
            "total_input_tokens": int(inp),
            "total_output_tokens": int(outp),
            "total_cache_read_tokens": int(cache),
            "total_wall_clock_s": round(wall, 1),
        }

    progress_state: dict[str, Any] = {
        "run_id": run_id,
        "started_at": dt.datetime.now().isoformat(timespec="seconds"),
        "_started_monotonic": time.time(),
        "argv": invocation.split(),
        "jobs_total": len(all_jobs),
        "jobs_done": len(all_jobs) - len(pending_jobs),
        "jobs_in_flight": [],
        "jobs_planned": [
            {"condition": c.name, "fixture": t.spec.stem, "phase": p}
            for (c, t, p) in all_jobs
        ],
        **_running_totals(),
        "last_completed": None,
    }

    # Always emit an initial progress.json + results.csv so the operator can
    # see something on disk before the first job finishes.
    df0 = pd.DataFrame(rows) if rows else pd.DataFrame(columns=agg.RESULTS_COLUMNS)
    _persist_tick(out_dir=out_run_dir, df=df0, progress_state=progress_state)

    # Worker console: in parallel mode, force non-TTY so extractors pick
    # PlainConsoleReporter (avoids N concurrent rich.Live displays). In
    # serial mode, keep the module-level (TTY) console so the operator gets
    # the rich per-step LiveConsoleReporter.
    use_parallel = harness.parallel > 1
    use_progress_bar = use_parallel and console.is_terminal
    if use_parallel:
        worker_console = Console(file=sys.stdout, force_terminal=False, soft_wrap=True)
    else:
        worker_console = console

    def _job(condition: Condition, truth: FixtureTruth, phase_int: int) -> list[dict[str, Any]]:
        if phase_int == 1:
            if not truth.queries:
                return []
            return _phase1_rows(
                harness=harness, run_id=run_id, condition=condition,
                truth=truth, worker_console=worker_console,
            )
        return _phase2_rows(
            harness=harness, run_id=run_id, condition=condition,
            truth=truth, worker_console=worker_console,
        )

    def _on_complete(
        condition: Condition, truth: FixtureTruth, phase_int: int,
        new_rows: list[dict[str, Any]], elapsed_s: float,
    ) -> None:
        rows.extend(new_rows)
        progress_state["jobs_done"] = int(progress_state["jobs_done"]) + 1

        # Per-job billable summary for the last_completed banner.
        cost_this = inp_this = outp_this = cache_this = 0.0
        for r in new_rows:
            if not _is_billable_row(r):
                continue
            cost_this += float(r.get("cost_usd", 0.0) or 0.0)
            inp_this += int(r.get("input_tokens", 0) or 0)
            outp_this += int(r.get("output_tokens", 0) or 0)
            cache_this += int(r.get("cache_read_tokens", 0) or 0)

        progress_state.update(_running_totals())
        progress_state["last_completed"] = {
            "condition": condition.name, "fixture": truth.spec.stem,
            "phase": phase_int, "wall_clock_s": round(elapsed_s, 1),
            "cost_usd": round(cost_this, 4),
            "input_tokens": int(inp_this), "output_tokens": int(outp_this),
            "cache_read_tokens": int(cache_this),
        }
        with in_flight_lock:
            in_flight.discard(f"{condition.name}/{truth.spec.stem}#{phase_int}")
            progress_state["jobs_in_flight"] = sorted(in_flight)
        df_now = pd.DataFrame(rows) if rows else pd.DataFrame(columns=agg.RESULTS_COLUMNS)
        _persist_tick(out_dir=out_run_dir, df=df_now, progress_state=progress_state)

    def _summary_line(condition: Condition, truth: FixtureTruth,
                      phase_int: int, new_rows: list[dict[str, Any]],
                      elapsed_s: float, k: int) -> str:
        return (
            f"[{k}/{progress_state['jobs_total']}] "
            f"{condition.name}/{truth.spec.stem} ✓ "
            f"in {elapsed_s:.1f}s  {_job_summary(new_rows, phase_int)}"
        )

    # ----- execution: parallel (thread pool) or serial (loop) -------------
    # Independent of the Progress bar (which only renders on TTY).
    if pending_jobs:
        progress_bar: Progress | None = None
        progress_task_id = None
        if use_progress_bar:
            progress_bar = Progress(
                SpinnerColumn(),
                TextColumn("[bold]{task.description}"),
                BarColumn(),
                MofNCompleteColumn(),
                TimeElapsedColumn(),
                TextColumn("eta"),
                TimeRemainingColumn(),
                TextColumn("[cyan]${task.fields[cost]:.2f}[/cyan]"),
                console=console, transient=False,
            )
            progress_bar.start()
            progress_task_id = progress_bar.add_task(
                "evaluating",
                total=progress_state["jobs_total"],
                completed=progress_state["jobs_done"],
                cost=progress_state["total_cost_usd"],
            )

        def _emit(line: str) -> None:
            (progress_bar.console if progress_bar else console).print(line)

        def _drain(c: Condition, t: FixtureTruth, p: int,
                   new_rows: list[dict[str, Any]], elapsed: float) -> None:
            _on_complete(c, t, p, new_rows, elapsed)
            k = int(progress_state["jobs_done"])
            _emit(_summary_line(c, t, p, new_rows, elapsed, k))
            if progress_bar is not None:
                progress_bar.update(progress_task_id, completed=k,
                                    cost=progress_state["total_cost_usd"])

        try:
            if use_parallel:
                with ThreadPoolExecutor(max_workers=harness.parallel) as pool:
                    futures: dict[Future, tuple[Condition, FixtureTruth, int, float]] = {}
                    for c, t, p in pending_jobs:
                        with in_flight_lock:
                            in_flight.add(f"{c.name}/{t.spec.stem}#{p}")
                        futures[pool.submit(_job, c, t, p)] = (c, t, p, time.perf_counter())
                    for fut in as_completed(futures):
                        c, t, p, started = futures[fut]
                        elapsed = time.perf_counter() - started
                        try:
                            new_rows = fut.result()
                        except Exception as exc:  # noqa: BLE001
                            _emit(f"[red]{c.name}/{t.spec.stem} phase={p} crashed: {exc}[/red]")
                            new_rows = []
                        _drain(c, t, p, new_rows, elapsed)
            else:
                for c, t, p in pending_jobs:
                    k_next = int(progress_state["jobs_done"]) + 1
                    _emit(
                        f"[dim]{k_next}/{progress_state['jobs_total']} "
                        f"starting {c.name}/{t.spec.stem} phase={p}...[/dim]"
                    )
                    with in_flight_lock:
                        in_flight.add(f"{c.name}/{t.spec.stem}#{p}")
                    started = time.perf_counter()
                    try:
                        new_rows = _job(c, t, p)
                    except Exception as exc:  # noqa: BLE001
                        _emit(f"[red]{c.name}/{t.spec.stem} phase={p} crashed: {exc}[/red]")
                        new_rows = []
                    elapsed = time.perf_counter() - started
                    _drain(c, t, p, new_rows, elapsed)
        finally:
            if progress_bar is not None:
                progress_bar.stop()

    # ----- final pass: tables, figures, σ-diff report.md, prev.csv roll ----
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=agg.RESULTS_COLUMNS)
    _atomic_write_csv(df, csv_path)

    if harness.emit_tables and not df.empty:
        wide = agg.phase1_per_fixture_wide(df)
        per_fixture = agg.phase2_per_fixture(df)
        latex_tables.write_tables(out_run_dir / "tables",
                                   table2_wide=wide, table3=per_fixture)

    if harness.emit_figures and not df.empty:
        try:
            from eval.figures.fig2_cost_accuracy import render_figure2
            from eval.figures.fig3_heterogeneity import render_figure3
        except Exception as exc:  # noqa: BLE001
            console.print(f"[yellow]figures skipped: {exc}[/yellow]")
        else:
            try:
                render_figure2(agg.figure2_points(df), out_run_dir / "figures" / "fig2.pdf")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]fig2 skipped: {exc}[/yellow]")
            try:
                render_figure3(out_run_dir / "figures" / "fig3_heterogeneity.pdf")
            except Exception as exc:  # noqa: BLE001
                console.print(f"[yellow]fig3 skipped: {exc}[/yellow]")

    prev_csv = out_run_dir / "results.prev.csv"
    df_prev = pd.read_csv(prev_csv) if prev_csv.exists() else None
    report_md.write_report(
        out_run_dir / "report.md",
        df_curr=df, df_prev=df_prev,
        run_id=run_id, invocation=invocation,
    )

    if csv_path.exists():
        shutil.copy2(csv_path, prev_csv)

    console.print(f"[green]wrote {csv_path}[/green]")
    return csv_path


@app.command()
def run(
    fixtures: Path = typer.Option(
        Path("eval/datasets"), "--fixtures", help="Dataset root containing the manifest.",
    ),
    phase: str = typer.Option("both", "--phase", help="1|2|both"),
    conditions: str = typer.Option(
        "baseline", "--conditions",
        help="Comma-separated condition names (see eval/conditions.py).",
    ),
    parallel: int = typer.Option(1, "--parallel", help="Worker count for fixture × condition jobs."),
    out: Path = typer.Option(Path("out/diagex"), "--out", help="Output directory."),
    emit: str = typer.Option(
        "tables,figures,artifacts", "--emit",
        help="Comma-separated subset of {tables,figures,artifacts}.",
    ),
    use_cassettes: bool = typer.Option(
        False, "--use-cassettes",
        help="Read pre-canned per-fixture outputs from --cassettes-dir; no API calls. "
             "Strict by default — missing cassettes raise. Pass --allow-live-fallback "
             "to call the live API for any missing (condition, fixture) cells.",
    ),
    allow_live_fallback: bool = typer.Option(
        False, "--allow-live-fallback",
        help="When --use-cassettes is on and a cassette is missing, call the live "
             "API for that cell instead of erroring. Costs real money — opt in.",
    ),
    cassettes_dir: Path = typer.Option(
        Path("eval/cassettes"), "--cassettes-dir", help="Cassette root.",
    ),
    n_replicates: int = typer.Option(1, "--n-replicates",
                                     help="Phase 1 trials per query (plan §8.1: N=3)."),
    fixtures_filter: str = typer.Option(
        "", "--only", help="Comma-separated fixture stems to restrict to.",
    ),
    resume: bool = typer.Option(
        False, "--resume",
        help="Continue an incomplete prior run in --out (reuses run_id, "
             "skips already-completed (condition, fixture, phase) cells).",
    ),
    fresh: bool = typer.Option(
        False, "--fresh",
        help="Start a new run even if --out has an incomplete progress.json. "
             "Existing results.csv will be overwritten.",
    ),
    resume_force: bool = typer.Option(
        False, "--resume-force",
        help="With --resume: tolerate gated-flag mismatches "
             "(--conditions/--phase/--only/--n-replicates/--use-cassettes). "
             "Mixes old and new rows in the same CSV — opt in.",
    ),
) -> None:
    if phase not in ("1", "2", "both"):
        console.print(f"[red]invalid --phase {phase!r}; pick 1|2|both.[/red]")
        raise typer.Exit(2)
    if resume and fresh:
        console.print("[red]--resume and --fresh are mutually exclusive.[/red]")
        raise typer.Exit(2)
    cond_objs = resolve_conditions(conditions.split(","))
    emit_set = {tok.strip() for tok in emit.split(",") if tok.strip()}
    invalid = emit_set - {"tables", "figures", "artifacts"}
    if invalid:
        console.print(f"[red]invalid --emit tokens: {invalid}.[/red]")
        raise typer.Exit(2)

    only = tuple(s.strip() for s in fixtures_filter.split(",") if s.strip()) if fixtures_filter else None

    manifest_path = fixtures / "manifest.yaml"
    if not manifest_path.exists():
        console.print(f"[red]manifest missing: {manifest_path}[/red]")
        raise typer.Exit(2)
    manifest = load_manifest(manifest_path)
    pdf_root = (fixtures.parent.parent / manifest.pdf_root) if not manifest.pdf_root.is_absolute() \
                else manifest.pdf_root

    if allow_live_fallback and not use_cassettes:
        console.print(
            "[yellow]--allow-live-fallback has no effect without --use-cassettes; ignoring.[/yellow]"
        )

    harness = HarnessConfig(
        out_dir=out,
        cassettes_dir=cassettes_dir if use_cassettes else None,
        use_cassettes=use_cassettes,
        parallel=max(1, parallel),
        n_replicates=max(1, n_replicates),
        fixtures_filter=only,
        dataset_root=fixtures,
        pdf_root=pdf_root,
        emit_tables="tables" in emit_set,
        emit_figures="figures" in emit_set,
        emit_artifacts="artifacts" in emit_set,
        allow_live_fallback=allow_live_fallback,
    )

    invocation = " ".join(sys.argv)
    resume_mode = "resume" if resume else "fresh" if fresh else "auto"
    csv_path = _run(
        harness=harness, phase=phase, conditions=cond_objs,
        invocation=invocation, resume_mode=resume_mode, resume_force=resume_force,
    )
    console.print(f"[bold green]done.[/bold green] results.csv → {csv_path}")


if __name__ == "__main__":
    app()
