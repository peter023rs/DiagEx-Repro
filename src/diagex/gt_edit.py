"""Ground-truth correction CLI — `diagex gt edit`.

Walks a fixture's `graph.bootstrap.json` entity-by-entity, shows a PDF crop
around each node, prompts the rater for keep/revise/drop/skip/add-missing,
and emits `graph.truth.json` + `graph.truth.history.json`. Append-only history
gives crash-safe resume.

Design: docs/correction-ui.md. Bootstrap-then-correct rationale: plan §4.2.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Optional, Protocol

import pymupdf
from pydantic import ValidationError

from diagex.config import load_config
from diagex.vision.models import (
    BBox, Confidence, Kind, LineType, ReconciledEdge, ReconciledGraph, ReconciledNode,
)


_LINE_TYPES: tuple[str, ...] = (
    "process",
    "signal_electric",
    "signal_pneumatic",
    "instrument_capillary",
    "electrical_power",
    "other",
)


# ---------------------------------------------------------------------------
# Prompter abstraction (lets tests script the interactive surface)
# ---------------------------------------------------------------------------


class Prompter(Protocol):
    def action(self, choices: list[str], default: str) -> str: ...
    def text(self, prompt: str, default: Optional[str] = None) -> str: ...
    def confirm(self, prompt: str, default: bool = True) -> bool: ...
    def int_(self, prompt: str, default: Optional[int] = None) -> int: ...
    def message(self, text: str) -> None: ...


class ConsolePrompter:
    """Production prompter — uses `rich.prompt`. Keeps output on stderr so stdout
    stays clean for scripts that read the CLI's final report."""

    def __init__(self) -> None:
        from rich.console import Console
        self._console = Console(stderr=True)

    def action(self, choices: list[str], default: str) -> str:
        from rich.prompt import Prompt
        return Prompt.ask(
            f"[{'/'.join(choices)}]",
            choices=choices,
            default=default,
            console=self._console,
            show_choices=False,
        )

    def text(self, prompt: str, default: Optional[str] = None) -> str:
        from rich.prompt import Prompt
        return Prompt.ask(prompt, default=default or "", console=self._console)

    def confirm(self, prompt: str, default: bool = True) -> bool:
        from rich.prompt import Confirm
        return Confirm.ask(prompt, default=default, console=self._console)

    def int_(self, prompt: str, default: Optional[int] = None) -> int:
        from rich.prompt import IntPrompt
        return IntPrompt.ask(prompt, default=default, console=self._console)

    def message(self, text: str) -> None:
        self._console.print(text)


# ---------------------------------------------------------------------------
# File / render helpers
# ---------------------------------------------------------------------------


def _render_dpi_for(pdf_path: Path) -> float:
    """Replicate `src/diagex/vision/loader.py:_adaptive_dpi` without importing.

    bbox_global in graph.bootstrap.json is in page-pixel space at this DPI.
    """
    cfg = load_config()
    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc[0]
        pw, ph = float(page.rect.width), float(page.rect.height)
    finally:
        doc.close()
    max_side = max(pw, ph)
    if max_side <= 0:
        return float(cfg.tiling.target_dpi)
    max_dpi = cfg.tiling.max_page_dim_px * 72.0 / max_side
    return float(min(cfg.tiling.target_dpi, max_dpi))


def _render_crop(
    pdf_path: Path,
    page_index: int,
    bbox_px: BBox,
    base_dpi: float,
    crop_pad_px: int,
    out_path: Path,
    render_dpi: int = 150,
) -> None:
    """Render the crop surrounding `bbox_px` at `render_dpi` and write PNG."""
    doc = pymupdf.open(str(pdf_path))
    try:
        page = doc[page_index]
        # px → pt conversion using the base_dpi the bootstrap rendered at.
        scale_pt = 72.0 / base_dpi
        x0 = max(0.0, (bbox_px.x - crop_pad_px) * scale_pt)
        y0 = max(0.0, (bbox_px.y - crop_pad_px) * scale_pt)
        x1 = min(float(page.rect.width),  (bbox_px.x + bbox_px.w + crop_pad_px) * scale_pt)
        y1 = min(float(page.rect.height), (bbox_px.y + bbox_px.h + crop_pad_px) * scale_pt)
        clip = pymupdf.Rect(x0, y0, x1, y1)
        pix = page.get_pixmap(clip=clip, dpi=render_dpi)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        pix.save(str(out_path))
    finally:
        doc.close()


