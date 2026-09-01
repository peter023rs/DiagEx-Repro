"""Spec §5.5 — LLM-arbitrated reconciliation (secondary pass).

Runs after the deterministic `reconcile()` pass. For each `conflicts[]` entry
seeded there, we send a scoped LLM call with the relevant cropped regions and
a narrow pick-one / yes-no prompt, then mutate the conflict record in-place
with the decision. Results are logged to `runs/<stem>/<run>/arbitration.jsonl`
for audit.

Conflict types handled (§5.5 final paragraph):
  - `iou_grey_zone`          → pick-one or "same/different entity"
  - `ocr_flip_candidate`     → pick the correct tag reading
  - `ambiguous_opc`          → flag three+ OPCs with the same normalised label

`unstitched_line_endpoint` conflicts are NOT handled here. They are resolved
by the focused agentic ReAct sub-loop in `vision/edge_resolve.py`, which
runs before this pass and may both extend the line geometry and clear the
conflict by re-reconciliation. Anything that survives into this pass is
left unarbitrated (a no-op record).

Budget cap: `max_arbitrations_per_run` (default 25 per `PidConfig`). Conflicts
beyond the cap are tagged `arbitration={"status": "skipped_over_budget"}` so
operators can raise the cap for a rerun if they care.

The LLM call is kept tight on purpose: no tools, no thinking, `max_tokens`
small enough that a 25-conflict run adds ~$0.02 at the planning rates in §10.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

from PIL import Image

from diagex.llm.client import LLMClient, is_non_retryable_api_error
from diagex.llm.cost import CostTracker
from diagex.vision.encode import encode_image_block
from diagex.vision.models import BBox, ReconciledGraph, ReconciledNode


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------


@dataclass
class ArbitrationConfig:
    max_arbitrations_per_run: int = 25
    crop_pad_px: int = 40  # padding around the bbox so context is visible
    crop_max_dim: int = 768  # long side of the crop sent to the LLM

    # Low-confidence second pass (see arbitrate_low_confidence).
    low_conf_max: int = 200
    low_conf_crop_pad_px: int = 60
    low_conf_crop_max_dim: int = 400
    low_conf_reject_abort_frac: float = 0.5  # if >50% of calls REJECT, abort the pass


# ---------------------------------------------------------------------------
# Result record (written to arbitration.jsonl)
# ---------------------------------------------------------------------------


@dataclass
class ArbitrationRecord:
    conflict_index: int
    conflict_type: str
    page_index: int
    decision: dict[str, Any]
    prompt: str
    llm_text: str
    input_tokens: int = 0
    output_tokens: int = 0


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------


def arbitrate_conflicts(
    *,
    graph: ReconciledGraph,
    page_images: dict[int, Image.Image],
    client: LLMClient,
    cost_tracker: CostTracker,
    config: Optional[ArbitrationConfig] = None,
    log_path: Optional[Path] = None,
) -> list[ArbitrationRecord]:
    """Arbitrate `graph.conflicts[]` entries with a scoped LLM call each.

    Mutates conflicts in-place by setting `conflict["arbitration"]` to the
    decision record. Returns the audit trail; when `log_path` is given, the
    trail is also appended as one JSON object per line.

    Conflicts of an unrecognised type are tagged `status=skipped_unknown_type`
    and skipped — arbitration is additive, never destructive.
    """
    cfg = config or ArbitrationConfig()
    records: list[ArbitrationRecord] = []
    nodes_by_id: dict[str, ReconciledNode] = {n.id: n for n in graph.nodes}

    budget_left = max(0, int(cfg.max_arbitrations_per_run))
    for idx, conflict in enumerate(graph.conflicts or []):
        ctype = str(conflict.get("type", ""))
        if budget_left <= 0:
            conflict["arbitration"] = {"status": "skipped_over_budget"}
            continue

        try:
            decision, prompt, resp_text, usage = _arbitrate_one(
                conflict=conflict,
                nodes_by_id=nodes_by_id,
                page_images=page_images,
                client=client,
                cost_tracker=cost_tracker,
                cfg=cfg,
                step_hint=idx,
            )
        except _SkipArbitration as skip:
            conflict["arbitration"] = {"status": skip.status, "detail": skip.detail}
            continue
        except Exception as exc:  # noqa: BLE001 - arbitration is best-effort
            if is_non_retryable_api_error(exc):
                raise
            conflict["arbitration"] = {"status": "error", "detail": repr(exc)}
            continue

        conflict["arbitration"] = decision
        budget_left -= 1

        in_tok = int(usage.get("input_tokens", 0) or 0)
        out_tok = int(usage.get("output_tokens", 0) or 0)
        records.append(
            ArbitrationRecord(
                conflict_index=idx,
                conflict_type=ctype,
                page_index=int(conflict.get("page_index", -1)),
                decision=decision,
                prompt=prompt,
                llm_text=resp_text,
                input_tokens=in_tok,
                output_tokens=out_tok,
            )
        )

    if log_path is not None and records:
        _append_log(log_path, records)

    return records


# ---------------------------------------------------------------------------
# Per-conflict dispatch
# ---------------------------------------------------------------------------


class _SkipArbitration(Exception):
    """Internal signal: the conflict cannot be arbitrated in this run."""

    def __init__(self, status: str, detail: str = "") -> None:
        super().__init__(status)
        self.status = status
        self.detail = detail


def _arbitrate_one(
    *,
    conflict: dict[str, Any],
    nodes_by_id: dict[str, ReconciledNode],
    page_images: dict[int, Image.Image],
    client: LLMClient,
    cost_tracker: CostTracker,
    cfg: ArbitrationConfig,
    step_hint: int,
) -> tuple[dict[str, Any], str, str, dict[str, int]]:
    ctype = str(conflict.get("type", ""))
    page_idx = int(conflict.get("page_index", -1))
    page_image = page_images.get(page_idx)
    if page_image is None and ctype != "ambiguous_opc":
        raise _SkipArbitration("skipped_no_page_image", f"page {page_idx}")

    kwargs = dict(
        client=client,
        cost_tracker=cost_tracker,
        cfg=cfg,
        step_hint=step_hint,
        page_idx=page_idx,
    )
    if ctype == "iou_grey_zone":
        return _arb_iou(conflict, nodes_by_id, page_image, **kwargs)
    if ctype == "ocr_flip_candidate":
        return _arb_ocr(conflict, nodes_by_id, page_image, **kwargs)
    if ctype == "ambiguous_opc":
        return _arb_ambiguous_opc(conflict, nodes_by_id, page_images, **kwargs)
    if ctype == "unstitched_line_endpoint":
        # Handled upstream by vision/edge_resolve.py. Leftovers here mean the
        # resolver was disabled, over budget, or returned uncertain — skip.
        raise _SkipArbitration("skipped_handled_by_edge_resolve")

    raise _SkipArbitration("skipped_unknown_type", ctype)


# ---------------------------------------------------------------------------
# Per-type arbitrators
# ---------------------------------------------------------------------------


def _arb_iou(
    conflict: dict[str, Any],
    nodes_by_id: dict[str, ReconciledNode],
    page_image: Optional[Image.Image],
    *,
    client: LLMClient,
    cost_tracker: CostTracker,
    cfg: ArbitrationConfig,
    step_hint: int,
    page_idx: int,
) -> tuple[dict[str, Any], str, str, dict[str, int]]:
    """IoU grey-zone: are these two annotations the same physical entity?"""
    labels = list(conflict.get("labels") or [])
    anno_ids = list(conflict.get("annotation_ids") or [])
    if len(labels) < 2 or page_image is None:
        raise _SkipArbitration("skipped_insufficient_data")

    # The conflict does not carry bboxes directly; find a node whose
    # source_annotation_ids include the first / second id.
    bboxes = _bboxes_for_annotation_ids(anno_ids, nodes_by_id)
    if len(bboxes) < 2:
        raise _SkipArbitration("skipped_no_bbox")

    crop_a = _crop_with_pad(page_image, bboxes[0], cfg.crop_pad_px, cfg.crop_max_dim)
    crop_b = _crop_with_pad(page_image, bboxes[1], cfg.crop_pad_px, cfg.crop_max_dim)

    prompt = (
        "Two annotations with the same kind and overlapping bounding boxes "
        f"(IoU={conflict.get('iou', '?')}) were kept separate. Are they the "
        "same physical entity on this drawing, or two different entities that "
        "happen to overlap?\n"
        f"Label A: {labels[0]!r}\n"
        f"Label B: {labels[1]!r}\n"
        "Reply with exactly one line:\n"
        "  SAME\n"
        "  DIFFERENT\n"
        "  UNCERTAIN"
    )
    text, usage = _ask(client, cost_tracker, prompt, [crop_a, crop_b], step_hint, page_idx)
    answer = _first_token(text).upper()
    if answer not in {"SAME", "DIFFERENT", "UNCERTAIN"}:
        answer = "UNCERTAIN"
    return (
        {"status": "ok", "verdict": answer, "type": "iou_grey_zone"},
        prompt,
        text,
        usage,
    )


def _arb_ocr(
    conflict: dict[str, Any],
    nodes_by_id: dict[str, ReconciledNode],
    page_image: Optional[Image.Image],
    *,
    client: LLMClient,
    cost_tracker: CostTracker,
    cfg: ArbitrationConfig,
    step_hint: int,
    page_idx: int,
) -> tuple[dict[str, Any], str, str, dict[str, int]]:
    """OCR-flip candidate: pick the correct reading from two similar tags."""
    labels = list(conflict.get("labels") or [])
    anno_ids = list(conflict.get("annotation_ids") or [])
    if len(labels) < 2 or page_image is None:
        raise _SkipArbitration("skipped_insufficient_data")

    bboxes = _bboxes_for_annotation_ids(anno_ids, nodes_by_id)
    if len(bboxes) < 1:
        raise _SkipArbitration("skipped_no_bbox")

    # Crop the union so the tag text is shown in context.
    union = _union_bbox(bboxes)
    crop = _crop_with_pad(page_image, union, cfg.crop_pad_px, cfg.crop_max_dim)

    prompt = (
        "Two readings for the same tag differ by one character — this looks "
        "like an OCR flip (O↔0, I↔1, 5↔S). Looking at the tag in the image, "
        "which reading is correct?\n"
        f"Candidate A: {labels[0]!r}\n"
        f"Candidate B: {labels[1]!r}\n"
        "Reply with exactly one line:\n"
        "  A\n"
        "  B\n"
        "  UNCERTAIN"
    )
    text, usage = _ask(client, cost_tracker, prompt, [crop], step_hint, page_idx)
    answer = _first_token(text).upper()
    if answer == "A":
        chosen = labels[0]
    elif answer == "B":
        chosen = labels[1]
    else:
        answer = "UNCERTAIN"
        chosen = None
    return (
        {
            "status": "ok",
            "verdict": answer,
            "chosen_label": chosen,
            "type": "ocr_flip_candidate",
        },
        prompt,
        text,
        usage,
    )


def _arb_ambiguous_opc(
    conflict: dict[str, Any],
    nodes_by_id: dict[str, ReconciledNode],
    page_images: dict[int, Image.Image],
    *,
    client: LLMClient,
    cost_tracker: CostTracker,
    cfg: ArbitrationConfig,
    step_hint: int,
    page_idx: int,
) -> tuple[dict[str, Any], str, str, dict[str, int]]:
    """Three or more OPCs with the same normalised label — flag for operator."""
    node_ids = list(conflict.get("node_ids") or [])
    if len(node_ids) < 3:
        raise _SkipArbitration("skipped_insufficient_data")

    crops: list[Image.Image] = []
    labels: list[str] = []
    for nid in node_ids[:4]:  # cap for prompt size
        n = nodes_by_id.get(nid)
        if n is None:
            continue
        img = page_images.get(n.page_index)
        if img is None:
            continue
        crops.append(_crop_with_pad(img, n.bbox_global, cfg.crop_pad_px, cfg.crop_max_dim))
        labels.append(f"{n.label} (page {n.page_index + 1})")
    if not crops:
        raise _SkipArbitration("skipped_no_crops")

    prompt = (
        "Three or more off-page connectors (OPCs) share the same normalised "
        "label — an OPC is point-to-point so at least one must be an OCR "
        "error. Which, if any, of these readings matches the shape of the "
        "OPC glyph in its crop?\n"
        + "\n".join(f"  {i + 1}. {lab}" for i, lab in enumerate(labels))
        + "\nReply with exactly one line: the number of the correct reading "
        "(e.g. '1'), 'ALL_MATCH' if they really are the same label, or "
        "'UNCERTAIN'."
    )
    text, usage = _ask(client, cost_tracker, prompt, crops, step_hint, page_idx)
    token = _first_token(text).upper()
    verdict: str
    chosen_index: int | None = None
    if token.isdigit():
        chosen_index = int(token) - 1
        verdict = "CHOSEN"
    elif token == "ALL_MATCH":
        verdict = "ALL_MATCH"
    else:
        verdict = "UNCERTAIN"
    return (
        {
            "status": "ok",
            "verdict": verdict,
            "chosen_index": chosen_index,
            "type": "ambiguous_opc",
        },
        prompt,
        text,
        usage,
    )


# ---------------------------------------------------------------------------
# Low-confidence second pass
# ---------------------------------------------------------------------------


_LOW_CONF_SYSTEM_PROMPT = (
    "You are auditing an individual symbol detection on a P&ID. You will see "
    "a cropped region plus a short description of what was detected there. "
    "Decide whether the detection is correct. Reply with exactly one verdict "
    "token on the first line; if the verdict is REVISE, put the correction on "
    "line 2. Emit no other text."
)

_LOW_CONF_VERDICTS = {"CONFIRM", "REVISE", "REJECT", "UNCERTAIN"}


def arbitrate_low_confidence(
    *,
    graph: ReconciledGraph,
    page_images: dict[int, Image.Image],
    client: LLMClient,
    cost_tracker: CostTracker,
    config: Optional[ArbitrationConfig] = None,
    log_path: Optional[Path] = None,
) -> list[ArbitrationRecord]:
    """Re-crop every medium/low-confidence equipment/instrument node and ask
    the model to CONFIRM, REVISE, REJECT, or mark UNCERTAIN.

    Mutates `graph.nodes` in place:
      - CONFIRM  → node.confidence upgraded to "high"
      - REVISE   → node.label and/or node.attributes["equipment_class"] updated
      - REJECT   → node dropped from graph.nodes; edges touching it are dropped
                   and recorded in graph.conflicts as `dropped_edge_after_arbitration`
      - UNCERTAIN or unparseable → node.attributes["arbitration"] = "uncertain"

    Safety rails: caps the number of calls at `cfg.low_conf_max`; aborts with
    no mutations if more than `low_conf_reject_abort_frac` of the first N
    calls reject (sign that crops are too tight); skips any node already
    carrying an `attributes["arbitration"]` marker (idempotent).
    """
    cfg = config or ArbitrationConfig()
    records: list[ArbitrationRecord] = []

    candidates = [
        n
        for n in graph.nodes
        if n.kind in ("equipment", "instrument")
        and n.confidence in ("medium", "low")
        and "arbitration" not in (n.attributes or {})
    ]
    if not candidates:
        return records

    # Deterministic order: low confidence first, then smaller bbox first
    # (smaller symbols are the ones most likely to be false positives).
    def _order_key(n: ReconciledNode) -> tuple[int, int]:
        conf_rank = 0 if n.confidence == "low" else 1
        area = int(n.bbox_global.w) * int(n.bbox_global.h)
        return (conf_rank, area)

    candidates.sort(key=_order_key)

    cap = max(0, int(cfg.low_conf_max))
    over_cap = candidates[cap:]
    candidates = candidates[:cap]
    for skipped in over_cap:
        attrs = dict(skipped.attributes or {})
        attrs["arbitration"] = "skipped_over_cap"
        skipped.attributes = attrs

    # Two-phase mutation: first collect verdicts, then apply after the
    # safety-check on overall reject rate. That keeps the pass atomic when
    # crops are systematically too tight.
    pending: list[tuple[ReconciledNode, dict[str, Any], str, str, dict[str, int]]] = []
    rejects = 0
    total_calls = 0

    for idx, node in enumerate(candidates):
        img = page_images.get(node.page_index)
        if img is None:
            attrs = dict(node.attributes or {})
            attrs["arbitration"] = "skipped_no_page_image"
            node.attributes = attrs
            continue

        crop = _crop_with_pad(
            img,
            node.bbox_global,
            cfg.low_conf_crop_pad_px,
            cfg.low_conf_crop_max_dim,
        )
        prompt = _build_low_conf_prompt(node)
        try:
            text, usage = _ask_low_conf(
                client,
                cost_tracker,
                prompt,
                [crop],
                idx,
                node.page_index,
            )
        except Exception as exc:  # noqa: BLE001 - arbitration is best-effort
            if is_non_retryable_api_error(exc):
                raise
            attrs = dict(node.attributes or {})
            attrs["arbitration"] = "error"
            attrs["arbitration_error"] = repr(exc)
            node.attributes = attrs
            continue

        verdict, revision = _parse_low_conf_verdict(text)
        total_calls += 1
        if verdict == "REJECT":
            rejects += 1
        decision: dict[str, Any] = {
            "status": "ok",
            "verdict": verdict,
            "type": "low_confidence_reask",
            "node_id": node.id,
        }
        if verdict == "REVISE" and revision:
            decision["revision"] = revision
        pending.append((node, decision, prompt, text, usage))

    # Safety: if the reject rate is implausibly high, return without mutating.
    if total_calls >= 4 and rejects / total_calls > cfg.low_conf_reject_abort_frac:
        for node, decision, prompt, text, usage in pending:
            attrs = dict(node.attributes or {})
            attrs["arbitration"] = "aborted_high_reject_rate"
            node.attributes = attrs
            records.append(
                ArbitrationRecord(
                    conflict_index=-1,
                    conflict_type="low_confidence_reask",
                    page_index=node.page_index,
                    decision={**decision, "status": "aborted_high_reject_rate"},
                    prompt=prompt,
                    llm_text=text,
                    input_tokens=int(usage.get("input_tokens", 0) or 0),
                    output_tokens=int(usage.get("output_tokens", 0) or 0),
                )
            )
        if log_path is not None and records:
            _append_log(log_path, records)
        return records

    # Apply verdicts.
    drop_ids: set[str] = set()
    for node, decision, prompt, text, usage in pending:
        verdict = decision["verdict"]
        attrs = dict(node.attributes or {})
        if verdict == "CONFIRM":
            node.confidence = "high"
            attrs["arbitration"] = "confirmed"
        elif verdict == "REVISE":
            rev = decision.get("revision") or {}
            new_label = rev.get("tag")
            new_class = rev.get("class")
            if new_label:
                attrs["label_before_arbitration"] = node.label
                node.label = new_label
            if new_class:
                attrs["equipment_class_before_arbitration"] = attrs.get("equipment_class")
                attrs["equipment_class"] = new_class
            attrs["arbitration"] = "revised"
            # confidence intentionally left at medium/low — the model changed
            # its mind on re-look; that's not an upgrade
        elif verdict == "REJECT":
            drop_ids.add(node.id)
            attrs["arbitration"] = "rejected"  # recorded on the drop-copy below for audit
        else:  # UNCERTAIN or unparseable
            attrs["arbitration"] = "uncertain"
        node.attributes = attrs

        records.append(
            ArbitrationRecord(
                conflict_index=-1,
                conflict_type="low_confidence_reask",
                page_index=node.page_index,
                decision=decision,
                prompt=prompt,
                llm_text=text,
                input_tokens=int(usage.get("input_tokens", 0) or 0),
                output_tokens=int(usage.get("output_tokens", 0) or 0),
            )
        )

    # Drop rejected nodes and edges that reference them.
    if drop_ids:
        graph.nodes[:] = [n for n in graph.nodes if n.id not in drop_ids]
        kept_edges = []
        for e in graph.edges:
            if e.from_node in drop_ids or e.to_node in drop_ids:
                graph.conflicts.append(
                    {
                        "type": "dropped_edge_after_arbitration",
                        "edge_id": e.id,
                        "from_node": e.from_node,
                        "to_node": e.to_node,
                        "reason": "endpoint_rejected_in_low_confidence_arbitration",
                    }
                )
            else:
                kept_edges.append(e)
        graph.edges[:] = kept_edges

    if log_path is not None and records:
        _append_log(log_path, records)

    return records


def _build_low_conf_prompt(node: ReconciledNode) -> str:
    eq_class = (node.attributes or {}).get("equipment_class") or "n/a"
    return (
        f"This region of a P&ID was detected as kind={node.kind}, "
        f"class={eq_class}, tag={node.label!r}. Confidence was "
        f"{node.confidence!r}. Examine the cropped image and verdict the "
        "detection.\n"
        "Reply with exactly one verdict token on line 1:\n"
        "  CONFIRM   — detection is correct as described.\n"
        "  REVISE    — symbol is present but class/tag is wrong. On line 2, "
        "give the correction as 'class=<X>' and/or 'tag=<Y>' "
        "(space-separated, either or both).\n"
        "  REJECT    — no such symbol exists here; this is a false positive.\n"
        "  UNCERTAIN — cannot tell from the crop."
    )


def _ask_low_conf(
    client: LLMClient,
    cost_tracker: CostTracker,
    prompt: str,
    images: list[Image.Image],
    step_hint: int,
    page_idx: int,
) -> tuple[str, dict[str, int]]:
    """Same shape as `_ask`, but uses the low-confidence system prompt.

    Negative step offset is distinct from `_ask`'s so the two passes are
    separable in cost.json (main arbitration uses -1000-idx; this pass uses
    -2000-idx).
    """
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
            + [_image_content_block(img) for img in images],
        }
    ]
    resp = client.messages_create(
        system=[{"type": "text", "text": _LOW_CONF_SYSTEM_PROMPT}],
        messages=messages,
        tools=None,
        max_tokens=128,
        thinking={"type": "disabled"},
        output_config={"effort": "low"},
    )
    cost_tracker.record(
        resp,
        step=-2000 - step_hint,
        tile_id="arbitration_low_conf",
        page_index=page_idx if page_idx >= 0 else None,
    )
    text = _extract_text(resp)
    usage = getattr(resp, "usage", None)
    usage_dict = {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
    }
    return text, usage_dict


def _parse_low_conf_verdict(text: str) -> tuple[str, dict[str, str] | None]:
    """Parse a low-confidence reply into (verdict, revision-or-None).

    Verdict is the first token of line 1, normalised to uppercase and
    constrained to the allowed set; unknown tokens map to UNCERTAIN. For
    REVISE, line 2 may carry 'class=<X>' and/or 'tag=<Y>' (space-separated);
    either, both, or neither are accepted.
    """
    lines = [ln.strip() for ln in (text or "").splitlines() if ln.strip()]
    if not lines:
        return "UNCERTAIN", None
    verdict = _first_token(lines[0]).upper()
    if verdict not in _LOW_CONF_VERDICTS:
        return "UNCERTAIN", None
    if verdict != "REVISE":
        return verdict, None
    revision: dict[str, str] = {}
    if len(lines) >= 2:
        for tok in lines[1].split():
            if "=" not in tok:
                continue
            k, _, v = tok.partition("=")
            k = k.strip().lower()
            v = v.strip().strip("'\"")
            if k in ("class", "tag") and v:
                revision[k] = v
    return "REVISE", (revision or None)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _bboxes_for_annotation_ids(
    anno_ids: Iterable[str],
    nodes_by_id: dict[str, ReconciledNode],
) -> list[BBox]:
    """Return one bbox per annotation id, looking the id up among node
    `source_annotation_ids`. De-duplicates to avoid the same node appearing
    twice when a cluster already absorbed both sides of the conflict.
    """
    out: list[BBox] = []
    seen_nodes: set[str] = set()
    for aid in anno_ids:
        for n in nodes_by_id.values():
            if aid in (n.source_annotation_ids or []):
                if n.id in seen_nodes:
                    break
                seen_nodes.add(n.id)
                out.append(n.bbox_global)
                break
    return out


def _union_bbox(boxes: list[BBox]) -> BBox:
    x1 = min(b.x for b in boxes)
    y1 = min(b.y for b in boxes)
    x2 = max(b.x + b.w for b in boxes)
    y2 = max(b.y + b.h for b in boxes)
    return BBox(x=x1, y=y1, w=x2 - x1, h=y2 - y1)


def _crop_with_pad(
    page_image: Image.Image,
    bbox: BBox,
    pad: int,
    max_dim: int,
) -> Image.Image:
    pw, ph = page_image.size
    x1 = max(0, bbox.x - pad)
    y1 = max(0, bbox.y - pad)
    x2 = min(pw, bbox.x + bbox.w + pad)
    y2 = min(ph, bbox.y + bbox.h + pad)
    if x2 <= x1 or y2 <= y1:
        # Degenerate bbox — fall back to a tiny window at the origin so the
        # LLM at least sees something; the prompt still frames the question.
        x1, y1, x2, y2 = 0, 0, min(pw, 64), min(ph, 64)
    crop = page_image.crop((x1, y1, x2, y2))
    w, h = crop.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        crop = crop.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
    return crop


def _image_content_block(img: Image.Image) -> dict[str, Any]:
    return encode_image_block(img)


_ARB_SYSTEM_PROMPT = (
    "You are auditing uncertain annotations on an industrial-schematic "
    "extraction run. Each call gives you one or more image crops and a narrow "
    "multiple-choice question. Answer with exactly the requested token on the "
    "first line and no further commentary."
)


def _ask(
    client: LLMClient,
    cost_tracker: CostTracker,
    prompt: str,
    images: list[Image.Image],
    step_hint: int,
    page_idx: int,
) -> tuple[str, dict[str, int]]:
    messages = [
        {
            "role": "user",
            "content": [{"type": "text", "text": prompt}]
            + [_image_content_block(img) for img in images],
        }
    ]
    resp = client.messages_create(
        system=[{"type": "text", "text": _ARB_SYSTEM_PROMPT}],
        messages=messages,
        tools=None,
        max_tokens=128,
        thinking={"type": "disabled"},
        output_config={"effort": "low"},
    )
    # Fold arbitration spend into cost.json — step index uses a negative
    # offset so arbitration steps sort distinctly from the ReAct loop.
    cost_tracker.record(
        resp,
        step=-1000 - step_hint,
        tile_id="arbitration",
        page_index=page_idx if page_idx >= 0 else None,
    )
    text = _extract_text(resp)
    usage = getattr(resp, "usage", None)
    usage_dict = {
        "input_tokens": int(getattr(usage, "input_tokens", 0) or 0) if usage else 0,
        "output_tokens": int(getattr(usage, "output_tokens", 0) or 0) if usage else 0,
    }
    return text, usage_dict


def _extract_text(resp: Any) -> str:
    content = getattr(resp, "content", None) or []
    out: list[str] = []
    for b in content:
        t = getattr(b, "type", None) if not isinstance(b, dict) else b.get("type")
        if t == "text":
            out.append(getattr(b, "text", "") if not isinstance(b, dict) else (b.get("text") or ""))
    return "\n".join(out).strip()


def _first_token(text: str) -> str:
    for ln in text.splitlines():
        stripped = ln.strip().strip(".").strip()
        if stripped:
            return stripped.split()[0]
    return ""


def _append_log(path: Path, records: list[ArbitrationRecord]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        for r in records:
            f.write(
                json.dumps(
                    {
                        "conflict_index": r.conflict_index,
                        "conflict_type": r.conflict_type,
                        "page_index": r.page_index,
                        "decision": r.decision,
                        "prompt": r.prompt,
                        "llm_text": r.llm_text,
                        "input_tokens": r.input_tokens,
                        "output_tokens": r.output_tokens,
                    }
                )
                + "\n"
            )
