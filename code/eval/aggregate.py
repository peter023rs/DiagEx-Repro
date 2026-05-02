"""Aggregate per-(condition, fixture, metric) rows into paper-shape tables.

Reads ``out/diagex/results.csv`` (the single source of truth, plan §7.1)
and produces:

* Table II input — per-fixture × query-family accuracy (long DataFrame)
* Table III input — per-fixture Phase-2 metrics (one row per fixture)
* Figure-2 input — cost vs entity-count points

Pure pandas; no I/O outside the CSV read. Tables/figures are written by the
``latex_tables`` and ``figures`` modules.
"""

from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import pandas as pd

# Stable column contract for results.csv. The driver writes one row per
# (run_id, condition, fixture, phase, metric) tuple; downstream code keys
# on these names without renaming.
RESULTS_COLUMNS = [
    "run_id",          # batch run id (one per run_paper_eval invocation)
    "condition",       # baseline | ablation-no-tile | ...
    "fixture",         # stem from manifest
    "phase",           # 1 | 2
    "metric_kind",     # "phase1_query" | "phase2_node_f1" | ...
    "family",          # query family (Phase 1) or "" (Phase 2)
    "query_id",        # "" for Phase 2
    "scoring",         # set_match | numeric_tolerance | ... | ""
    "score",           # 0..1
    "detail",          # one-liner
    "trial",           # 0..N-1 (Phase 1 N=3 replicates)
    "cost_usd",        # cost charged to this metric row (Phase 1 query, Phase 2 fixture)
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",   # tokens served from prompt cache (~0.1× price)
    "cache_write_tokens",  # tokens written to cache on this call
    "image_tokens",        # vision input tokens (subset of input_tokens)
    "n_steps",             # LLM round-trips (= tool-call iterations)
    "n_tool_calls",        # total tool_use blocks across all steps
    "tool_call_counts_json",  # JSON-encoded {tool_name: count}; "" if absent
    "retries",             # SDK retry attempts (5xx / 429 / connection errors)
    "wall_clock_s",
    "source_type",     # vector | raster | scanned (from meta.yaml)
    "domain",          # from meta.yaml
    "entity_count_truth",  # Phase 2 only
]

# Backfilled to a sensible zero/empty default by ``_ensure_observability_columns``
# so old CSVs (pre-2026-04) load without errors.
_OBSERVABILITY_DEFAULTS: dict[str, object] = {
    "cache_read_tokens": 0,
    "cache_write_tokens": 0,
    "image_tokens": 0,
    "n_steps": 0,
    "n_tool_calls": 0,
    "tool_call_counts_json": "",
    "retries": 0,
}


def _ensure_observability_columns(df: pd.DataFrame) -> pd.DataFrame:
    """Backfill any missing observability columns with their default value."""
    for col, default in _OBSERVABILITY_DEFAULTS.items():
        if col not in df.columns:
            df[col] = default
    return df


def load_results(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path)
    df = _ensure_observability_columns(df)
    required = [c for c in RESULTS_COLUMNS if c not in _OBSERVABILITY_DEFAULTS]
    missing = [c for c in required if c not in df.columns]
    if missing:
        raise ValueError(f"results.csv missing columns: {missing}")
    return df


def write_results(df: pd.DataFrame, csv_path: Path) -> None:
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df = _ensure_observability_columns(df.copy())
    # Column order is part of the contract.
    df = df.reindex(columns=RESULTS_COLUMNS)
    df.to_csv(csv_path, index=False)


# ---------------------------------------------------------------------------
# Phase 1 — per-diagram × family
# ---------------------------------------------------------------------------


PHASE1_FAMILIES = ("inventory", "counting", "connectivity", "identification")


def phase1_per_fixture(df: pd.DataFrame, *, condition: str = "baseline") -> pd.DataFrame:
    """Long-format DataFrame: rows = (fixture, family) → mean(score) over trials.

    Use ``pivot`` downstream to get the wide Table II shape.
    """
    sub = df[(df["phase"] == 1) & (df["condition"] == condition)].copy()
    if sub.empty:
        return pd.DataFrame(columns=["fixture", "family", "score", "n_trials"])
    grouped = (
        sub.groupby(["fixture", "family"], as_index=False)
        .agg(score=("score", "mean"), n_trials=("trial", "nunique"))
    )
    return grouped