def _open_in_viewer(path: Path) -> None:
    """Best-effort: open the rendered crop in the OS image viewer.

    Silently skips in headless / CI environments. Failures are tolerated — the
    rater can always open the file path printed on screen by hand.
    """
    if os.environ.get("DIAGEX_GT_EDIT_NO_OPEN"):
        return
    try:
        if sys.platform == "darwin":
            subprocess.Popen(["open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        elif sys.platform == "win32":
            os.startfile(str(path))  # type: ignore[attr-defined]
        elif shutil.which("xdg-open"):
            subprocess.Popen(["xdg-open", str(path)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Session state + history
# ---------------------------------------------------------------------------


@dataclass
class EditSession:
    stem: str
    pdf_path: Path
    base_dpi: float
    graph: ReconciledGraph                         # mutated in place
    history: dict[str, Any]                        # JSON-serialisable audit log
    fixture_dir: Path
    bootstrap_path: Path
    truth_path: Path
    history_path: Path
    pending_skipped: list[str] = field(default_factory=list)
    pending_skipped_edges: list[str] = field(default_factory=list)


def _new_history(stem: str, bootstrap_path: Path, rater: str) -> dict[str, Any]:
    return {
        "stem": stem,
        "bootstrap_path": str(bootstrap_path),
        "rater": rater,
        "started_at": _now(),
        "completed_at": None,
        "actions": [],
        "summary": None,
    }


def _now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _write_history(session: EditSession) -> None:
    session.history_path.write_text(json.dumps(session.history, indent=2, default=str))


def _append_action(session: EditSession, action: dict[str, Any]) -> None:
    action = {"ts": _now(), **action}
    session.history["actions"].append(action)
    _write_history(session)


# ---------------------------------------------------------------------------
# Action dispatch
# ---------------------------------------------------------------------------


def _node_by_id(graph: ReconciledGraph, nid: str) -> Optional[ReconciledNode]:
    for n in graph.nodes:
        if n.id == nid:
            return n
    return None


def _describe(node: ReconciledNode) -> str:
    cls = (node.attributes or {}).get("equipment_class") or "n/a"
    bb = node.bbox_global
    arb = (node.attributes or {}).get("arbitration") or "-"
    return (
        f"{node.id}   {node.kind} / {cls}\n"
        f"  label      : {node.label!r}\n"
        f"  bbox px    : ({bb.x}, {bb.y}, {bb.w}x{bb.h})  page {node.page_index}\n"
        f"  confidence : {node.confidence}   arbitration: {arb}"
    )


def _do_keep(session: EditSession, node: ReconciledNode) -> None:
    _append_action(session, {"op": "keep", "node_id": node.id, "label": node.label})


def _do_revise(session: EditSession, node: ReconciledNode, prompter: Prompter) -> None:
    before = {
        "label": node.label,
        "kind": node.kind,
        "equipment_class": (node.attributes or {}).get("equipment_class"),
    }
    new_label = prompter.text("  new label", default=node.label).strip()
    new_kind = prompter.text("  new kind", default=node.kind).strip() or node.kind
    new_class = prompter.text(
        "  new equipment_class",
        default=before["equipment_class"] or "",
    ).strip()
    reason = prompter.text("  reason (optional)", default="").strip()

    node.label = new_label or node.label
    node.kind = new_kind  # type: ignore[assignment]
    attrs = dict(node.attributes or {})
    if new_class:
        attrs["equipment_class"] = new_class
    node.attributes = attrs

    _append_action(
        session,
        {
            "op": "revise",
            "node_id": node.id,
            "before": before,
            "after": {"label": node.label, "kind": node.kind, "equipment_class": new_class or before["equipment_class"]},
            "reason": reason or None,
        },
    )


def _do_drop(session: EditSession, node: ReconciledNode, prompter: Prompter) -> None:
    reason = prompter.text("  reason for drop (optional)", default="").strip()
    # Mark for drop; the actual list-removal happens at save time so undo is clean.
    attrs = dict(node.attributes or {})
    attrs["gt_drop"] = True
    node.attributes = attrs
    _append_action(
        session,
        {
            "op": "drop",
            "node_id": node.id,
            "label": node.label,
            "reason": reason or None,
        },
    )


def _do_skip(session: EditSession, node: ReconciledNode) -> None:
    session.pending_skipped.append(node.id)
    _append_action(session, {"op": "skip", "node_id": node.id, "label": node.label})


def _do_add_missing(
    session: EditSession,
    current_node: ReconciledNode,
    prompter: Prompter,
) -> None:
    """Coord entry in PDF points (what Acrobat rulers show); converted to page-pixel."""
    label = prompter.text("  label", default="").strip()
    kind = prompter.text("  kind", default="equipment").strip() or "equipment"
    eq_class = prompter.text("  equipment_class", default="").strip()
    page_index = prompter.int_("  page_index", default=current_node.page_index)
    x_pt = prompter.int_("  bbox x (PDF pt, top-left)", default=0)
    y_pt = prompter.int_("  bbox y (PDF pt, top-left)", default=0)
    w_pt = prompter.int_("  bbox width (PDF pt)", default=40)
    h_pt = prompter.int_("  bbox height (PDF pt)", default=40)
    conf_text = prompter.text("  confidence [high/medium/low]", default="high").strip() or "high"
    if conf_text not in ("high", "medium", "low"):
        conf_text = "high"

    # Convert PDF pt → page-pixel using the fixture's base DPI.
    scale_px = session.base_dpi / 72.0
    bbox = BBox(
        x=int(round(x_pt * scale_px)),
        y=int(round(y_pt * scale_px)),
        w=max(1, int(round(w_pt * scale_px))),
        h=max(1, int(round(h_pt * scale_px))),
    )
    attrs: dict[str, Any] = {"gt_added": True}
    if eq_class:
        attrs["equipment_class"] = eq_class

    new_id = f"n-{uuid.uuid4().hex[:8]}"
    new_node = ReconciledNode(
        id=new_id,
        kind=kind,  # type: ignore[arg-type]
        label=label or "unlabelled",
        bbox_global=bbox,
        page_index=page_index,
        attributes=attrs,
        confidence=conf_text,  # type: ignore[arg-type]
    )
    session.graph.nodes.append(new_node)
    _append_action(
        session,
        {
            "op": "add",
            "new_node": {
                "id": new_id,
                "kind": kind,
                "label": new_node.label,
                "bbox_global": bbox.model_dump(),
                "page_index": page_index,
                "attributes": attrs,
                "confidence": conf_text,
            },
        },
    )


# ---------------------------------------------------------------------------
# Edge action dispatch
# ---------------------------------------------------------------------------


def _edge_by_id(graph: ReconciledGraph, eid: str) -> Optional[ReconciledEdge]:
    for e in graph.edges:
        if e.id == eid:
            return e
    return None


def _edge_crop_bbox(
    edge: ReconciledEdge, graph: ReconciledGraph,
) -> tuple[Optional[BBox], int]:
    """Enclosing bbox spanning both endpoints + polyline. (None, 0) if endpoints
    are missing from the graph (shouldn't happen, but defensive)."""
    from_n = _node_by_id(graph, edge.from_node)
    to_n = _node_by_id(graph, edge.to_node)
    if from_n is None or to_n is None:
        return None, 0
    xs: list[int] = []
    ys: list[int] = []
    for n in (from_n, to_n):
        xs += [n.bbox_global.x, n.bbox_global.x + n.bbox_global.w]
        ys += [n.bbox_global.y, n.bbox_global.y + n.bbox_global.h]
    for px, py in edge.polyline_global or []:
        xs.append(int(px))
        ys.append(int(py))
    x0, x1 = min(xs), max(xs)
    y0, y1 = min(ys), max(ys)
    page_index = from_n.page_index
    return BBox(x=x0, y=y0, w=max(1, x1 - x0), h=max(1, y1 - y0)), page_index


def _describe_edge(edge: ReconciledEdge, graph: ReconciledGraph) -> str:
    from_n = _node_by_id(graph, edge.from_node)
    to_n = _node_by_id(graph, edge.to_node)
    fl = f"{from_n.label!r} ({edge.from_node})" if from_n else edge.from_node
    tl = f"{to_n.label!r} ({edge.to_node})" if to_n else edge.to_node
    lt = edge.line_type or "n/a"
    pts = len(edge.polyline_global or [])
    return (
        f"{edge.id}   line_type={lt}\n"
        f"  from   : {fl}\n"
        f"  to     : {tl}\n"
        f"  polyline points : {pts}   confidence : {edge.confidence}"
    )


def _resolve_endpoint(
    graph: ReconciledGraph, query: str, prompter: Prompter,
) -> Optional[str]:
    """Resolve a typed endpoint reference to a node id. Accepts:

    - exact node id (e.g. `n-abc12345`)
    - exact label match (case-insensitive)
    - case-insensitive label substring → unique match
    - case-insensitive label substring with multiple matches → pick by index

    Returns None if nothing matched (caller re-prompts).
    """
    q = (query or "").strip()
    if not q:
        return None
    for n in graph.nodes:
        if n.id == q:
            return n.id
    qup = q.upper()
    exact = [n for n in graph.nodes if (n.label or "").strip().upper() == qup]
    if len(exact) == 1:
        return exact[0].id
    if len(exact) > 1:
        prompter.message(f"  multiple exact matches for label {q!r}:")
        for i, n in enumerate(exact):
            prompter.message(f"    [{i}] {n.label} ({n.id}) — {n.kind}")
        idx = prompter.int_("  pick index", default=0)
        return exact[idx].id if 0 <= idx < len(exact) else None
    subs = [n for n in graph.nodes if qup in (n.label or "").upper()]
    if len(subs) == 1:
        return subs[0].id
    if len(subs) > 1:
        prompter.message(f"  multiple substring matches for {q!r}:")
        for i, n in enumerate(subs[:20]):
            prompter.message(f"    [{i}] {n.label} ({n.id}) — {n.kind}")
        if len(subs) > 20:
            prompter.message(f"    … {len(subs) - 20} more (refine your query)")
        idx = prompter.int_("  pick index", default=0)
        return subs[idx].id if 0 <= idx < len(subs) else None
    return None


def _do_edge_keep(session: EditSession, edge: ReconciledEdge) -> None:
    _append_action(session, {"op": "edge_keep", "edge_id": edge.id})


def _do_edge_revise(
    session: EditSession, edge: ReconciledEdge, prompter: Prompter,
) -> None:
    before = {
        "from_node": edge.from_node,
        "to_node": edge.to_node,
        "line_type": edge.line_type,
    }
    new_from_q = prompter.text("  new from-node (Enter to keep)", default="").strip()
    new_to_q = prompter.text("  new to-node (Enter to keep)", default="").strip()
    new_lt = prompter.text(
        f"  new line_type [{'/'.join(_LINE_TYPES)}]",
        default=str(edge.line_type or "process"),
    ).strip() or (edge.line_type or "process")
    if new_lt not in _LINE_TYPES:
        prompter.message(f"  unknown line_type {new_lt!r}; keeping {edge.line_type!r}")
        new_lt = edge.line_type or "process"
    reason = prompter.text("  reason (optional)", default="").strip()

    new_from = (
        _resolve_endpoint(session.graph, new_from_q, prompter) if new_from_q else edge.from_node
    )
    new_to = (
        _resolve_endpoint(session.graph, new_to_q, prompter) if new_to_q else edge.to_node
    )
    if new_from is None or new_to is None:
        prompter.message("  endpoint resolution failed; revise aborted")
        return

    edge.from_node = new_from
    edge.to_node = new_to
    edge.line_type = new_lt  # type: ignore[assignment]

    _append_action(session, {
        "op": "edge_revise",
        "edge_id": edge.id,
        "before": before,
        "after": {"from_node": new_from, "to_node": new_to, "line_type": new_lt},
        "reason": reason or None,
    })


def _do_edge_drop(
    session: EditSession, edge: ReconciledEdge, prompter: Prompter,
) -> None:
    reason = prompter.text("  reason for drop (optional)", default="").strip()
    attrs = dict(edge.attributes or {})
    attrs["gt_drop"] = True
    edge.attributes = attrs
    _append_action(session, {
        "op": "edge_drop",
        "edge_id": edge.id,
        "from_node": edge.from_node,
        "to_node": edge.to_node,
        "reason": reason or None,
    })


def _do_edge_skip(session: EditSession, edge: ReconciledEdge) -> None:
    session.pending_skipped_edges.append(edge.id)
    _append_action(session, {"op": "edge_skip", "edge_id": edge.id})


def _do_edge_add(session: EditSession, prompter: Prompter) -> Optional[str]:
    """Pick two endpoints by label/id, set line_type, optional polyline skipped.

    Returns the new edge id, or None if the rater bailed out of the picker.
    """
    from_q = prompter.text("  from-node label or id", default="").strip()
    if not from_q:
        prompter.message("  add aborted (empty from-node)")
        return None
    from_id = _resolve_endpoint(session.graph, from_q, prompter)
    if from_id is None:
        prompter.message(f"  no node matched {from_q!r}; add aborted")
        return None
    to_q = prompter.text("  to-node label or id", default="").strip()
    if not to_q:
        prompter.message("  add aborted (empty to-node)")
        return None
    to_id = _resolve_endpoint(session.graph, to_q, prompter)
    if to_id is None:
        prompter.message(f"  no node matched {to_q!r}; add aborted")
        return None
    if from_id == to_id:
        prompter.message("  self-loop rejected")
        return None
    lt = prompter.text(
        f"  line_type [{'/'.join(_LINE_TYPES)}]", default="process",
    ).strip() or "process"
    if lt not in _LINE_TYPES:
        prompter.message(f"  unknown line_type {lt!r}; defaulting to 'process'")
        lt = "process"
    conf_text = prompter.text(
        "  confidence [high/medium/low]", default="high",
    ).strip() or "high"
    if conf_text not in ("high", "medium", "low"):
        conf_text = "high"

    new_id = f"e-{uuid.uuid4().hex[:8]}"
    new_edge = ReconciledEdge(
        id=new_id,
        from_node=from_id,
        to_node=to_id,
        line_type=lt,  # type: ignore[arg-type]
        polyline_global=[],
        confidence=conf_text,  # type: ignore[arg-type]
        attributes={"gt_added": True},
    )
    session.graph.edges.append(new_edge)
    _append_action(session, {
        "op": "edge_add",
        "new_edge": {
            "id": new_id,
            "from_node": from_id,
            "to_node": to_id,
            "line_type": lt,
            "confidence": conf_text,
            "attributes": {"gt_added": True},
        },
    })
    return new_id


def _do_undo(session: EditSession) -> Optional[str]:
    """Pop the last action and reverse its effect. Returns a description or None
    if there's nothing to undo."""
    actions = session.history["actions"]
    if not actions:
        return None
    last = actions.pop()
    op = last.get("op")
    if op == "keep" or op == "skip":
        if op == "skip" and last.get("node_id") in session.pending_skipped:
            session.pending_skipped.remove(last["node_id"])
        _write_history(session)
        return f"undid {op} on {last.get('node_id')}"
    if op == "revise":
        n = _node_by_id(session.graph, last.get("node_id"))
        if n is not None:
            before = last.get("before") or {}
            n.label = before.get("label", n.label)
            if before.get("kind"):
                n.kind = before["kind"]
            attrs = dict(n.attributes or {})
            if before.get("equipment_class"):
                attrs["equipment_class"] = before["equipment_class"]
            elif "equipment_class" in attrs and last.get("after", {}).get("equipment_class"):
                # the revise added a class where there was none; remove it
                attrs.pop("equipment_class", None)
            n.attributes = attrs
        _write_history(session)
        return f"undid revise on {last.get('node_id')}"
    if op == "drop":
        n = _node_by_id(session.graph, last.get("node_id"))
        if n is not None:
            attrs = dict(n.attributes or {})
            attrs.pop("gt_drop", None)
            n.attributes = attrs
        _write_history(session)
        return f"undid drop on {last.get('node_id')}"
    if op == "add":
        nid = (last.get("new_node") or {}).get("id")
        session.graph.nodes[:] = [n for n in session.graph.nodes if n.id != nid]
        _write_history(session)
        return f"undid add of {nid}"
    if op == "edge_keep":
        _write_history(session)
        return f"undid edge_keep on {last.get('edge_id')}"
    if op == "edge_skip":
        eid = last.get("edge_id")
        if eid in session.pending_skipped_edges:
            session.pending_skipped_edges.remove(eid)
        _write_history(session)
        return f"undid edge_skip on {eid}"
    if op == "edge_revise":
        e = _edge_by_id(session.graph, last.get("edge_id"))
        if e is not None:
            before = last.get("before") or {}
            if before.get("from_node"):
                e.from_node = before["from_node"]
            if before.get("to_node"):
                e.to_node = before["to_node"]
            if "line_type" in before:
                e.line_type = before["line_type"]
        _write_history(session)
        return f"undid edge_revise on {last.get('edge_id')}"
    if op == "edge_drop":
        e = _edge_by_id(session.graph, last.get("edge_id"))
        if e is not None:
            attrs = dict(e.attributes or {})
            attrs.pop("gt_drop", None)
            e.attributes = attrs
        _write_history(session)
        return f"undid edge_drop on {last.get('edge_id')}"
    if op == "edge_add":
        eid = (last.get("new_edge") or {}).get("id")
        session.graph.edges[:] = [e for e in session.graph.edges if e.id != eid]
        _write_history(session)
        return f"undid edge_add of {eid}"
    # Unknown op — put it back
    actions.append(last)
    _write_history(session)
    return None


# ---------------------------------------------------------------------------
# Top-level orchestrator
# ---------------------------------------------------------------------------


def run_edit(
    fixture_dir: Path,
    *,
    prompter: Optional[Prompter] = None,
    viewer: Optional[Callable[[Path], None]] = None,
    render_dpi: int = 150,
    crop_pad_px: int = 80,
    skip_confirmed: bool = False,
    rater: str = "",
    resume: Optional[bool] = None,
) -> dict[str, Any]:
    """Run the interactive correction loop and return the final summary dict.

    Non-interactive callers (tests) must pass a `Prompter`. `viewer` defaults to
    the platform image-viewer shim; tests should pass a no-op.
    """
    prompter = prompter or ConsolePrompter()
    viewer = viewer or _open_in_viewer

    fixture_dir = Path(fixture_dir).resolve()
    stem = fixture_dir.name
    # Prefer graph.bootstrap_v2.json (post-VIA correction) when present; the
    # original graph.bootstrap.json is the seed for the VIA pass and stays
    # on disk for retention reporting.
    v2_path = fixture_dir / "graph.bootstrap_v2.json"
    bootstrap_path = v2_path if v2_path.exists() else fixture_dir / "graph.bootstrap.json"
    truth_path = fixture_dir / "graph.truth.json"
    history_path = fixture_dir / "graph.truth.history.json"
    pdf_path = Path(f"tests/p-ids-public/{stem}.pdf")
    if not pdf_path.is_absolute():
        pdf_path = fixture_dir.parents[1].parent / "tests" / "p-ids-public" / f"{stem}.pdf"

    if not bootstrap_path.exists():
        raise FileNotFoundError(
            f"{bootstrap_path} — run `diagex extract-pid` first "
            f"(or, after a VIA correction pass, `scripts/via_to_bootstrap_v2.py`)"
        )
    if not pdf_path.exists():
        raise FileNotFoundError(f"source PDF not found at {pdf_path}")

    bootstrap_graph = ReconciledGraph.model_validate_json(bootstrap_path.read_text())

    # Resume logic: if history exists, offer to continue.
    existing_history: Optional[dict[str, Any]] = None
    if history_path.exists():
        try:
            existing_history = json.loads(history_path.read_text())
        except json.JSONDecodeError:
            existing_history = None

    if existing_history:
        should_resume = resume
        if should_resume is None:
            prompter.message(
                f"Found existing history with {len(existing_history.get('actions') or [])} actions."
            )
            should_resume = prompter.confirm("Resume from checkpoint?", default=True)
        if should_resume:
            graph = bootstrap_graph.model_copy(deep=True)
            session = EditSession(
                stem=stem,
                pdf_path=pdf_path,
                base_dpi=_render_dpi_for(pdf_path),
                graph=graph,
                history=existing_history,
                fixture_dir=fixture_dir,
                bootstrap_path=bootstrap_path,
                truth_path=truth_path,
                history_path=history_path,
            )
            _replay_actions(session)
        else:
            session = _fresh_session(
                stem, pdf_path, bootstrap_graph, fixture_dir,
                bootstrap_path, truth_path, history_path, rater,
            )
    else:
        session = _fresh_session(
            stem, pdf_path, bootstrap_graph, fixture_dir,
            bootstrap_path, truth_path, history_path, rater,
        )

    # Build the processing queue: every bootstrap node not already decided.
    decided: set[str] = {
        a.get("node_id") or ""
        for a in session.history["actions"]
        if a.get("op") in ("keep", "revise", "drop", "skip") and a.get("node_id")
    }
    queue = [n for n in bootstrap_graph.nodes if n.id not in decided]

    # Interactive loop. Uses the bootstrap_graph's node order so the rater sees
    # entities deterministically.
    total = len(bootstrap_graph.nodes)
    for idx_in_queue, b_node in enumerate(queue):
        # Find the up-to-date copy in session.graph (may have been mutated).
        node = _node_by_id(session.graph, b_node.id)
        if node is None:
            # Previously dropped via an undo-replay; skip
            continue

        # --skip-confirmed honours the arbitration marker from the run
        if skip_confirmed and (node.attributes or {}).get("arbitration") == "confirmed":
            _do_keep(session, node)
            continue

        while True:
            prog = _progress_line(session, total)
            prompter.message(
                f"\n[{prog}]\n{_describe(node)}"
            )
            crop_path = fixture_dir / ".edit_crops" / f"{node.id}.png"
            try:
                _render_crop(
                    pdf_path, node.page_index, node.bbox_global,
                    session.base_dpi, crop_pad_px, crop_path,
                    render_dpi=render_dpi,
                )
                viewer(crop_path)
                prompter.message(f"  crop → {crop_path}")
            except Exception as exc:
                prompter.message(f"  (could not render crop: {exc})")

            act = prompter.action(
                ["k", "r", "d", "s", "a", "u", "q"], default="k",
            )
            if act == "k":
                _do_keep(session, node)
                break
            if act == "r":
                _do_revise(session, node, prompter)
                break
            if act == "d":
                _do_drop(session, node, prompter)
                break
            if act == "s":
                _do_skip(session, node)
                break
            if act == "a":
                _do_add_missing(session, node, prompter)
                # stay on current node after an add
                continue
            if act == "u":
                msg = _do_undo(session)
                prompter.message(f"  {msg or 'nothing to undo'}")
                continue
            if act == "q":
                prompter.message("saved checkpoint; run again to resume")
                return _save(session, finalised=False)

    # Re-prompt skipped nodes at the end.
    if session.pending_skipped:
        prompter.message(
            f"\n{len(session.pending_skipped)} node(s) were skipped; re-prompting before save."
        )
        requeue = list(session.pending_skipped)
        session.pending_skipped.clear()
        for nid in requeue:
            node = _node_by_id(session.graph, nid)
            if node is None:
                continue
            prompter.message(f"\n(revisit skipped) {_describe(node)}")
            act = prompter.action(["k", "r", "d"], default="k")
            if act == "k":
                _do_keep(session, node)
            elif act == "r":
                _do_revise(session, node, prompter)
            elif act == "d":
                _do_drop(session, node, prompter)

    # Edge correction pass — runs after the node walk so endpoint pickers see
    # the cleaned-up node inventory. The history flag ensures we don't re-run
    # the pass on resume.
    if not session.history.get("edge_walk_done"):
        quit_edges = _run_edge_walk(
            session, prompter, viewer,
            render_dpi=render_dpi, crop_pad_px=crop_pad_px,
        )
        if quit_edges:
            prompter.message("saved checkpoint; run again to resume")
            return _save(session, finalised=False)
        session.history["edge_walk_done"] = True
        _write_history(session)

    return _save(session, finalised=True)


def _run_edge_walk(
    session: EditSession,
    prompter: Prompter,
    viewer: Callable[[Path], None],
    *,
    render_dpi: int,
    crop_pad_px: int,
) -> bool:
    """Walk every surviving edge: keep / revise / drop / skip / add / undo / quit.

    Returns True if the rater quit (meaning checkpoint-and-exit). The skipped
    requeue is handled inline before returning.
    """
    decided_edges: set[str] = {
        a.get("edge_id") or ""
        for a in session.history["actions"]
        if a.get("op") in ("edge_keep", "edge_revise", "edge_drop", "edge_skip")
        and a.get("edge_id")
    }

    # Snapshot the current edge order; new edges added mid-walk land at the end
    # but aren't re-prompted (they were just authored).
    initial_edge_ids = [e.id for e in session.graph.edges]
    queue = [eid for eid in initial_edge_ids if eid not in decided_edges]

    total = len(initial_edge_ids)
    if total == 0:
        # No bootstrap edges → nothing to walk. Skip silently.
        return False

    prompter.message(f"\n=== edge correction pass ===\n{total} edge(s) to review")

    idx_in_queue = 0
    while idx_in_queue < len(queue):
        if True:
            eid = queue[idx_in_queue]
            edge = _edge_by_id(session.graph, eid)
            if edge is None or (edge.attributes or {}).get("gt_drop"):
                idx_in_queue += 1
                continue

            prog = _edge_progress_line(session, total)
            prompter.message(f"\n[edges {prog}]\n{_describe_edge(edge, session.graph)}")
            crop_bbox, page_index = _edge_crop_bbox(edge, session.graph)
            if crop_bbox is not None:
                crop_path = session.fixture_dir / ".edit_crops" / f"edge_{edge.id}.png"
                try:
                    _render_crop(
                        session.pdf_path, page_index, crop_bbox,
                        session.base_dpi, crop_pad_px, crop_path,
                        render_dpi=render_dpi,
                    )
                    viewer(crop_path)
                    prompter.message(f"  crop → {crop_path}")
                except Exception as exc:
                    prompter.message(f"  (could not render edge crop: {exc})")
            else:
                prompter.message("  (one or both endpoints missing — render skipped)")

            choices = ["k", "r", "d", "s", "a", "u", "q"]
            act = prompter.action(choices, default="k")
            if act == "k":
                _do_edge_keep(session, edge)
                idx_in_queue += 1
            elif act == "r":
                _do_edge_revise(session, edge, prompter)
                idx_in_queue += 1
            elif act == "d":
                _do_edge_drop(session, edge, prompter)
                idx_in_queue += 1
            elif act == "s":
                _do_edge_skip(session, edge)
                idx_in_queue += 1
            elif act == "a":
                _do_edge_add(session, prompter)
                # stay on current edge
            elif act == "u":
                msg = _do_undo(session)
                prompter.message(f"  {msg or 'nothing to undo'}")
            elif act == "q":
                return True

    # Re-prompt skipped edges at the end of the walk (mirrors the node flow).
    if session.pending_skipped_edges:
        prompter.message(
            f"\n{len(session.pending_skipped_edges)} edge(s) were skipped; re-prompting before save."
        )
        requeue = list(session.pending_skipped_edges)
        session.pending_skipped_edges.clear()
        for eid in requeue:
            edge = _edge_by_id(session.graph, eid)
            if edge is None:
                continue
            prompter.message(f"\n(revisit skipped) {_describe_edge(edge, session.graph)}")
            act = prompter.action(["k", "r", "d"], default="k")
            if act == "k":
                _do_edge_keep(session, edge)
            elif act == "r":
                _do_edge_revise(session, edge, prompter)
            elif act == "d":
                _do_edge_drop(session, edge, prompter)
    return False


def run_add_edges(
    fixture_dir: Path,
    *,
    prompter: Optional[Prompter] = None,
    rater: str = "",
) -> dict[str, Any]:
    """Append-only edge authoring on top of a finalised `graph.truth.json`.

    Use case: after `run_edit` finalised a session you spot a few connections
    you missed. The full editor would skip the edge walk on resume; this entry
    point is a tight `[a]dd / [q]uit` loop that invokes the same `_do_edge_add`
    helper. Each add lands as an `edge_add` action in the history (timestamped),
    `graph.truth.json` is rewritten, and `history.summary` is bumped to reflect
    the new edge counts.
    """
    prompter = prompter or ConsolePrompter()

    fixture_dir = Path(fixture_dir).resolve()
    stem = fixture_dir.name
    truth_path = fixture_dir / "graph.truth.json"
    history_path = fixture_dir / "graph.truth.history.json"
    pdf_path = fixture_dir.parents[1].parent / "tests" / "p-ids-public" / f"{stem}.pdf"

    if not truth_path.exists():
        raise FileNotFoundError(
            f"{truth_path} — run `diagex gt edit` first to produce a truth file"
        )
    if not history_path.exists():
        # Allowed: caller may want to add edges to a hand-authored truth file.
        history: dict[str, Any] = {
            "stem": stem,
            "bootstrap_path": str(truth_path),
            "rater": rater,
            "started_at": _now(),
            "completed_at": None,
            "actions": [],
            "summary": None,
        }
    else:
        history = json.loads(history_path.read_text())

    graph = ReconciledGraph.model_validate_json(truth_path.read_text())

    # Pick a base_dpi for any future bbox-pt conversions; safe even if the PDF
    # is missing (we don't render crops here, but _do_edge_add doesn't need it).
    base_dpi = _render_dpi_for(pdf_path) if pdf_path.exists() else 300.0

    session = EditSession(
        stem=stem,
        pdf_path=pdf_path,
        base_dpi=base_dpi,
        graph=graph,
        history=history,
        fixture_dir=fixture_dir,
        bootstrap_path=truth_path,
        truth_path=truth_path,
        history_path=history_path,
    )

    prompter.message(
        f"\n=== add-edge mode ===\n"
        f"truth file: {truth_path}\n"
        f"current: {len(graph.nodes)} nodes, {len(graph.edges)} edges"
    )

    added = 0
    while True:
        act = prompter.action(["a", "q"], default="a")
        if act == "q":
            break
        new_id = _do_edge_add(session, prompter)
        if new_id:
            added += 1
            prompter.message(f"  + edge {new_id}  (total added this session: {added})")

    # Refresh summary (don't lose existing fields — just bump edge counts).
    summary = dict(history.get("summary") or {})
    from collections import Counter
    c = Counter(a.get("op") for a in history["actions"])
    summary["edge_added"] = c.get("edge_add", 0)
    summary["final_edges"] = len(graph.edges)
    summary["finalised"] = True
    history["summary"] = summary
    history["completed_at"] = _now()
    history_path.write_text(json.dumps(history, indent=2, default=str))

    truth_path.write_text(graph.model_dump_json(indent=2))

    return {
        "added_this_session": added,
        "final_edges": len(graph.edges),
        "edge_added_total": summary["edge_added"],
    }


def _fresh_session(
    stem: str, pdf_path: Path, bootstrap_graph: ReconciledGraph, fixture_dir: Path,
    bootstrap_path: Path, truth_path: Path, history_path: Path, rater: str,
) -> EditSession:
    return EditSession(
        stem=stem,
        pdf_path=pdf_path,
        base_dpi=_render_dpi_for(pdf_path),
        graph=bootstrap_graph.model_copy(deep=True),
        history=_new_history(stem, bootstrap_path, rater),
        fixture_dir=fixture_dir,
        bootstrap_path=bootstrap_path,
        truth_path=truth_path,
        history_path=history_path,
    )


def _replay_actions(session: EditSession) -> None:
    """Apply existing history actions onto session.graph so the in-memory state
    matches what the rater previously produced. Called on resume."""
    for a in session.history.get("actions") or []:
        op = a.get("op")
        if op == "keep":
            continue
        if op == "skip":
            nid = a.get("node_id")
            if nid:
                session.pending_skipped.append(nid)
            continue
        if op == "revise":
            n = _node_by_id(session.graph, a.get("node_id"))
            if n is None:
                continue
            after = a.get("after") or {}
            if after.get("label"):
                n.label = after["label"]
            if after.get("kind"):
                n.kind = after["kind"]
            attrs = dict(n.attributes or {})
            if after.get("equipment_class"):
                attrs["equipment_class"] = after["equipment_class"]
            n.attributes = attrs
        elif op == "drop":
            n = _node_by_id(session.graph, a.get("node_id"))
            if n is not None:
                attrs = dict(n.attributes or {})
                attrs["gt_drop"] = True
                n.attributes = attrs
        elif op == "add":
            payload = a.get("new_node") or {}
            try:
                bb = payload.get("bbox_global") or {}
                session.graph.nodes.append(
                    ReconciledNode(
                        id=payload["id"],
                        kind=payload.get("kind", "equipment"),
                        label=payload.get("label", "unlabelled"),
                        bbox_global=BBox(**bb),
                        page_index=int(payload.get("page_index", 0)),
                        attributes=payload.get("attributes") or {},
                        confidence=payload.get("confidence", "high"),
                    )
                )
            except (ValidationError, KeyError, TypeError):
                continue
        elif op == "edge_keep":
            continue
        elif op == "edge_skip":
            eid = a.get("edge_id")
            if eid:
                session.pending_skipped_edges.append(eid)
        elif op == "edge_revise":
            e = _edge_by_id(session.graph, a.get("edge_id"))
            if e is None:
                continue
            after = a.get("after") or {}
            if after.get("from_node"):
                e.from_node = after["from_node"]
            if after.get("to_node"):
                e.to_node = after["to_node"]
            if "line_type" in after and after["line_type"] is not None:
                e.line_type = after["line_type"]
        elif op == "edge_drop":
            e = _edge_by_id(session.graph, a.get("edge_id"))
            if e is not None:
                attrs = dict(e.attributes or {})
                attrs["gt_drop"] = True
                e.attributes = attrs
        elif op == "edge_add":
            payload = a.get("new_edge") or {}
            try:
                session.graph.edges.append(
                    ReconciledEdge(
                        id=payload["id"],
                        from_node=payload["from_node"],
                        to_node=payload["to_node"],
                        line_type=payload.get("line_type"),
                        polyline_global=[],
                        confidence=payload.get("confidence", "high"),
                        attributes=payload.get("attributes") or {},
                    )
                )
            except (ValidationError, KeyError, TypeError):
                continue


def _progress_line(session: EditSession, total: int) -> str:
    from collections import Counter
    c = Counter(a.get("op") for a in session.history["actions"])
    done = c.get("keep", 0) + c.get("revise", 0) + c.get("drop", 0) + c.get("skip", 0)
    return (
        f"{done}/{total} "
        f"kept={c.get('keep',0)} revised={c.get('revise',0)} "
        f"dropped={c.get('drop',0)} skipped={c.get('skip',0)} added={c.get('add',0)}"
    )


def _edge_progress_line(session: EditSession, total: int) -> str:
    from collections import Counter
    c = Counter(a.get("op") for a in session.history["actions"])
    done = (
        c.get("edge_keep", 0) + c.get("edge_revise", 0)
        + c.get("edge_drop", 0) + c.get("edge_skip", 0)
    )
    return (
        f"{done}/{total} "
        f"kept={c.get('edge_keep',0)} revised={c.get('edge_revise',0)} "
        f"dropped={c.get('edge_drop',0)} skipped={c.get('edge_skip',0)} added={c.get('edge_add',0)}"
    )


def _save(session: EditSession, *, finalised: bool) -> dict[str, Any]:
    """Emit graph.truth.json (dropping flagged nodes/edges and their orphans)
    and finalise the history.summary."""
    graph = session.graph.model_copy(deep=True)
    drop_node_ids = {n.id for n in graph.nodes if (n.attributes or {}).get("gt_drop")}
    drop_edge_ids = {e.id for e in graph.edges if (e.attributes or {}).get("gt_drop")}

    if drop_node_ids:
        graph.nodes[:] = [n for n in graph.nodes if n.id not in drop_node_ids]
        kept_edges = []
        for e in graph.edges:
            if e.id in drop_edge_ids:
                continue  # already going away under its own ticket
            if e.from_node in drop_node_ids or e.to_node in drop_node_ids:
                graph.conflicts.append(
                    {
                        "type": "edge_auto_drop_after_gt_edit",
                        "edge_id": e.id,
                        "from_node": e.from_node,
                        "to_node": e.to_node,
                        "reason": "endpoint dropped by rater",
                    }
                )
            else:
                kept_edges.append(e)
        graph.edges[:] = kept_edges

    if drop_edge_ids:
        graph.edges[:] = [e for e in graph.edges if e.id not in drop_edge_ids]

    # Clean the working markers off survivors — gt_drop / gt_added are session
    # state, not ground-truth semantics. via_corrected / via_added are kept on
    # nodes for §V provenance reporting.
    for n in graph.nodes:
        if n.attributes:
            attrs = dict(n.attributes)
            attrs.pop("gt_drop", None)
            n.attributes = attrs
    for e in graph.edges:
        if e.attributes:
            attrs = dict(e.attributes)
            attrs.pop("gt_drop", None)
            e.attributes = attrs

    session.truth_path.write_text(graph.model_dump_json(indent=2))

    from collections import Counter
    c = Counter(a.get("op") for a in session.history["actions"])
    bootstrap_count = 0
    bootstrap_edge_count = 0
    try:
        bs_doc = json.loads(session.bootstrap_path.read_text())
        bootstrap_count = len(bs_doc.get("nodes", []))
        bootstrap_edge_count = len(bs_doc.get("edges", []))
    except Exception:
        pass
    summary = {
        "bootstrap_nodes": bootstrap_count,
        "kept": c.get("keep", 0),
        "revised": c.get("revise", 0),
        "dropped": c.get("drop", 0),
        "added": c.get("add", 0),
        "skipped": c.get("skip", 0),
        "final_nodes": len(graph.nodes),
        "retention_pct": round(
            100.0 * c.get("keep", 0) / bootstrap_count if bootstrap_count else 0.0, 1,
        ),
        "bootstrap_edges": bootstrap_edge_count,
        "edge_kept": c.get("edge_keep", 0),
        "edge_revised": c.get("edge_revise", 0),
        "edge_dropped": c.get("edge_drop", 0),
        "edge_added": c.get("edge_add", 0),
        "edge_skipped": c.get("edge_skip", 0),
        "final_edges": len(graph.edges),
        "edge_retention_pct": round(
            100.0 * c.get("edge_keep", 0) / bootstrap_edge_count
            if bootstrap_edge_count else 0.0, 1,
        ),
        "finalised": finalised,
    }
    session.history["summary"] = summary
    if finalised:
        session.history["completed_at"] = _now()
    _write_history(session)
    return summary
