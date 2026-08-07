"""Phase 1 query extractor: point diagex at a diagram, ask a question, get an answer.

Spec §7.1 is the contract: CLI options, --effort profile, multi-page support via
page spec, artefact layout under runs/<diagram-stem>/<ts>_<id>/.
"""

from __future__ import annotations

import datetime as dt
import json
import re
import secrets
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

from diagex.agent.runtime import ReactRuntime, RunConfig
from diagex.agent.state import AgentState, aggregate_tool_call_counts
from diagex.config import Config, EffortLevel, load_config
from diagex.llm.client import LLMClient
from diagex.llm.cost import (
    CostTracker,
    format_tokens_millions,
    total_tokens_from_summary,
)
from diagex.llm.prompts.phase1_query import build_system_prompt
from diagex.ui.progress import make_reporter
from diagex.vision.loader import iter_pages, load
from diagex.vision.models import ReconciledGraph
from diagex.vision.reconcile import reconcile
from diagex.vision.tiling import AspectAwareStrategy, tile
from diagex.vision.views import ViewProvider

# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class PageAnswer:
    page_index: int
    answer: str
    confidence: str
    supporting_annotation_ids: list[str] = field(default_factory=list)


@dataclass
class QueryResult:
    question: str
    diagram_stem: str
    effort: EffortLevel
    model: str
    answers: list[PageAnswer]
    graph: ReconciledGraph
    cost_summary: dict[str, Any]
    run_dir: Path | None              # None when --no-persist
    run_id: str

    def to_text(self) -> str:
        lines: list[str] = []
        for pa in self.answers:
            header = f"--- page {pa.page_index + 1} · confidence {pa.confidence} ---"
            lines.append(header)
            lines.append(pa.answer.rstrip())
        if len(self.answers) > 1:
            lines.append(f"--- {len(self.answers)} pages queried ---")
        lines.append(
            "tokens: "
            f"{format_tokens_millions(total_tokens_from_summary(self.cost_summary))} "
            f"({format_tokens_millions(self.cost_summary.get('input_tokens', 0))} in / "
            f"{format_tokens_millions(self.cost_summary.get('output_tokens', 0))} out)"
        )
        if self.run_dir is not None:
            lines.append(f"run: {self.run_dir}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps({
            "question": self.question,
            "diagram_stem": self.diagram_stem,
            "effort": self.effort,
            "model": self.model,
            "run_id": self.run_id,
            "run_dir": str(self.run_dir) if self.run_dir else None,
            "answers": [
                {
                    "page_index": a.page_index,
                    "answer": a.answer,
                    "confidence": a.confidence,
                    "supporting_annotation_ids": a.supporting_annotation_ids,
                }
                for a in self.answers
            ],
            "cost": self.cost_summary,
            "graph": json.loads(self.graph.model_dump_json()),
        }, indent=2)


# ---------------------------------------------------------------------------
# Page-spec parser (1-based to 0-based index list)
# ---------------------------------------------------------------------------


def _parse_page_spec(spec: str) -> tuple[str, tuple[int, int] | None]:
    """Return ('all',None) or ('range',(lo,hi)) in 0-based inclusive form.

    Accepted: "1", "3-7", "all". Always 1-based on the CLI.
    """
    s = spec.strip().lower()
    if s == "all":
        return "all", None
    if "-" in s:
        lo, hi = s.split("-", 1)
        return "range", (int(lo) - 1, int(hi) - 1)
    n = int(s) - 1
    return "range", (n, n)


# ---------------------------------------------------------------------------
# Run-folder helpers (spec §7.1)
# ---------------------------------------------------------------------------


_STEM_SAFE = re.compile(r"[^a-z0-9._-]+")


def _safe_stem(path: Path) -> str:
    stem = path.stem.lower()
    stem = _STEM_SAFE.sub("-", stem).strip("-")
    return stem or "diagram"


def _new_run_id() -> str:
    return "r-" + secrets.token_hex(2)


def _timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def _prepare_run_dir(cfg: Config, stem: str) -> tuple[Path, str]:
    runs_root = cfg.runs_dir / stem
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = _new_run_id()
    run_dir = runs_root / f"{_timestamp()}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "tiles").mkdir(exist_ok=True)
    return run_dir, run_id


