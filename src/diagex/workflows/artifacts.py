"""Coordinate extraction deliverables shared by the legacy and evidence engines.

This workflow invokes the existing renderers. Filesystem and checkpoint mechanics
live in ``diagex.runs``; format-specific rendering remains in its existing modules
until the export-module migration.
"""

from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any

from diagex.config import load_config
from diagex.llm.cost import format_elapsed, format_tokens_millions, total_tokens_from_summary
from diagex.runs.layout import append_index
from diagex.vision.legend_models import LegendPack
from diagex.vision.models import ReconciledGraph


def write_page_artifacts(run_dir: Path, page, tiles, state) -> None:
    fetched_ids = [tid for tid, n in state.tile_fetch_counts.items() if n > 0]
    region_fetches = getattr(state, "region_fetches", []) or []
    if not fetched_ids and not region_fetches:
        return
    by_id = {t.id: t for t in tiles}
    for tid in fetched_ids:
        t = by_id.get(tid)
        if t is None or t.image is None:
            continue
        t.image.save(run_dir / "tiles" / f"p{page.page_index:02d}_{tid}.png")
    for idx, region in enumerate(region_fetches):
        if region.image is None:
            continue
        name = (
            f"p{page.page_index:02d}_region-{idx:02d}"
            f"_x{region.x}-y{region.y}-w{region.w}-h{region.h}.png"
        )
        region.image.save(run_dir / "tiles" / name)