def phase1_per_fixture_wide(df: pd.DataFrame, *, condition: str = "baseline") -> pd.DataFrame:
    """Table II input: rows=fixture, columns=family + ``overall``,
    cost columns appended. ``overall`` is the per-fixture mean across the
    available families. The "macro" row at the bottom is the column-wise
    mean across fixtures."""
    long = phase1_per_fixture(df, condition=condition)
    if long.empty:
        return pd.DataFrame()

    wide = long.pivot(index="fixture", columns="family", values="score")
    for fam in PHASE1_FAMILIES:
        if fam not in wide.columns:
            wide[fam] = float("nan")
    wide = wide[list(PHASE1_FAMILIES)]
    wide["overall"] = wide.mean(axis=1)

    # Cost / latency / token totals across queries × trials for each fixture.
    sub = _ensure_observability_columns(
        df[(df["phase"] == 1) & (df["condition"] == condition)].copy()
    )
    cost_lat = (
        sub.groupby("fixture")
        .agg(
            cost_total=("cost_usd", "sum"),
            cost_median=("cost_usd", "median"),
            latency_total=("wall_clock_s", "sum"),
            latency_median=("wall_clock_s", "median"),
            input_tokens_total=("input_tokens", "sum"),
            output_tokens_total=("output_tokens", "sum"),
            cache_read_tokens_total=("cache_read_tokens", "sum"),
            n_calls=("score", "size"),
        )
    )
    out = wide.join(cost_lat, how="left").reset_index()

    macro = pd.DataFrame([{
        "fixture": "macro",
        **{fam: out[fam].mean(skipna=True) for fam in PHASE1_FAMILIES},
        "overall": out["overall"].mean(skipna=True),
        "cost_total": out["cost_total"].sum(skipna=True),
        "cost_median": out["cost_median"].median(skipna=True),
        "latency_total": out["latency_total"].sum(skipna=True),
        "latency_median": out["latency_median"].median(skipna=True),
        "input_tokens_total": out["input_tokens_total"].sum(skipna=True),
        "output_tokens_total": out["output_tokens_total"].sum(skipna=True),
        "cache_read_tokens_total": out["cache_read_tokens_total"].sum(skipna=True),
        "n_calls": out["n_calls"].sum(skipna=True),
    }])
    return pd.concat([out, macro], ignore_index=True)


# ---------------------------------------------------------------------------
# Phase 2 — per-fixture extraction metrics
# ---------------------------------------------------------------------------


PHASE2_METRICS = (
    "phase2_equipment_f1",
    "phase2_instrument_f1",
    "phase2_opc_f1",
    "phase2_tag_ocr_em",
    "phase2_edge_f1",
    "phase2_dexpi_validates",
)


def phase2_per_fixture(df: pd.DataFrame, *, condition: str = "baseline") -> pd.DataFrame:
    """Table III input: one row per fixture, one column per Phase-2 metric.

    Edge F1 is NaN for partial-truth fixtures (no edges in truth → edge_f1
    is reported as ``N/A`` in the rendered table)."""
    sub = df[(df["phase"] == 2) & (df["condition"] == condition)].copy()
    if sub.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for fixture, fdf in sub.groupby("fixture"):
        row = {"fixture": fixture}
        for metric in PHASE2_METRICS:
            mdf = fdf[fdf["metric_kind"] == metric]
            row[metric] = float(mdf["score"].mean()) if not mdf.empty else float("nan")
        # Cost / wall-clock attached to the fixture-level row (metric_kind="phase2_run").
        run_row = fdf[fdf["metric_kind"] == "phase2_run"]
        if not run_row.empty:
            r0 = run_row.iloc[0]
            def _i(v) -> int:
                try:
                    f = float(v)
                except (TypeError, ValueError):
                    return 0
                return 0 if (f != f) else int(f)  # NaN-safe
            def _f(v) -> float:
                try:
                    f = float(v)
                except (TypeError, ValueError):
                    return 0.0
                return 0.0 if (f != f) else f
            row["cost_usd"] = _f(r0.get("cost_usd"))
            row["wall_clock_s"] = _f(r0.get("wall_clock_s"))
            row["wall_clock_min"] = row["wall_clock_s"] / 60.0
            row["input_tokens"] = _i(r0.get("input_tokens"))
            row["output_tokens"] = _i(r0.get("output_tokens"))
            row["cache_read_tokens"] = _i(r0.get("cache_read_tokens"))
            row["image_tokens"] = _i(r0.get("image_tokens"))
            row["n_steps"] = _i(r0.get("n_steps"))
            row["entity_count_truth"] = _f(r0.get("entity_count_truth"))
            row["source_type"] = str(r0.get("source_type", "") or "")
            row["domain"] = str(r0.get("domain", "") or "")
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------
# Run-level totals (cost / tokens / wall-clock) — used by report.md and the
# live progress.json tick. Phase 1 sums every query trial; Phase 2 sums only
# the `phase2_run` row per fixture (other phase-2 rows are scoring metrics
# with cost=0 and would double-count if included).
# ---------------------------------------------------------------------------


_TOTAL_FIELDS = (
    "cost_usd", "input_tokens", "output_tokens",
    "cache_read_tokens", "cache_write_tokens",
    "image_tokens", "n_steps", "n_tool_calls", "retries",
    "wall_clock_s", "n_calls",
)