def _append_index(runs_root: Path, run_id: str, question: str, snippet: str) -> None:
    idx = runs_root / "index.md"
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    snippet_one_line = snippet.replace("\n", " ").strip()
    if len(snippet_one_line) > 100:
        snippet_one_line = snippet_one_line[:97] + "..."
    with idx.open("a", encoding="utf-8") as f:
        f.write(f"{ts}  {run_id}  {question!r} → {snippet_one_line}\n")


# ---------------------------------------------------------------------------
# Main entry point
# ---------------------------------------------------------------------------


def run_query(
    *,
    diagram: Path,
    question: str,
    page_spec: str = "1",
    effort: EffortLevel = "high",
    config: Config | None = None,
    persist: bool = True,
    console: Console | None = None,
) -> QueryResult:
    cfg = config or load_config()
    stem = _safe_stem(diagram)
    run_dir: Path | None = None
    run_id: str = "r-" + secrets.token_hex(2)

    if persist:
        run_dir, run_id = _prepare_run_dir(cfg, stem)

    # --- load + tile the diagram ------------------------------------------------
    source = load(diagram, tiling=cfg.tiling, scan_cfg=cfg.scan)

    kind, rng = _parse_page_spec(page_spec)
    want_all = kind == "all"
    lo_hi = rng

    cost = CostTracker(pricing=cfg.pricing) if _cost_accepts_pricing() else CostTracker()
    llm = LLMClient(cfg.llm, budgets=cfg.budgets)
    llm.reset_retry_counter()
    _t_run_start = time.perf_counter()
    system_blocks = build_system_prompt(question, effort)

    # Progress reporter: Rich Live for interactive TTYs, plain lines when piped.
    # Build it now so the TTY check sees the real stdout.
    progress_console = console or Console()
    reporter_factory = lambda: make_reporter(progress_console, effort=effort)  # noqa: E731

    runtime = ReactRuntime(
        client=llm,
        system_blocks=system_blocks,
        cost_tracker=cost,
        budgets=cfg.budgets,
    )

    answers: list[PageAnswer] = []
    all_annotations: list = []
    per_page_states: list[AgentState] = []
    per_page_status: dict[int, str] = {}

    for page in iter_pages(source):
        if not want_all:
            assert lo_hi is not None
            if page.page_index < lo_hi[0] or page.page_index > lo_hi[1]:
                continue

        tiles = tile(page, AspectAwareStrategy(
            max_tokens_per_tile=cfg.tiling.max_tokens_per_tile,
            overlap_frac=cfg.tiling.overlap_frac,
            token_per_pixel=cfg.tiling.token_per_pixel,
        ))
        vp = ViewProvider(page, tiles)
        state = AgentState(question=question, page=page)

        # Fresh reporter per page so Live contexts don't overlap and each page's
        # status bar starts clean.
        reporter = reporter_factory()
        runtime.reporter = reporter
        try:
            with reporter:
                runtime.run(state=state, view_provider=vp, run_cfg=RunConfig(effort=effort))
            per_page_status[page.page_index] = "ok" if state.final_answer else "error"
        except Exception as exc:
            state.final_answer = f"error during extraction: {exc}"
            state.final_confidence = "low"
            per_page_status[page.page_index] = "error"

        answers.append(PageAnswer(
            page_index=page.page_index,
            answer=state.final_answer or "(no answer produced)",
            confidence=state.final_confidence or "low",
            supporting_annotation_ids=[a.id for a in state.annotations.all()],
        ))
        all_annotations.extend(state.annotations.all())
        per_page_states.append(state)

        if run_dir is not None:
            _write_page_artefacts(run_dir, page, tiles, state)

    # --- reconcile across pages -------------------------------------------------
    graph = reconcile(all_annotations, source_path=source.path.name)
    graph.per_page_status = {k: _coerce_status(v) for k, v in per_page_status.items()}

    wall_clock_s = round(time.perf_counter() - _t_run_start, 3)
    retries = int(llm.retries_total)
    tool_call_counts = aggregate_tool_call_counts(per_page_states)

    cost_summary = cost.summary()
    cost_summary["wall_clock_s"] = wall_clock_s
    cost_summary["retries"] = retries
    cost_summary["tool_call_counts"] = tool_call_counts
    cost_summary["n_tool_calls"] = sum(tool_call_counts.values())

    if run_dir is not None:
        _write_run_artefacts(
            run_dir=run_dir,
            runs_root=run_dir.parent,
            run_id=run_id,
            question=question,
            answers=answers,
            graph=graph,
            cost=cost,
            effort=effort,
            model=cfg.llm.model,
            states=per_page_states,
            wall_clock_s=wall_clock_s,
            retries=retries,
            tool_call_counts=tool_call_counts,
        )

    return QueryResult(
        question=question,
        diagram_stem=stem,
        effort=effort,
        model=cfg.llm.model,
        answers=answers,
        graph=graph,
        cost_summary=cost_summary,
        run_dir=run_dir,
        run_id=run_id,
    )