def write_run_artifacts(
    *,
    run_dir: Path,
    runs_root: Path,
    run_id: str,
    stem: str,
    effort: str,
    model: str,
    graph: ReconciledGraph,
    cost_summary: dict,
    dexpi_stats: dict,
    dexpi_issues: list[str],
    validation_issues: list[dict],
    dexpi_json_path: Path | None,
    legend_pack: LegendPack | None,
    legend_source_tag: str,
    states: list,
    per_page_status: dict[int, str],
    confidence_report_path: Path | None,
    engine: str = "legacy",
) -> None:
    # graph.json — full reconciled graph.
    (run_dir / "graph.json").write_text(graph.model_dump_json(indent=2), encoding="utf-8")

    # pages.json — the exact coordinate frame used by graph.json.  The human
    # review workbench uses this to reproduce source-aligned page renderings
    # even if rendering defaults change after the extraction run.
    page_records: list[dict] = []
    seen_pages: set[int] = set()
    for state in states:
        page = state.page
        if page.page_index in seen_pages:
            continue
        seen_pages.add(page.page_index)
        page_records.append(
            {
                "page_index": page.page_index,
                "width": page.width,
                "height": page.height,
                "dpi": page.dpi,
                "effective_dpi": page.effective_dpi,
                "is_scanned": page.is_scanned,
                "rotation_deg": page.rotation_deg,
                "source_ref": page.source_ref,
            }
        )
    (run_dir / "pages.json").write_text(
        json.dumps(
            {
                "schema_version": "1.0.0",
                "scan": {
                    "deskew": bool(getattr(load_config().scan, "deskew", False)),
                    "contrast": bool(getattr(load_config().scan, "contrast", True)),
                    "despeckle": bool(getattr(load_config().scan, "despeckle", True)),
                },
                "pages": sorted(page_records, key=lambda item: item["page_index"]),
            },
            indent=2,
        ),
        encoding="utf-8",
    )

    # pid.svg — self-contained visualisation of the extracted DEXPI model.
    render_metadata = {
        "run_id": run_id,
        "model": model,
        "engine": engine,
        "effort": effort,
        "total_tokens": total_tokens_from_summary(cost_summary),
        "timestamp": run_dir.name.split("_", 1)[0],
    }
    try:
        from diagex.extractors.dexpi_svg import write_svg as _write_dexpi_svg

        _write_dexpi_svg(
            graph,
            run_dir / "pid.svg",
            title=f"{stem} · {run_id}",
            metadata=render_metadata,
        )
    except Exception as exc:
        dexpi_issues.append(f"SVG render failed: {exc}")

    # pid.drawio — same graph rendered with diagrams.net "Process Engineering"
    # stencils (mxgraph.pid*). Editable in diagrams.net for review / cleanup.
    try:
        from diagex.extractors.dexpi_drawio import write_drawio as _write_drawio

        _write_drawio(
            graph,
            run_dir / "pid.drawio",
            title=f"{stem} · {run_id}",
            metadata=render_metadata,
        )
    except Exception as exc:
        dexpi_issues.append(f"drawio render failed: {exc}")

    # debug_report.md — scan-friendly textual dump for side-by-side PDF inspection.
    try:
        from diagex.extractors.debug_report import write_debug_report as _write_debug

        _write_debug(
            graph,
            run_dir / "debug_report.md",
            title=f"{stem} · {run_id}",
            metadata=render_metadata,
        )
    except Exception as exc:
        dexpi_issues.append(f"debug report render failed: {exc}")

    # cost.json — same shape as Phase 1.
    (run_dir / "cost.json").write_text(
        json.dumps(cost_summary, indent=2, sort_keys=True), encoding="utf-8"
    )

    # transcript.jsonl — one line per step across all pages.
    with (run_dir / "transcript.jsonl").open("w", encoding="utf-8") as f:
        for st in states:
            for ts in st.transcript:
                f.write(
                    json.dumps(
                        {
                            "page_index": st.page.page_index,
                            "step": ts.step,
                            "kind": ts.kind,
                            "payload": ts.payload,
                        }
                    )
                    + "\n"
                )

    # legend.json — exact pack the run used (audit).
    if legend_pack is not None:
        (run_dir / "legend.json").write_text(
            legend_pack.model_dump_json(indent=2), encoding="utf-8"
        )

    # result.json — compact summary.
    result_obj = {
        "schema_version": "0.1.0",
        "run_id": run_id,
        "diagram_stem": stem,
        "effort": effort,
        "model": model,
        "engine": engine,
        "stats": dexpi_stats,
        "dexpi_issues": dexpi_issues,
        "validation_issues": validation_issues,
        "cost": cost_summary,
        "wall_clock_s": float(cost_summary.get("wall_clock_s", 0.0)),
        "retries": int(cost_summary.get("retries", 0)),
        "tool_call_counts": dict(cost_summary.get("tool_call_counts", {})),
        "legend": {
            "source": legend_source_tag,
            "entry_count": len(legend_pack.entries) if legend_pack else 0,
        },
        "dexpi_json_path": str(dexpi_json_path) if dexpi_json_path else None,
        "per_page_status": {str(k): v for k, v in per_page_status.items()},
    }
    (run_dir / "result.json").write_text(json.dumps(result_obj, indent=2), encoding="utf-8")

    # confidence_report.html — printable, self-contained digest.
    report_target = (
        Path(confidence_report_path)
        if confidence_report_path
        else (run_dir / "confidence_report.html")
    )
    write_confidence_report(
        report_target,
        stem=stem,
        run_id=run_id,
        effort=effort,
        cost_summary=cost_summary,
        legend_source_tag=legend_source_tag,
        legend_entry_count=len(legend_pack.entries) if legend_pack else 0,
        dexpi_stats=dexpi_stats,
        dexpi_issues=dexpi_issues,
        validation_issues=validation_issues,
        graph=graph,
        per_page_status=per_page_status,
    )

    # index.md line.
    snippet = (
        f"dexpi={dexpi_json_path.name if dexpi_json_path else 'none'} "
        f"equipment={dexpi_stats.get('equipment_count', 0)} "
        f"valves={dexpi_stats.get('valve_count', 0)} "
        f"instruments={dexpi_stats.get('instrument_count', 0)}"
    )
    append_index(runs_root, run_id, f"extract-pid {stem}", snippet)


# ---------------------------------------------------------------------------
# Confidence report (HTML)
# ---------------------------------------------------------------------------