def _sum_billable(sub: pd.DataFrame) -> dict[str, float]:
    if sub.empty:
        return {k: 0 for k in _TOTAL_FIELDS}
    out: dict[str, float] = {}
    for col in ("cost_usd", "wall_clock_s"):
        out[col] = float(sub[col].fillna(0).sum()) if col in sub.columns else 0.0
    for col in ("input_tokens", "output_tokens", "cache_read_tokens",
                "cache_write_tokens", "image_tokens", "n_steps",
                "n_tool_calls", "retries"):
        out[col] = int(sub[col].fillna(0).sum()) if col in sub.columns else 0
    out["n_calls"] = int(len(sub))
    return out


def run_totals(df: pd.DataFrame) -> dict[str, dict[str, float]]:
    """Return ``{phase1, phase2, total}`` → totals dict.

    Each totals dict has cost_usd, input/output/cache tokens, image_tokens,
    n_steps, n_tool_calls, retries, wall_clock_s, n_calls. Phase 2 sums only
    the ``phase2_run`` row per fixture (other rows are scoring metrics with
    cost=0 and would double-count).
    """
    df = _ensure_observability_columns(df.copy()) if not df.empty else df
    p1 = df[df["phase"] == 1] if not df.empty else df
    p2_run = (df[(df["phase"] == 2) & (df["metric_kind"] == "phase2_run")]
              if not df.empty else df)

    p1t = _sum_billable(p1)
    p2t = _sum_billable(p2_run)
    total = {k: (p1t[k] + p2t[k]) for k in _TOTAL_FIELDS}
    return {"phase1": p1t, "phase2": p2t, "total": total}


def run_totals_by_condition(df: pd.DataFrame) -> dict[str, dict[str, dict[str, float]]]:
    """``{condition: {phase1, phase2, total}}``. Conditions present in the
    DataFrame are returned in stable sorted order.

    Use this in addition to (not instead of) ``run_totals`` so a single-
    condition run still has a single totals block to render."""
    if df.empty:
        return {}
    out: dict[str, dict[str, dict[str, float]]] = {}
    for cond in sorted(df["condition"].dropna().unique().tolist()):
        out[cond] = run_totals(df[df["condition"] == cond])
    return out


# ---------------------------------------------------------------------------
# Figure 2 — cost / accuracy scatter
# ---------------------------------------------------------------------------


def figure2_points(df: pd.DataFrame, *, condition: str = "baseline") -> pd.DataFrame:
    p2 = phase2_per_fixture(df, condition=condition)
    if p2.empty:
        return p2
    keep = ["fixture", "entity_count_truth", "cost_usd", "source_type",
            "phase2_equipment_f1", "phase2_instrument_f1"]
    out = p2.copy()
    out["overall_f1"] = out[["phase2_equipment_f1", "phase2_instrument_f1"]].mean(axis=1)
    return out[keep + ["overall_f1"]]


# ---------------------------------------------------------------------------
# Run-over-run delta (used by report_md.py)
# ---------------------------------------------------------------------------


def diff_runs(prev: pd.DataFrame, curr: pd.DataFrame, *, sigma_threshold: float = 2.0) -> pd.DataFrame:
    """Per-(condition, fixture, metric_kind) Δ = curr_mean − prev_mean.

    σ is taken from the union of both runs' trial pool. Returns rows where
    |Δ| ≥ sigma_threshold × σ (or σ == 0 and Δ != 0)."""
    keys = ["condition", "fixture", "metric_kind", "family", "query_id"]

    def _agg(d: pd.DataFrame) -> pd.DataFrame:
        return d.groupby(keys, as_index=False).agg(score=("score", "mean"),
                                                   n=("score", "size"),
                                                   sd=("score", "std"))

    a = _agg(prev).rename(columns={"score": "score_prev", "n": "n_prev", "sd": "sd_prev"})
    b = _agg(curr).rename(columns={"score": "score_curr", "n": "n_curr", "sd": "sd_curr"})
    merged = a.merge(b, on=keys, how="outer")
    merged["delta"] = merged["score_curr"] - merged["score_prev"]
    sd = merged[["sd_prev", "sd_curr"]].fillna(0).max(axis=1)
    merged["sd"] = sd

    def is_flagged(row: pd.Series) -> bool:
        d = row["delta"]
        if pd.isna(d):
            return False
        s = row["sd"]
        if s == 0 or pd.isna(s):
            return abs(d) > 1e-9
        return abs(d) >= sigma_threshold * s

    return merged[merged.apply(is_flagged, axis=1)].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Convenience for ad-hoc inspection
# ---------------------------------------------------------------------------


def list_conditions(df: pd.DataFrame) -> Iterable[str]:
    return sorted(df["condition"].dropna().unique().tolist())
