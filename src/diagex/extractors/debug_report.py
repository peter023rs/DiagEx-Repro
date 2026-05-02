"""Condensed textual debug report for a ReconciledGraph.

Purpose: a scan-friendly, monospace-aligned Markdown dump of every
extracted node and edge, laid out so a human can inspect it side-by-side
with the original PDF and spot omissions or mis-classifications at a
glance.

Public API (mirrors `dexpi_svg.py`):

    render_debug_report(graph, *, title="", metadata=None, show_coords=False) -> str
    write_debug_report(graph, path, *, title="", metadata=None, show_coords=False) -> Path
    render_graph_json_to_debug(graph_json_path, *, title="", show_coords=False) -> str

Output file: Markdown with fenced code blocks so alignment survives in
any viewer, including `diff`.
"""

from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterable

from diagex.vision.models import (
    BBox,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_LINE_TYPE_SHORT = {
    "process": "process",
    "signal_electric": "sig_elec",
    "signal_pneumatic": "sig_pneu",
    "instrument_capillary": "cap",
    "electrical_power": "elec",
    "other": "other",
    None: "??",
}

_ZONE_COLS = "ABCD"
_ZONE_ROWS = "1234"


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def render_debug_report(
    graph: ReconciledGraph,
    *,
    title: str = "",
    metadata: dict | None = None,
    show_coords: bool = False,
    edge_resolve_log_path: Path | None = None,
) -> str:
    """Render a ReconciledGraph as a condensed Markdown debug report."""
    md = metadata or {}
    parts: list[str] = []

    parts.append(_render_header(graph, title=title, metadata=md))
    parts.append(_render_summary(graph))

    nodes_by_page: dict[int, list[ReconciledNode]] = defaultdict(list)
    for n in graph.nodes:
        nodes_by_page[n.page_index].append(n)

    # Per-page envelope for the zone grid, so the CLI works without page dims.
    envelopes = {p: _page_envelope(ns) for p, ns in nodes_by_page.items()}

    for page_index in sorted(nodes_by_page.keys()):
        parts.append(
            _render_page_section(
                page_index=page_index,
                nodes=nodes_by_page[page_index],
                envelope=envelopes[page_index],
                show_coords=show_coords,
            )
        )

    parts.append(_render_edges(graph, show_coords=show_coords))
    parts.append(_render_adjacency(graph))
    parts.append(_render_conflicts(graph))
    parts.append(_render_edge_resolve_summary(edge_resolve_log_path))
    parts.append(_render_debug_flags(graph))

    return "\n".join(p for p in parts if p) + "\n"


def write_debug_report(
    graph: ReconciledGraph,
    path: Path,
    *,
    title: str = "",
    metadata: dict | None = None,
    show_coords: bool = False,
) -> Path:
    """Render `graph` and write the report to `path`. Returns the path."""
    path.parent.mkdir(parents=True, exist_ok=True)
    sibling_log = path.parent / "edge_resolve.jsonl"
    text = render_debug_report(
        graph,
        title=title,
        metadata=metadata,
        show_coords=show_coords,
        edge_resolve_log_path=sibling_log if sibling_log.exists() else None,
    )
    path.write_text(text, encoding="utf-8")
    return path


def render_graph_json_to_debug(
    graph_json_path: Path,
    *,
    title: str = "",
    show_coords: bool = False,
) -> str:
    """Load a graph.json from disk and render a debug report.

    Opportunistically harvests sibling result.json for the header banner,
    same pattern as `render_graph_json_to_svg`.
    """
    raw = json.loads(Path(graph_json_path).read_text(encoding="utf-8"))
    graph = ReconciledGraph.model_validate(raw)
    p = Path(graph_json_path)
    metadata = _harvest_run_metadata(p)
    sibling_log = p.parent / "edge_resolve.jsonl"
    return render_debug_report(
        graph,
        title=title or graph.source_path,
        metadata=metadata,
        show_coords=show_coords,
        edge_resolve_log_path=sibling_log if sibling_log.exists() else None,
    )


# ---------------------------------------------------------------------------
# Metadata harvest (mirrors dexpi_svg._harvest_run_metadata; duplicated by design)
# ---------------------------------------------------------------------------


def _harvest_run_metadata(graph_json_path: Path) -> dict:
    try:
        candidate = graph_json_path.with_name("result.json")
        if not candidate.exists():
            return {}
        r = json.loads(candidate.read_text(encoding="utf-8"))
        return {
            "run_id": r.get("run_id"),
            "model": r.get("model"),
            "effort": r.get("effort"),
            "total_usd": (r.get("cost") or {}).get("total_usd"),
            "timestamp": graph_json_path.parent.name.split("_", 1)[0],
        }
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Header + summary
# ---------------------------------------------------------------------------


def _render_header(graph: ReconciledGraph, *, title: str, metadata: dict) -> str:
    display_title = title or graph.source_path or "(untitled)"
    bits = [f"# P&ID debug report — {display_title}"]
    kv = []
    if metadata.get("run_id"):
        kv.append(f"run={metadata['run_id']}")
    if metadata.get("effort"):
        kv.append(f"effort={metadata['effort']}")
    if metadata.get("model"):
        kv.append(f"model={metadata['model']}")
    if metadata.get("total_usd") is not None:
        kv.append(f"cost=${float(metadata['total_usd']):.4f}")
    if metadata.get("timestamp"):
        kv.append(f"timestamp={metadata['timestamp']}")
    if kv:
        bits.append("")
        bits.append("> " + "  ·  ".join(kv))
    return "\n".join(bits)


def _render_summary(graph: ReconciledGraph) -> str:
    kinds = defaultdict(int)
    for n in graph.nodes:
        if n.kind == "equipment" and n.attributes.get("equipment_class") == "valve":
            kinds["valve"] += 1
        else:
            kinds[n.kind] += 1

    line_types = defaultdict(int)
    cross_sheet = 0
    for e in graph.edges:
        if e.cross_sheet:
            cross_sheet += 1
        line_types[e.line_type] += 1

    unsnapped = sum(1 for e in graph.edges if _has_flag(e, "UNSNAPPED"))
    loose = sum(1 for e in graph.edges if _has_flag(e, "INFERRED_LOOSE"))
    unclassified = sum(
        1 for n in graph.nodes
        if n.attributes.get("equipment_class") == "unclassified_equipment"
        or n.attributes.get("instrument_function") == "unclassified_instrument"
    )
    low_conf = sum(1 for n in graph.nodes if n.confidence == "low")

    conflict_tally = defaultdict(int)
    arbitrated = 0
    for c in graph.conflicts or []:
        conflict_tally[str(c.get("type", "other"))] += 1
        arb = c.get("arbitration") if isinstance(c, dict) else None
        if isinstance(arb, dict) and str(arb.get("status", "")) == "ok":
            arbitrated += 1

    lines = ["## Summary", "", "```"]
    lines.append(
        f"nodes:       {len(graph.nodes):<4d}"
        f"  (equipment {kinds['equipment']}, instrument {kinds['instrument']},"
        f" valve {kinds['valve']}, opc {kinds['opc']}, text/note {kinds['text'] + kinds['note']})"
    )
    et_bits = []
    for lt in ("process", "signal_electric", "signal_pneumatic",
               "instrument_capillary", "electrical_power", "other"):
        if line_types.get(lt):
            et_bits.append(f"{_LINE_TYPE_SHORT[lt]} {line_types[lt]}")
    if line_types.get(None):
        et_bits.append(f"?? {line_types[None]}")
    if cross_sheet:
        et_bits.append(f"cross_sheet {cross_sheet}")
    lines.append(
        f"edges:       {len(graph.edges):<4d}"
        + (f"  ({', '.join(et_bits)})" if et_bits else "")
    )
    lines.append(
        f"flags:       unsnapped={unsnapped}  loose={loose}"
        f"  unclassified={unclassified}  low_confidence={low_conf}"
    )
    conf_detail = (
        f"  ({arbitrated} arbitrated)" if arbitrated and graph.conflicts else ""
    )
    conf_type_tail = (
        "  [" + ", ".join(f"{k}={v}" for k, v in sorted(conflict_tally.items())) + "]"
        if conflict_tally else ""
    )
    lines.append(
        f"conflicts:   {len(graph.conflicts or [])}{conf_detail}{conf_type_tail}"
    )
    lines.append(
        f"dangling:    {len(graph.dangling_opcs or [])}    "
        f"per-page: {_fmt_per_page(graph.per_page_status)}"
    )
    lines.append("```")
    return "\n".join(lines)


def _fmt_per_page(status: dict[int, str]) -> str:
    if not status:
        return "(none)"
    return ", ".join(f"p{p + 1}={status[p]}" for p in sorted(status.keys()))


# ---------------------------------------------------------------------------
# Per-page section
# ---------------------------------------------------------------------------


def _render_page_section(
    *,
    page_index: int,
    nodes: list[ReconciledNode],
    envelope: tuple[int, int, int, int] | None,
    show_coords: bool,
) -> str:
    equipment = [
        n for n in nodes
        if n.kind == "equipment"
        and n.attributes.get("equipment_class") != "valve"
    ]
    valves = [
        n for n in nodes
        if n.kind == "equipment"
        and n.attributes.get("equipment_class") == "valve"
    ]
    instruments = [n for n in nodes if n.kind == "instrument"]
    opcs = [n for n in nodes if n.kind == "opc"]
    others = [n for n in nodes if n.kind in ("text", "note")]

    parts = [f"## Page {page_index + 1}"]

    if equipment:
        parts.append(
            _render_node_table(
                "Equipment", equipment, envelope, show_coords=show_coords,
                subkey="equipment_class",
            )
        )
    if instruments:
        parts.append(
            _render_node_table(
                "Instruments", instruments, envelope, show_coords=show_coords,
                subkey="instrument_function",
            )
        )
    if valves:
        parts.append(
            _render_node_table(
                "Valves", valves, envelope, show_coords=show_coords,
                subkey="valve_type",
            )
        )
    if opcs:
        parts.append(
            _render_node_table(
                "OPCs", opcs, envelope, show_coords=show_coords, subkey=None,
            )
        )
    if others:
        parts.append(
            _render_node_table(
                "Text/notes", others, envelope, show_coords=show_coords, subkey=None,
            )
        )
    return "\n\n".join(parts)


def _render_node_table(
    heading: str,
    nodes: list[ReconciledNode],
    envelope: tuple[int, int, int, int] | None,
    *,
    show_coords: bool,
    subkey: str | None,
) -> str:
    # Sort top-to-bottom, left-to-right.
    nodes_sorted = sorted(
        nodes,
        key=lambda n: (n.bbox_global.y, n.bbox_global.x, n.label or n.id),
    )

    rows: list[tuple[str, ...]] = []
    for n in nodes_sorted:
        zone = _page_zone(n.bbox_global, envelope)
        label = n.label.strip() or "--"
        sub = _kind_subtype(n, subkey=subkey)
        loop = n.attributes.get("loop_number") or ""
        conf = f"[{n.confidence}]"
        notes = _node_notes(n)
        coord_cell = (
            f"({n.bbox_global.x + n.bbox_global.w // 2},"
            f"{n.bbox_global.y + n.bbox_global.h // 2})"
            if show_coords else ""
        )
        rows.append((zone, coord_cell, label, sub, str(loop), conf, notes))

    header = ("zone", "xy", "label", "kind/subtype", "loop", "conf", "notes")
    if not show_coords:
        # Drop the xy column entirely.
        header = tuple(c for c in header if c != "xy")
        rows = [tuple(c for i, c in enumerate(r) if i != 1) for r in rows]

    body = _format_aligned_rows(header, rows)
    return f"### {heading} ({len(nodes)})\n\n```\n{body}\n```"


def _kind_subtype(n: ReconciledNode, *, subkey: str | None) -> str:
    """Compact kind/subtype cell."""
    if n.kind == "opc":
        direction = str(n.attributes.get("direction", "") or "?").lower()
        target = n.attributes.get("target_sheet")
        tail = f"→p{target}" if target else ""
        return f"opc/{direction}{tail}"
    if n.kind in ("text", "note"):
        return n.kind
    if subkey is None:
        return n.kind
    subclass = str(n.attributes.get(subkey, "") or "").strip()
    # Surface the secondary hint derived from the DEXPI registry (pumps,
    # compressors, HX, etc. carry a subtype_hint_attr that names the hint).
    from diagex.dexpi_schema import equipment_spec_for

    spec = equipment_spec_for(subclass)
    hint_key = spec.subtype_hint_attr if spec is not None else None
    hint = str(n.attributes.get(hint_key, "") or "").strip() if hint_key else ""
    if subclass and hint:
        return f"{n.kind}/{subclass}·{hint}"
    if subclass:
        return f"{n.kind}/{subclass}"
    return n.kind


def _node_notes(n: ReconciledNode) -> str:
    bits: list[str] = []
    if n.alternate_readings:
        alts = ", ".join(f"\"{a}\"" for a in n.alternate_readings[:3])
        bits.append(f"alt: {alts}")
    # Pull a quote out of source annotations if available (stored on attributes).
    quote = str(n.attributes.get("source_quote", "") or "").strip()
    if quote:
        truncated = quote if len(quote) <= 48 else quote[:45] + "..."
        bits.append(f'"{truncated}"')
    return "  ".join(bits)


# ---------------------------------------------------------------------------
# Edges
# ---------------------------------------------------------------------------


def _render_edges(graph: ReconciledGraph, *, show_coords: bool) -> str:
    by_page: dict[int, list[ReconciledEdge]] = defaultdict(list)
    cross: list[ReconciledEdge] = []
    for e in graph.edges:
        if e.cross_sheet:
            cross.append(e)
            continue
        pi = _edge_page_index(e, graph)
        by_page[pi].append(e)

    nodes_by_id = {n.id: n for n in graph.nodes}
    parts = ["## Edges"]

    for page_index in sorted(by_page.keys()):
        if page_index < 0:
            heading = f"### Unplaced ({len(by_page[page_index])})"
        else:
            heading = f"### Page {page_index + 1} ({len(by_page[page_index])})"
        body = _edge_rows(by_page[page_index], nodes_by_id, show_coords)
        parts.append(f"{heading}\n\n```\n{body}\n```")

    if cross:
        body = _edge_rows(cross, nodes_by_id, show_coords, cross_sheet=True)
        parts.append(f"### Cross-sheet ({len(cross)})\n\n```\n{body}\n```")

    return "\n\n".join(parts)


def _edge_rows(
    edges: list[ReconciledEdge],
    nodes_by_id: dict[str, ReconciledNode],
    show_coords: bool,
    *,
    cross_sheet: bool = False,
) -> str:
    # Sort by (source label, target label, id) for stable output.
    edges_sorted = sorted(
        edges,
        key=lambda e: (
            _node_display(e.from_node, nodes_by_id),
            _node_display(e.to_node, nodes_by_id),
            e.id,
        ),
    )
    # Only show the line-id column if at least one edge in this block has a tag.
    line_ids = [str(e.attributes.get("line_id", "") or "") for e in edges_sorted]
    show_line_id = any(line_ids)
    rows: list[tuple[str, ...]] = []
    for e, lid in zip(edges_sorted, line_ids):
        src = _node_display(e.from_node, nodes_by_id, with_page=cross_sheet)
        dst = _node_display(e.to_node, nodes_by_id, with_page=cross_sheet)
        arrow = "══cross══" if cross_sheet else f"──{_LINE_TYPE_SHORT.get(e.line_type, '??')}──▶"
        flags = _edge_flags(e)
        conf = f"[{e.confidence}]"
        if show_line_id:
            rows.append((f"{e.id[:10]}", src, arrow, dst, lid, flags, conf))
        else:
            rows.append((f"{e.id[:10]}", src, arrow, dst, flags, conf))
    if show_line_id:
        header = ("id", "from", "", "to", "line_id", "flags", "conf")
    else:
        header = ("id", "from", "", "to", "flags", "conf")
    return _format_aligned_rows(header, rows)


def _node_display(
    node_id: str,
    nodes_by_id: dict[str, ReconciledNode],
    *,
    with_page: bool = False,
) -> str:
    if not node_id:
        return "??"
    n = nodes_by_id.get(node_id)
    if n is None:
        return f"?{node_id[:6]}"
    label = n.label.strip() or f"?{node_id[:6]}"
    if with_page:
        return f"{label}@p{n.page_index + 1}"
    return label


def _edge_flags(e: ReconciledEdge) -> str:
    flags: list[str] = []
    snap_note = str(e.attributes.get("snap_note", "") or "")
    if "unsnappable" in snap_note:
        flags.append("UNSNAPPED")
    elif "inferred_loose" in snap_note:
        flags.append("INFERRED_LOOSE")
    if not e.from_node or not e.to_node:
        flags.append("DANGLING")
    return " ".join(flags)


def _has_flag(e: ReconciledEdge, flag: str) -> bool:
    return flag in _edge_flags(e).split()


def _edge_page_index(edge: ReconciledEdge, graph: ReconciledGraph) -> int:
    """Page index inferred from either endpoint; returns -1 when unknown."""
    for nid in (edge.from_node, edge.to_node):
        for n in graph.nodes:
            if n.id == nid:
                return n.page_index
    return -1


# ---------------------------------------------------------------------------
# Connection graph (adjacency view)
# ---------------------------------------------------------------------------


def _render_adjacency(graph: ReconciledGraph) -> str:
    nodes_by_id = {n.id: n for n in graph.nodes}
    out_edges: dict[str, list[ReconciledEdge]] = defaultdict(list)
    in_edges: dict[str, list[ReconciledEdge]] = defaultdict(list)
    for e in graph.edges:
        if e.from_node:
            out_edges[e.from_node].append(e)
        if e.to_node:
            in_edges[e.to_node].append(e)

    # Only list nodes that participate in at least one edge (leaves with
    # no connectivity are already in the per-page tables).
    connected_ids = set(out_edges.keys()) | set(in_edges.keys())
    if not connected_ids:
        return "## Connection graph\n\n```\n(no connected nodes)\n```"

    lines: list[str] = ["## Connection graph", "", "```"]
    display_order = sorted(
        connected_ids,
        key=lambda nid: (
            nodes_by_id.get(nid).page_index if nid in nodes_by_id else 999,
            (nodes_by_id.get(nid).label if nid in nodes_by_id else nid),
        ),
    )
    # Pre-compute display widths so arrows align.
    max_label = max(
        (len(_node_display(nid, nodes_by_id)) for nid in display_order), default=4
    )
    for nid in display_order:
        src = _node_display(nid, nodes_by_id).ljust(max_label)
        out_parts = [
            f"→ {_node_display(e.to_node, nodes_by_id)} "
            f"({_LINE_TYPE_SHORT.get(e.line_type, '??')})"
            + (" [xsheet]" if e.cross_sheet else "")
            for e in out_edges.get(nid, [])
        ]
        in_parts = [
            f"← {_node_display(e.from_node, nodes_by_id)} "
            f"({_LINE_TYPE_SHORT.get(e.line_type, '??')})"
            + (" [xsheet]" if e.cross_sheet else "")
            for e in in_edges.get(nid, [])
        ]
        outs = ", ".join(out_parts) if out_parts else "—"
        ins = ", ".join(in_parts) if in_parts else "—"
        lines.append(f"{src}   out: {outs}")
        lines.append(f"{' ' * max_label}    in:  {ins}")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Conflicts
# ---------------------------------------------------------------------------


def _render_conflicts(graph: ReconciledGraph) -> str:
    conflicts = graph.conflicts or []
    lines = [f"## Conflicts ({len(conflicts)})"]
    if not conflicts:
        lines.append("")
        lines.append("_none_")
        return "\n".join(lines)

    lines.append("")
    for c in conflicts:
        lines.append(_format_conflict(c))
    return "\n".join(lines)


def _format_conflict(c: dict) -> str:
    ctype = str(c.get("type", "other"))
    page = c.get("page_index")
    page_tag = f"p{int(page) + 1}" if isinstance(page, int) else ""
    head_bits = [f"- **{ctype}**"]
    if page_tag:
        head_bits.append(page_tag)
    labels = c.get("labels") or []
    if labels:
        head_bits.append(" vs ".join(f"`{str(x)}`" for x in labels))
    iou = c.get("iou")
    if iou is not None:
        head_bits.append(f"iou={iou}")
    if ctype == "unstitched_line_endpoint":
        head_bits.append(f"at ({c.get('x')},{c.get('y')})")
        if c.get("line_type"):
            head_bits.append(c["line_type"])
    if ctype == "ambiguous_opc":
        norm = c.get("normalised")
        if norm:
            head_bits.append(f"normalised=`{norm}`")
        node_ids = c.get("node_ids") or []
        if node_ids:
            head_bits.append(f"{len(node_ids)} candidates")
    head = "  ".join(head_bits)

    arb = c.get("arbitration") if isinstance(c, dict) else None
    tail = ""
    if isinstance(arb, dict):
        status = str(arb.get("status", "?"))
        verdict = arb.get("verdict")
        chosen = arb.get("chosen_label") or arb.get("chosen_index")
        arb_bits = [f"status={status}"]
        if verdict is not None:
            arb_bits.append(f"verdict={verdict}")
        if chosen is not None:
            arb_bits.append(f"chosen={chosen}")
        if arb.get("detail"):
            arb_bits.append(f"detail={arb['detail']}")
        tail = f"\n  → arbitration: {'  '.join(arb_bits)}"
    return head + tail


# ---------------------------------------------------------------------------
# Edge-resolve summary
# ---------------------------------------------------------------------------


def _render_edge_resolve_summary(log_path: Path | None) -> str:
    """Aggregate a runs/<id>/edge_resolve.jsonl log into a Markdown section.

    Returns an empty string if there is no log file (so the section is silently
    skipped on runs where the adaptive zoom pass was disabled or had nothing
    to do).
    """
    if log_path is None:
        return ""
    try:
        text = log_path.read_text(encoding="utf-8")
    except OSError:
        return ""
    if not text.strip():
        return ""

    records: list[dict] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    if not records:
        return ""

    verdict_counts: dict[str, int] = defaultdict(int)
    source_counts: dict[str, int] = defaultdict(int)
    total_steps = 0
    total_new_annos = 0
    for r in records:
        verdict_counts[str(r.get("verdict", "?"))] += 1
        source_counts[str(r.get("source_kind", "?"))] += 1
        total_steps += int(r.get("steps", 0) or 0)
        total_new_annos += len(r.get("new_annotation_ids") or [])

    lines = ["## Edge resolve summary", "", "```"]
    lines.append(f"targets:     {len(records)}")
    if source_counts:
        bits = ", ".join(f"{k}={v}" for k, v in sorted(source_counts.items()))
        lines.append(f"by source:   {bits}")
    if verdict_counts:
        bits = ", ".join(f"{k}={v}" for k, v in sorted(verdict_counts.items()))
        lines.append(f"verdicts:    {bits}")
    lines.append(f"new annos:   {total_new_annos}")
    lines.append(f"total steps: {total_steps}")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Debug flags section
# ---------------------------------------------------------------------------


def _render_debug_flags(graph: ReconciledGraph) -> str:
    nodes_by_id = {n.id: n for n in graph.nodes}
    unsnapped = [e for e in graph.edges if _has_flag(e, "UNSNAPPED")]
    loose = [e for e in graph.edges if _has_flag(e, "INFERRED_LOOSE")]
    low_conf_nodes = [n for n in graph.nodes if n.confidence == "low"]
    unclassified = [
        n for n in graph.nodes
        if n.attributes.get("equipment_class") == "unclassified_equipment"
        or n.attributes.get("instrument_function") == "unclassified_instrument"
    ]
    lines = ["## Debugging flags", "", "```"]

    def _edge_refs(edges: list[ReconciledEdge]) -> str:
        if not edges:
            return "—"
        return ", ".join(e.id[:10] for e in edges[:10]) + (
            f"  (+{len(edges) - 10} more)" if len(edges) > 10 else ""
        )

    def _node_refs(nodes: list[ReconciledNode]) -> str:
        if not nodes:
            return "—"
        pieces = []
        for n in nodes[:10]:
            label = n.label.strip() or f"?{n.id[:6]}"
            pieces.append(f"{label}@p{n.page_index + 1}")
        tail = f"  (+{len(nodes) - 10} more)" if len(nodes) > 10 else ""
        return ", ".join(pieces) + tail

    lines.append(f"Unsnapped edges ({len(unsnapped)}):       {_edge_refs(unsnapped)}")
    lines.append(f"Loose-snap edges ({len(loose)}):      {_edge_refs(loose)}")
    lines.append(f"Low-confidence nodes ({len(low_conf_nodes)}):  {_node_refs(low_conf_nodes)}")
    lines.append(f"Unclassified nodes ({len(unclassified)}):    {_node_refs(unclassified)}")
    dangling = graph.dangling_opcs or []
    if dangling:
        dangling_refs = ", ".join(
            f"{str(d.get('opc_label') or '?')[:16]}@p{int(d.get('page_index', -1)) + 1}"
            for d in dangling[:10]
        )
        lines.append(f"Dangling OPCs ({len(dangling)}):         {dangling_refs}")
    else:
        lines.append(f"Dangling OPCs (0):         —")
    lines.append("```")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Geometry and formatting helpers
# ---------------------------------------------------------------------------


def _page_envelope(nodes: list[ReconciledNode]) -> tuple[int, int, int, int] | None:
    if not nodes:
        return None
    xs = [n.bbox_global.x for n in nodes] + [n.bbox_global.x + n.bbox_global.w for n in nodes]
    ys = [n.bbox_global.y for n in nodes] + [n.bbox_global.y + n.bbox_global.h for n in nodes]
    return (min(xs), min(ys), max(xs), max(ys))


def _page_zone(
    bbox: BBox, envelope: tuple[int, int, int, int] | None
) -> str:
    """Map bbox centre to a 4×4 zone label (A1–D4)."""
    if envelope is None:
        return "--"
    x_min, y_min, x_max, y_max = envelope
    cx = bbox.x + bbox.w / 2
    cy = bbox.y + bbox.h / 2
    w = max(1, x_max - x_min)
    h = max(1, y_max - y_min)
    col_idx = min(3, max(0, int((cx - x_min) / w * 4)))
    row_idx = min(3, max(0, int((cy - y_min) / h * 4)))
    return f"{_ZONE_COLS[col_idx]}{_ZONE_ROWS[row_idx]}"


def _format_aligned_rows(
    header: Iterable[str], rows: Iterable[Iterable[Any]]
) -> str:
    """Pretty-print a table with space-padded columns. Empty header cells are dropped."""
    header = [str(h) for h in header]
    rows = [[str(c) for c in r] for r in rows]
    if not rows:
        return "(none)"
    widths = [len(h) for h in header]
    for r in rows:
        for i, cell in enumerate(r):
            if i < len(widths):
                widths[i] = max(widths[i], len(cell))

    def _line(cells: list[str]) -> str:
        return "  ".join(c.ljust(widths[i]) for i, c in enumerate(cells)).rstrip()

    lines = [_line(header)]
    lines.append(_line(["-" * w for w in widths]))
    for r in rows:
        lines.append(_line(r))
    return "\n".join(lines)