_REPORT_CSS = """
* { box-sizing: border-box; }
body { font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
       margin: 24px; color: #222; line-height: 1.45; }
h1, h2, h3 { font-family: ui-sans-serif, system-ui, sans-serif; }
h1 { margin: 0 0 6px 0; font-size: 22px; }
h2 { margin: 22px 0 8px 0; font-size: 16px; border-bottom: 1px solid #ccc; padding-bottom: 3px; }
h3 { margin: 12px 0 4px 0; font-size: 14px; }
.banner { background: #f4f6f8; padding: 10px 12px; border-left: 4px solid #2266cc;
          margin-bottom: 14px; }
.banner .kv { display: inline-block; margin-right: 18px; }
.banner .k { color: #556; font-weight: 600; }
table { border-collapse: collapse; width: auto; margin: 6px 0 12px 0; }
th, td { border: 1px solid #bbb; padding: 4px 10px; text-align: left; font-size: 13px;
         vertical-align: top; }
th { background: #eef; }
td.num { text-align: right; }
ul { margin: 4px 0 10px 20px; }
.empty { color: #888; font-style: italic; }
.section-count { color: #556; font-weight: normal; font-size: 13px; }
pre { background: #f8f8f8; padding: 6px; border: 1px solid #ddd;
      white-space: pre-wrap; word-break: break-all; font-size: 12px; margin: 4px 0; }
"""


def _h(s: Any) -> str:
    return html.escape("" if s is None else str(s))