def _coerce_status(s: str) -> str:
    if s in ("ok", "cost_exhausted", "error"):
        return s
    return "error"


def _cost_accepts_pricing() -> bool:
    """CostTracker may or may not accept a `pricing=` kwarg depending on impl."""
    try:
        import inspect
        sig = inspect.signature(CostTracker.__init__)
        return "pricing" in sig.parameters
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Artefact writers (spec §7.1)
# ---------------------------------------------------------------------------


def _write_page_artefacts(run_dir: Path, page, tiles, state: AgentState) -> None:
    # Thumbnails of tiles actually fetched (not all tiles).
    fetched_ids = [tid for tid, n in state.tile_fetch_counts.items() if n > 0]
    if fetched_ids:
        by_id = {t.id: t for t in tiles}
        for tid in fetched_ids:
            t = by_id.get(tid)
            if t is None or t.image is None:
                continue
            t.image.save(run_dir / "tiles" / f"p{page.page_index:02d}_{tid}.png")


def _write_run_artefacts(
    *,
    run_dir: Path,
    runs_root: Path,
    run_id: str,
    question: str,
    answers: list[PageAnswer],
    graph: ReconciledGraph,
    cost: CostTracker,
    effort: str,
    model: str,
    states: list[AgentState],
    wall_clock_s: float = 0.0,
    retries: int = 0,
    tool_call_counts: dict[str, int] | None = None,
) -> None:
    (run_dir / "query.txt").write_text(question + "\n", encoding="utf-8")

    # answer.md — humans read this first.
    lines = [f"# {question}\n"]
    for pa in answers:
        lines.append(f"## page {pa.page_index + 1} — confidence {pa.confidence}\n")
        lines.append(pa.answer.rstrip() + "\n")
    (run_dir / "answer.md").write_text("\n".join(lines), encoding="utf-8")

    # result.json — stable machine-readable shape (see spec §7.1).
    result_obj = {
        "schema_version": "0.1.0",
        "run_id": run_id,
        "question": question,
        "effort": effort,
        "model": model,
        "answers": [
            {
                "page_index": a.page_index,
                "answer": a.answer,
                "confidence": a.confidence,
                "supporting_annotation_ids": a.supporting_annotation_ids,
            }
            for a in answers
        ],
        "graph": json.loads(graph.model_dump_json()),
        "wall_clock_s": float(wall_clock_s),
        "retries": int(retries),
        "tool_call_counts": dict(tool_call_counts or {}),
    }
    (run_dir / "result.json").write_text(json.dumps(result_obj, indent=2), encoding="utf-8")

    # cost.json — per-step breakdown.
    (run_dir / "cost.json").write_text(cost.to_json(), encoding="utf-8")

    # transcript.jsonl — one JSON object per step (collected across all pages).
    with (run_dir / "transcript.jsonl").open("w", encoding="utf-8") as f:
        for st in states:
            for ts in st.transcript:
                f.write(json.dumps({
                    "page_index": st.page.page_index,
                    "step": ts.step,
                    "kind": ts.kind,
                    "payload": ts.payload,
                }) + "\n")

    # Index line — append-only history per diagram stem.
    first_snippet = answers[0].answer if answers else ""
    _append_index(runs_root, run_id, question, first_snippet)
