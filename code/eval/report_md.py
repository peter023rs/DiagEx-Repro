"""Human-readable digest emitted alongside ``results.csv``. Plan §7.1.

The author reads ``report.md`` before submission. It diffs against the prior
run's ``results.csv`` (if one exists) and flags any metric that moved more
than ``2σ`` — that is, the same threshold the plan calls out for "report.md
flags any metric that moved > 2 σ".

The report is plain text; no LaTeX. It ends up alongside
``out/diagex/<run_id>/report.md`` and a copy under
``out/diagex/report.md`` (the latter overwritten each run for quick
``less``).
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from eval.aggregate import (
    diff_runs,
    phase1_per_fixture_wide,
    phase2_per_fixture,
    run_totals,
    run_totals_by_condition,
)


def _aggregate_tool_call_counts(
    df: pd.DataFrame,
    *,
    condition: str | None = None,
) -> dict[str, int]:
    """Sum the per-row ``tool_call_counts_json`` strings from the CSV.

    The harness/rescore JSON-encode each cell's tool-call breakdown into the
    ``tool_call_counts_json`` column; this function decodes and aggregates.
    Phase 2 metric rows have empty strings (only ``phase2_run`` carries the
    data) — the empty-string check filters them. Returns a stable, descending-
    by-count dict. Empty when no row carries a breakdown.
    """
    from json import JSONDecodeError, loads

    if df.empty or "tool_call_counts_json" not in df.columns:
        return {}
    sub = df if condition is None else df[df["condition"] == condition]
    if sub.empty:
        return {}

    nonempty = sub["tool_call_counts_json"].dropna().astype(str)
    nonempty = nonempty[nonempty.str.strip().ne("")]
    counts: dict[str, int] = {}
    for raw in nonempty:
        try:
            tcc = loads(raw)
        except JSONDecodeError:
            continue
        if not isinstance(tcc, dict):
            continue
        for name, n in tcc.items():
            counts[str(name)] = counts.get(str(name), 0) + int(n or 0)
    return dict(sorted(counts.items(), key=lambda kv: (-kv[1], kv[0])))


def _fmt_int(n: float) -> str:
    """Compact integer with thousands separator."""
    return f"{int(n):,}"


def _fmt_secs(s: float) -> str:
    if s < 60:
        return f"{s:.1f}s"
    m, sec = divmod(s, 60)
    if m < 60:
        return f"{int(m)}m{int(sec):02d}s"
    h, m = divmod(int(m), 60)
    return f"{h}h{m:02d}m"


def _render_totals_block(
    header: str, totals: dict[str, dict[str, float]],
) -> list[str]:
    """Render one ``Run totals`` block. The Anthropic SDK reports
    ``input_tokens`` as *uncached* inputs, with cache reads/writes billed
    separately; cache_hit% is the fraction of total input flow from cache.
    """
    out: list[str] = [header]
    for label, key in (("Phase 1", "phase1"), ("Phase 2", "phase2"),
                       ("Combined", "total")):
        t = totals[key]
        if t["n_calls"] == 0 and key != "total":
            continue
        total_in_flow = (
            int(t["input_tokens"]) + int(t["cache_read_tokens"])
            + int(t.get("cache_write_tokens", 0))
        )
        cache_pct = (
            f", cache_hit={100.0 * t['cache_read_tokens'] / total_in_flow:.0f}%"
            if total_in_flow else ""
        )
        extras: list[str] = []
        for field, fmt in (("n_steps", "steps"), ("n_tool_calls", "tool_calls"),
                           ("retries", "retries")):
            if t[field]:
                extras.append(f"{fmt}={int(t[field])}")
        extras_str = (", " + ", ".join(extras)) if extras else ""
        out.append(
            f"  - **{label}** — calls={int(t['n_calls'])}, "
            f"cost=${t['cost_usd']:.4f}, "
            f"in={_fmt_int(t['input_tokens'])}, "
            f"out={_fmt_int(t['output_tokens'])}, "
            f"cache_read={_fmt_int(t['cache_read_tokens'])}{cache_pct}"
            f"{extras_str}, wall={_fmt_secs(t['wall_clock_s'])}"
        )
    return out


def render_report(
    df_curr: pd.DataFrame,
    df_prev: pd.DataFrame | None,
    *,
    run_id: str,
    invocation: str,
    sigma_threshold: float = 2.0,
) -> str:
    lines: list[str] = []
    lines.append(f"# diagex eval report — run `{run_id}`")
    lines.append("")
    lines.append(f"Invocation: `{invocation}`")
    lines.append("")
    lines.append(f"Rows: {len(df_curr)}")
    lines.append("")

    # Phase 1 summary
    p1 = phase1_per_fixture_wide(df_curr)
    if not p1.empty:
        lines.append("## Phase 1 (baseline) — per-fixture overall")
        lines.append("")
        for row in p1.itertuples():
            if row.fixture == "macro":
                continue
            cost_t = float(getattr(row, "cost_total", 0.0) or 0.0)
            in_t = int(getattr(row, "input_tokens_total", 0) or 0)
            out_t = int(getattr(row, "output_tokens_total", 0) or 0)
            cache_t = int(getattr(row, "cache_read_tokens_total", 0) or 0)
            wall_t = float(getattr(row, "latency_total", 0.0) or 0.0)
            n = int(getattr(row, "n_calls", 0) or 0)
            lines.append(
                f"- {row.fixture}: overall={row.overall:.2f} "
                f"(inv={row.inventory:.2f}, cnt={row.counting:.2f}, "
                f"conn={row.connectivity:.2f}, ident={row.identification:.2f})  "
                f"[n={n}, cost=${cost_t:.4f}, in={_fmt_int(in_t)}, "
                f"out={_fmt_int(out_t)}, cache_read={_fmt_int(cache_t)}, "
                f"wall={_fmt_secs(wall_t)}]"
            )
        macro = p1[p1["fixture"] == "macro"]
        if not macro.empty:
            m = macro.iloc[0]
            lines.append("")
            lines.append(
                f"**macro**: overall={m['overall']:.2f}  "
                f"cost_total=${float(m.get('cost_total', 0.0) or 0.0):.4f}, "
                f"cost_median=${float(m.get('cost_median', 0.0) or 0.0):.4f}, "
                f"in={_fmt_int(m.get('input_tokens_total', 0) or 0)}, "
                f"out={_fmt_int(m.get('output_tokens_total', 0) or 0)}, "
                f"cache_read={_fmt_int(m.get('cache_read_tokens_total', 0) or 0)}, "
                f"wall_total={_fmt_secs(float(m.get('latency_total', 0.0) or 0.0))}, "
                f"latency_median={float(m.get('latency_median', 0.0) or 0.0):.1f}s"
            )
        lines.append("")

    # Phase 2 summary
    p2 = phase2_per_fixture(df_curr)
    if not p2.empty:
        lines.append("## Phase 2 (baseline) — per-fixture extraction")
        lines.append("")
        for row in p2.itertuples():
            eq_f1 = getattr(row, "phase2_equipment_f1", float("nan"))
            inst_f1 = getattr(row, "phase2_instrument_f1", float("nan"))
            opc_f1 = getattr(row, "phase2_opc_f1", float("nan"))
            edge_f1 = getattr(row, "phase2_edge_f1", float("nan"))
            cost = getattr(row, "cost_usd", float("nan"))
            wall = getattr(row, "wall_clock_s", float("nan"))
            in_t = getattr(row, "input_tokens", 0) or 0
            out_t = getattr(row, "output_tokens", 0) or 0
            cache_t = getattr(row, "cache_read_tokens", 0) or 0
            steps = getattr(row, "n_steps", 0) or 0
            opc_str = "n/a" if pd.isna(opc_f1) else f"{opc_f1:.2f}"
            edge_str = "n/a" if pd.isna(edge_f1) else f"{edge_f1:.2f}"
            cost_str = "n/a" if pd.isna(cost) else f"{cost:.4f}"
            wall_str = "n/a" if pd.isna(wall) else _fmt_secs(float(wall))
            lines.append(
                f"- {row.fixture}: eq_f1={eq_f1:.2f}, inst_f1={inst_f1:.2f}, "
                f"opc_f1={opc_str}, edge_f1={edge_str}  "
                f"[cost=${cost_str}, in={_fmt_int(in_t)}, "
                f"out={_fmt_int(out_t)}, cache_read={_fmt_int(cache_t)}, "
                f"steps={int(steps)}, wall={wall_str}]"
            )
        lines.append("")

    # Run totals — split by condition when more than one ran, so the cost
    # comparison between conditions is the first thing the operator sees.
    by_cond = run_totals_by_condition(df_curr)
    if by_cond:
        lines.append("## Run totals")
        lines.append("")
        if len(by_cond) > 1:
            for cond, totals in by_cond.items():
                lines.extend(_render_totals_block(f"### Condition: {cond}", totals))
                lines.append("")
            lines.extend(_render_totals_block(
                "### Combined across conditions", run_totals(df_curr),
            ))
        else:
            (cond, totals), = by_cond.items()
            lines.extend(_render_totals_block(f"_(condition: {cond})_", totals))
        lines.append("")

        # Tool-call breakdown (per Phase / aggregate). Pulled from
        # runs/<stem>/<id>/result.json — silently empty if those files are
        # absent (e.g. a cassette-only run).
        breakdown = _aggregate_tool_call_counts(df_curr)
        if breakdown:
            lines.append("### Tool-call breakdown")
            lines.append("")
            top = list(breakdown.items())
            total_calls = sum(breakdown.values())
            for name, n in top:
                pct = 100.0 * n / total_calls if total_calls else 0.0
                lines.append(f"- {name}: {_fmt_int(n)} ({pct:.1f}%)")
            lines.append("")

    # σ-diff against previous run
    if df_prev is not None and not df_prev.empty:
        flagged = diff_runs(df_prev, df_curr, sigma_threshold=sigma_threshold)
        lines.append(f"## Δ vs. previous run (≥ {sigma_threshold}σ)")
        lines.append("")
        if flagged.empty:
            lines.append("(no metrics moved beyond threshold)")
        else:
            for row in flagged.itertuples():
                lines.append(
                    f"- {row.condition}/{row.fixture}/{row.metric_kind}"
                    f"{f' ({row.family})' if row.family else ''}: "
                    f"{row.score_prev:.3f} → {row.score_curr:.3f} "
                    f"(Δ={row.delta:+.3f}, σ={row.sd:.3f})"
                )
        lines.append("")

    # Conditions seen
    conds = sorted(df_curr["condition"].dropna().unique().tolist())
    lines.append(f"Conditions in this run: {', '.join(conds) if conds else '(none)'}")

    return "\n".join(lines).rstrip() + "\n"


def write_report(
    out_path: Path,
    *,
    df_curr: pd.DataFrame,
    df_prev: pd.DataFrame | None,
    run_id: str,
    invocation: str,
    sigma_threshold: float = 2.0,
) -> Path:
    text = render_report(
        df_curr, df_prev,
        run_id=run_id, invocation=invocation, sigma_threshold=sigma_threshold,
    )
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(text, encoding="utf-8")
    return out_path