def write_confidence_report(
    path: Path,
    *,
    stem: str,
    run_id: str,
    effort: str,
    cost_summary: dict,
    legend_source_tag: str,
    legend_entry_count: int,
    dexpi_stats: dict,
    dexpi_issues: list[str],
    validation_issues: list[dict],
    graph: ReconciledGraph,
    per_page_status: dict[int, str],
) -> None:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)

    parts: list[str] = []
    parts.append("<!doctype html><html><head><meta charset='utf-8'>")
    parts.append(f"<title>diagex P&ID report — {_h(stem)}</title>")
    parts.append(f"<style>{_REPORT_CSS}</style></head><body>")

    # Banner
    parts.append("<div class='banner'>")
    parts.append(f"<h1>P&amp;ID extraction — {_h(stem)}</h1>")
    parts.append(
        f"<div><span class='kv'><span class='k'>run:</span> {_h(run_id)}</span>"
        f"<span class='kv'><span class='k'>effort:</span> {_h(effort)}</span>"
        f"<span class='kv'><span class='k'>tokens:</span> "
        f"{format_tokens_millions(total_tokens_from_summary(cost_summary))}</span>"
        f"<span class='kv'><span class='k'>elapsed:</span> "
        f"{format_elapsed(cost_summary.get('wall_clock_s', 0.0))}</span>"
        f"<span class='kv'><span class='k'>legend:</span> {_h(legend_source_tag)} "
        f"({legend_entry_count})</span></div>"
    )
    parts.append("</div>")

    # Stats
    parts.append("<h2>Stats</h2>")
    parts.append("<table><tr><th>metric</th><th>value</th></tr>")
    for key in (
        "equipment_count",
        "valve_count",
        "instrument_count",
        "segment_count",
        "opc_count",
        "unclassified_count",
        "dropped_edges",
    ):
        parts.append(
            f"<tr><td>{_h(key)}</td><td class='num'>{_h(dexpi_stats.get(key, 0))}</td></tr>"
        )
    parts.append("</table>")

    # Validation issues
    parts.append(
        f"<h2>Validation issues <span class='section-count'>({len(validation_issues)})</span></h2>"
    )
    if not validation_issues:
        parts.append("<p class='empty'>none</p>")
    else:
        parts.append("<ul>")
        for iss in validation_issues:
            parts.append(
                f"<li><code>{_h(iss.get('path', ''))}</code>: {_h(iss.get('msg', ''))}</li>"
            )
        parts.append("</ul>")

    # DexpiBuilder issues (spec §7.2 step 7 — "offending annotations")
    parts.append(
        f"<h2>DexpiBuilder issues <span class='section-count'>({len(dexpi_issues)})</span></h2>"
    )
    if not dexpi_issues:
        parts.append("<p class='empty'>none</p>")
    else:
        parts.append("<ul>")
        for msg in dexpi_issues:
            parts.append(f"<li>{_h(msg)}</li>")
        parts.append("</ul>")

    # Reconciliation conflicts grouped by type.
    conflicts = list(getattr(graph, "conflicts", []) or [])
    parts.append(
        f"<h2>Reconciliation conflicts <span class='section-count'>({len(conflicts)})</span></h2>"
    )
    if not conflicts:
        parts.append("<p class='empty'>none</p>")
    else:
        by_type: dict[str, list[dict]] = {}
        for c in conflicts:
            t = str(c.get("type", "other"))
            by_type.setdefault(t, []).append(c)
        for t in (
            "iou_grey_zone",
            "ocr_flip_candidate",
            "unstitched_line_endpoint",
            "ambiguous_opc",
            "other",
        ):
            rows = by_type.get(t)
            if not rows:
                continue
            parts.append(f"<h3>{_h(t)} <span class='section-count'>({len(rows)})</span></h3>")
            parts.append("<ul>")
            for c in rows[:10]:
                arb = c.get("arbitration") if isinstance(c, dict) else None
                arb_badge = ""
                if isinstance(arb, dict):
                    verdict = arb.get("verdict") or arb.get("status") or "?"
                    arb_badge = f" <strong>[arbitration: {_h(verdict)}]</strong>"
                parts.append(f"<li>{arb_badge}<pre>{_h(json.dumps(c, sort_keys=True))}</pre></li>")
            if len(rows) > 10:
                parts.append(f"<li class='empty'>… {len(rows) - 10} more omitted</li>")
            parts.append("</ul>")
        # Any unrecognised types.
        unknown = {
            k: v
            for k, v in by_type.items()
            if k
            not in {
                "iou_grey_zone",
                "ocr_flip_candidate",
                "unstitched_line_endpoint",
                "ambiguous_opc",
                "other",
            }
        }
        for t, rows in unknown.items():
            parts.append(f"<h3>{_h(t)} <span class='section-count'>({len(rows)})</span></h3>")
            parts.append("<ul>")
            for c in rows[:10]:
                parts.append(f"<li><pre>{_h(json.dumps(c, sort_keys=True))}</pre></li>")
            parts.append("</ul>")

    # Per-page status table.
    parts.append("<h2>Per-page status</h2>")
    if not per_page_status:
        parts.append("<p class='empty'>no pages processed</p>")
    else:
        parts.append("<table><tr><th>page</th><th>status</th></tr>")
        for p in sorted(per_page_status.keys()):
            parts.append(
                f"<tr><td class='num'>{_h(p + 1)}</td><td>{_h(per_page_status[p])}</td></tr>"
            )
        parts.append("</table>")

    # Top 20 low-confidence annotations, grouped by kind (nodes only; edges have no label).
    low_nodes = [n for n in getattr(graph, "nodes", []) if n.confidence == "low"]
    low_nodes = sorted(
        low_nodes,
        key=lambda n: (n.kind, n.page_index, n.label),
    )
    parts.append(
        f"<h2>Low-confidence annotations <span class='section-count'>"
        f"(showing up to 20 of {len(low_nodes)})</span></h2>"
    )
    if not low_nodes:
        parts.append("<p class='empty'>none</p>")
    else:
        shown = low_nodes[:20]
        by_kind: dict[str, list] = {}
        for n in shown:
            by_kind.setdefault(n.kind, []).append(n)
        for kind in sorted(by_kind.keys()):
            rows = by_kind[kind]
            parts.append(f"<h3>{_h(kind)} <span class='section-count'>({len(rows)})</span></h3>")
            parts.append("<table><tr><th>page</th><th>label</th><th>bbox</th></tr>")
            for n in rows:
                bb = n.bbox_global
                bb_str = f"({bb.x},{bb.y}) {bb.w}x{bb.h}"
                parts.append(
                    f"<tr><td class='num'>{_h(n.page_index + 1)}</td>"
                    f"<td>{_h(n.label)}</td><td>{_h(bb_str)}</td></tr>"
                )
            parts.append("</table>")

    parts.append("</body></html>")
    path.write_text("".join(parts), encoding="utf-8")
