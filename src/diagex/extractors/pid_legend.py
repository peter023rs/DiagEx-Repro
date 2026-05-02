"""Legend resolution pipeline (spec §7.2.2).

Given a diagram + CLI flags, produce a `LegendResolution`: a merged
`LegendPack` (extracted union built-in, extracted wins on label collisions)
split into a cached few-shot block and a `lookup_symbol` overflow.

Resolution order (first matching rule wins):
    1. --legend <path>
    2. --legend-pages X,Y
    3. --legend-region "p<n>:x,y,w,h"
    4. --no-legend
    5. default: auto-detect via overview-only yes/no classifier per page.

Caching: extracted packs are persisted under either
    runs/<stem>/legend.cache.json   (per-diagram)         OR
    legends/<key>.json              (shared, --legend-key <key>)
The cache is keyed on `source_hash` (sha256 of the input bytes). A hash
mismatch forces re-extraction.

The extracted pack is cached *before* merge with built-ins so the built-in
library can evolve without invalidating every customer cache.
"""

from __future__ import annotations

import base64
import hashlib
import io
import json
from dataclasses import dataclass
from importlib import resources
from pathlib import Path
from typing import Any, Optional

from PIL import Image
from pydantic import ValidationError

from diagex.agent.runtime import ReactRuntime, RunConfig
from diagex.agent.state import AgentState
from diagex.agent.tools import build_phase2_tools
from diagex.config import Config, EFFORT_PROFILES, PidConfig
from diagex.llm.client import LLMClient
from diagex.llm.cost import CostTracker
from diagex.llm.prompts.phase2_legend import build_legend_system_prompt
from diagex.vision.encode import encode_image_block
from diagex.vision.legend_models import (
    LegendBudget,
    LegendEntry,
    LegendPack,
    SymbolStandard,
)
from diagex.vision.loader import iter_pages
from diagex.vision.models import BBox, DiagramPage, DiagramSource, Tile
from diagex.vision.tiling import AspectAwareStrategy, tile
from diagex.vision.views import ViewProvider


# ---------------------------------------------------------------------------
# Result container
# ---------------------------------------------------------------------------


@dataclass
class LegendResolution:
    """Outcome of `resolve_legend`: merged pack + budget split + provenance."""

    pack: LegendPack                   # merged (extracted ∪ built-in)
    budget: LegendBudget               # pack split into few_shot + lookup_only
    source: str                        # "explicit_file" | "explicit_pages" | "explicit_region"
                                       #  | "auto_detected" | "no_legend" | "cache_hit" | "built_in_only"
    cache_path: Optional[Path]         # where the *extracted* pack was persisted


# ---------------------------------------------------------------------------
# Built-in loader
# ---------------------------------------------------------------------------


def load_builtin_pack(standard: SymbolStandard) -> LegendPack:
    """Read src/diagex/assets/symbols/{standard}.json into a LegendPack.

    Returns an empty pack when `standard == "none"` so callers can merge
    unconditionally. Missing files raise FileNotFoundError — this is a
    packaging bug, not a runtime condition.
    """
    if standard == "none":
        return LegendPack(standard="none", source_ref="built-in:none", entries=[])

    try:
        files = resources.files("diagex.assets.symbols")
        raw = (files / f"{standard}.json").read_text(encoding="utf-8")
    except (FileNotFoundError, ModuleNotFoundError) as exc:
        raise FileNotFoundError(f"built-in symbol library missing: {standard}") from exc

    data = json.loads(raw)
    return LegendPack.model_validate(data)


# ---------------------------------------------------------------------------
# Hashing
# ---------------------------------------------------------------------------


def compute_source_hash(
    *,
    path: Optional[Path] = None,
    page_bytes: Optional[list[bytes]] = None,
    region_bytes: Optional[bytes] = None,
) -> str:
    """sha256 hex over the legend input bytes. Exactly one kwarg must be set."""
    provided = [x is not None for x in (path, page_bytes, region_bytes)]
    if sum(provided) != 1:
        raise ValueError("compute_source_hash: pass exactly one of path / page_bytes / region_bytes")

    h = hashlib.sha256()
    if path is not None:
        # Stream the file so a 200-page PDF doesn't land in RAM.
        with Path(path).open("rb") as f:
            for chunk in iter(lambda: f.read(1 << 20), b""):
                h.update(chunk)
    elif page_bytes is not None:
        # Deterministic: hash in the order passed, with a 32-bit length prefix
        # per chunk so `[b"a", b"bc"]` and `[b"ab", b"c"]` hash differently.
        for b in page_bytes:
            h.update(len(b).to_bytes(4, "big"))
            h.update(b)
    else:
        assert region_bytes is not None
        h.update(region_bytes)
    return h.hexdigest()


# ---------------------------------------------------------------------------
# Budget split
# ---------------------------------------------------------------------------


def apply_budget(pack: LegendPack, cfg_pid: PidConfig) -> LegendBudget:
    """Split `pack.entries` into few_shot + lookup_only per §7.2.2 prioritisation.

    Priority (entries earlier in the list are admitted first):
      1. source in {"legend_extracted", "customer_override"} — customer-specific wins.
      2. standard == pack.standard (the requested symbol_standard).
      3. kind in {"instrument", "valve", "equipment"} before {"line", "connector", "other"}.
      4. Remaining entries in file order (stable, deterministic).

    Token estimate: ~40 tokens for label+description text; +300 when image_b64
    is set. v0 built-ins are text-only so the 40-token figure dominates.
    Admission stops on the first boundary hit: token budget OR max entry count.
    """
    few_shot_token_cap = cfg_pid.legend_few_shot_tokens
    max_entries = cfg_pid.legend_few_shot_max_entries
    target_standard = pack.standard

    kind_rank = {"instrument": 0, "valve": 0, "equipment": 0, "line": 1, "connector": 1, "other": 2}

    # Decorate with (priority, original_index) then sort — stable on ties.
    decorated: list[tuple[tuple[int, int, int], int, LegendEntry]] = []
    for i, e in enumerate(pack.entries):
        p1 = 0 if e.source in ("legend_extracted", "customer_override") else 1
        p2 = 0 if (e.standard == target_standard) else 1
        p3 = kind_rank.get(e.kind, 2)
        decorated.append(((p1, p2, p3), i, e))

    # Sorting on (priority_tuple, original_index) is stable and deterministic.
    decorated.sort(key=lambda t: (t[0], t[1]))

    few_shot: list[LegendEntry] = []
    lookup_only: list[LegendEntry] = []
    used = 0
    for _, _, e in decorated:
        cost = _entry_token_estimate(e)
        # Admit while both caps hold; otherwise demote.
        if len(few_shot) < max_entries and (used + cost) <= few_shot_token_cap:
            few_shot.append(e)
            used += cost
        else:
            lookup_only.append(e)

    return LegendBudget(
        few_shot=few_shot,
        lookup_only=lookup_only,
        budget_tokens=few_shot_token_cap,
        used_tokens=used,
    )


def _entry_token_estimate(e: LegendEntry) -> int:
    return 40 + (300 if e.image_b64 else 0)


# ---------------------------------------------------------------------------
# Cache helpers
# ---------------------------------------------------------------------------


def _cache_path_for(
    *,
    legend_key: Optional[str],
    cfg_pid: PidConfig,
    runs_dir_for_stem: Optional[Path],
) -> Optional[Path]:
    """Resolve the cache file path.

    Shared (`legend_key` set) takes priority over per-diagram (`runs_dir_for_stem`).
    Returns None if neither is provided — caller then runs uncached.
    """
    if legend_key:
        return Path(cfg_pid.legends_dir) / f"{legend_key}.json"
    if runs_dir_for_stem:
        return Path(runs_dir_for_stem) / "legend.cache.json"
    return None


def _load_cached(path: Optional[Path], expected_hash: str) -> Optional[LegendPack]:
    """Return the cached pack iff its source_hash matches; else None."""
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        pack = LegendPack.model_validate(data)
    except (json.JSONDecodeError, ValidationError, OSError):
        # Corrupt or schema-shifted cache -> treat as miss; will be overwritten.
        return None
    if pack.source_hash != expected_hash:
        return None
    return pack


def _persist(path: Optional[Path], pack: LegendPack) -> Optional[Path]:
    """Write `pack` to `path`. Creates parent dirs. Returns the path or None."""
    if path is None:
        return None
    path.parent.mkdir(parents=True, exist_ok=True)
    # model_dump_json handles Path / Literal / nested models cleanly.
    path.write_text(pack.model_dump_json(indent=2), encoding="utf-8")
    return path


# ---------------------------------------------------------------------------
# Image / page helpers
# ---------------------------------------------------------------------------


def _page_png_bytes(page: DiagramPage) -> bytes:
    """Serialise a page image to PNG bytes for hashing (deterministic)."""
    if page.image is None:
        return b""
    buf = io.BytesIO()
    page.image.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _iter_legend_pages(source: DiagramSource, indices: list[int]) -> list[DiagramPage]:
    """Materialise only the requested page indices (0-based).

    Streams pages and keeps a reference to each one we want — callers
    subsequently run the extraction agent over the kept pages.
    """
    wanted = set(indices)
    kept: list[DiagramPage] = []
    for page in iter_pages(source):
        if page.page_index in wanted:
            kept.append(page)
        if len(kept) == len(wanted):
            break
    return kept


def _crop_region(page: DiagramPage, x: int, y: int, w: int, h: int) -> Image.Image:
    """Clip a region to the page bounds and return the crop."""
    if page.image is None:
        raise ValueError(f"Page {page.page_index} has no image; cannot crop region.")
    x0 = max(0, int(x))
    y0 = max(0, int(y))
    x1 = min(page.width, int(x) + int(w))
    y1 = min(page.height, int(y) + int(h))
    if x1 <= x0 or y1 <= y0:
        raise ValueError(f"Empty region: ({x},{y},{w},{h}) on page {page.width}x{page.height}")
    return page.image.crop((x0, y0, x1, y1))


def _thumbnail_b64(img: Image.Image, max_dim: int) -> str:
    """Downsize to `max_dim` long side, encode PNG -> base64."""
    thumb = img.copy()
    thumb.thumbnail((max_dim, max_dim), Image.BILINEAR)
    buf = io.BytesIO()
    thumb.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("ascii")


# ---------------------------------------------------------------------------
# Auto-detect: "is this page a legend?"
# ---------------------------------------------------------------------------


_AUTO_DETECT_MIN_DIM = 200  # pages smaller than this in either axis are skipped


def _image_to_content_block(img: Image.Image, max_dim: int = 1200) -> dict[str, Any]:
    """Downsampled image packaged as a size-safe Anthropic image content-block."""
    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)
    return encode_image_block(img)


def _auto_detect_page(
    *,
    page: DiagramPage,
    client: LLMClient,
    cost_tracker: CostTracker,
) -> tuple[bool, Optional[tuple[int, int, int, int]]]:
    """One-shot yes/no classifier over the page overview.

    Returns `(is_legend, bbox_or_None)` where bbox is in page-pixel coords.
    `bbox` is None when the model answered 'full' or omitted a box.
    """
    if page.image is None:
        return False, None
    if min(page.width, page.height) < _AUTO_DETECT_MIN_DIM:
        return False, None

    # System prompt: stable short instruction. Per-page framing is trivial
    # text so we don't bother with cache_control here.
    system_blocks = [
        {
            "type": "text",
            "text": (
                "You are a binary classifier over engineering-drawing pages. "
                "Answer the user's yes/no question about whether the supplied "
                "page is a symbol or abbreviation legend. Never add commentary."
            ),
            "cache_control": {"type": "ephemeral"},
        }
    ]
    user_text = (
        f"Page size: {page.width}x{page.height} px. Is this page (or a corner "
        f"of it) a symbol or abbreviation legend for an engineering drawing? "
        f"Reply with exactly one of:\n"
        f"  Line 1: 'yes' or 'no'.\n"
        f"  Line 2 (only if yes): 'full' if the whole page is legend, else "
        f"'x,y,w,h' in page pixels bounding the legend region."
    )
    messages = [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": user_text},
                _image_to_content_block(page.image, max_dim=1200),
            ],
        }
    ]

    try:
        resp = client.messages_create(
            system=system_blocks,
            messages=messages,
            tools=None,
            max_tokens=128,
            thinking={"type": "disabled"},
            output_config={"effort": "low"},
        )
    except Exception:
        # Any transport/validation failure -> treat the page as 'not a legend'.
        # A missed legend page just falls through to built-in-only; it does
        # not corrupt the run.
        return False, None

    cost_tracker.record(resp, step=0, page_index=page.page_index)
    text = _extract_text(resp).strip()
    return _parse_auto_detect(text, page_w=page.width, page_h=page.height)


def _extract_text(resp: Any) -> str:
    """Concatenate text blocks from an Anthropic Messages response."""
    content = getattr(resp, "content", None) or []
    out: list[str] = []
    for b in content:
        t = getattr(b, "type", None) if not isinstance(b, dict) else b.get("type")
        if t == "text":
            out.append(
                getattr(b, "text", "") if not isinstance(b, dict) else (b.get("text") or "")
            )
    return "\n".join(out)


def _parse_auto_detect(
    text: str, *, page_w: int, page_h: int
) -> tuple[bool, Optional[tuple[int, int, int, int]]]:
    """Parse the yes/no + bbox response.

    Robust to stray whitespace, trailing punctuation, and case; bails to
    'no' on anything ambiguous.
    """
    lines = [ln.strip().strip(".").lower() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return False, None
    first = lines[0]
    if first.startswith("no"):
        return False, None
    if not first.startswith("yes"):
        return False, None
    # yes; look for a bbox on any subsequent line.
    for ln in lines[1:]:
        if ln == "full":
            return True, None
        parts = [p.strip() for p in ln.replace(";", ",").split(",")]
        if len(parts) == 4:
            try:
                x, y, w, h = (int(float(p)) for p in parts)
            except ValueError:
                continue
            # Clip to page and drop nonsense boxes.
            x = max(0, min(page_w, x))
            y = max(0, min(page_h, y))
            w = max(0, min(page_w - x, w))
            h = max(0, min(page_h - y, h))
            if w > 0 and h > 0:
                return True, (x, y, w, h)
    # yes without a parseable bbox — treat as full-page legend.
    return True, None


# ---------------------------------------------------------------------------
# Extraction agent pass
# ---------------------------------------------------------------------------


def _extract_from_page(
    *,
    page: DiagramPage,
    region: Optional[tuple[int, int, int, int]],
    client: LLMClient,
    cost_tracker: CostTracker,
    cfg: Config,
) -> list[LegendEntry]:
    """Run a ReAct extraction pass over one page (optionally cropped) and
    harvest LegendEntry rows from the agent's annotations.

    On any failure (step limit, API error, validation error) returns an
    empty list — the caller falls back to built-in-only and logs the reason.
    """
    # If a sub-region was given, build a synthetic page containing just the
    # crop so tiling / views stay aligned with what the agent actually sees.
    work_page = page
    origin = (0, 0)
    if region is not None:
        x, y, w, h = region
        crop = _crop_region(page, x, y, w, h)
        origin = (x, y)
        work_page = DiagramPage(
            page_index=page.page_index,
            image=crop,
            width=crop.size[0],
            height=crop.size[1],
            dpi=page.dpi,
            effective_dpi=page.effective_dpi,
            is_scanned=page.is_scanned,
            rotation_deg=page.rotation_deg,
            source_ref=f"{page.source_ref}#legend-region",
        )

    tiles = tile(
        work_page,
        AspectAwareStrategy(
            max_tokens_per_tile=cfg.tiling.max_tokens_per_tile,
            overlap_frac=cfg.tiling.overlap_frac,
            token_per_pixel=cfg.tiling.token_per_pixel,
        ),
    )
    vp = ViewProvider(work_page, tiles)

    profile = EFFORT_PROFILES["medium"]
    system_blocks = build_legend_system_prompt(effort_max_steps=profile.max_steps)

    # Legend extraction MUST NOT carry a lookup_symbol tool — otherwise the
    # agent could recurse into its own overflow pack. Keep `lookup_legend`
    # on state as None; only the 7-tool base set is offered.
    state = AgentState(question="Extract the symbol legend on this page.", page=work_page)
    state.lookup_legend = None

    # Fresh local runtime so we can override the tools list. The standard
    # runtime reads TOOL_SCHEMAS at dispatch time; we ensure no lookup tool
    # is registered by simply not extending that list.
    runtime = ReactRuntime(
        client=client,
        system_blocks=system_blocks,
        cost_tracker=cost_tracker,
        budgets=cfg.budgets,
    )
    # Sanity: build_phase2_tools(with_lookup=False) == TOOL_SCHEMAS for the
    # base set. We invoke it to match the spec's wording; the runtime does
    # not consume this list directly (it reads TOOL_SCHEMAS itself), but
    # keeping the call documents intent + guards against future refactors.
    _ = build_phase2_tools(with_lookup=False)

    try:
        runtime.run(state=state, view_provider=vp, run_cfg=RunConfig(effort="medium"))
    except Exception:
        return []

    entries: list[LegendEntry] = []
    for a in state.annotations.all():
        entry = _annotation_to_entry(
            annotation=a,
            page=page,
            origin=origin,
            cfg_pid=cfg.pid,
        )
        if entry is not None:
            entries.append(entry)
    return entries


def _annotation_to_entry(
    *,
    annotation: Any,
    page: DiagramPage,
    origin: tuple[int, int],
    cfg_pid: PidConfig,
) -> Optional[LegendEntry]:
    """Convert a legend-pass Annotation into a LegendEntry.

    Rules:
      - Require a non-empty label. Illegible entries are skipped.
      - `legend_symbol_class` from attributes becomes `symbol_class`; fall
        back to a heuristic from `kind` when missing.
      - Crop the symbol thumbnail from the page image at bbox_global shifted
        back into the original page's coordinate system (via `origin`).
    """
    label = (annotation.label or "").strip()
    if not label:
        return None

    attrs = dict(annotation.attributes or {})
    symbol_class = str(attrs.pop("legend_symbol_class", "") or "").strip()
    if not symbol_class:
        symbol_class = _default_symbol_class_for_kind(annotation.kind)
    description = str(attrs.pop("legend_description", "") or "").strip() or None
    legend_kind = str(attrs.pop("legend_kind", "") or "").strip()
    standard_val = str(attrs.pop("legend_standard", "") or "").strip() or None
    standard: SymbolStandard | None
    if standard_val in ("isa-5.1", "iso-10628", "sama", "none"):
        standard = standard_val  # type: ignore[assignment]
    else:
        standard = None

    # Reproject bbox back to the original page if the extraction ran over a
    # cropped sub-region; origin is (0,0) otherwise so this is a no-op.
    bbox = annotation.bbox_global
    page_bbox = BBox(
        x=bbox.x + origin[0],
        y=bbox.y + origin[1],
        w=bbox.w,
        h=bbox.h,
    )
    image_b64: str | None = None
    if page.image is not None and page_bbox.w > 0 and page_bbox.h > 0:
        try:
            crop = page.image.crop(
                (page_bbox.x, page_bbox.y, page_bbox.x2, page_bbox.y2)
            )
            image_b64 = _thumbnail_b64(crop, cfg_pid.legend_thumb_max_dim)
        except Exception:
            image_b64 = None

    # Normalise the kind into the LegendEntry Literal set. The Annotation's
    # kind set is broader (includes text / note / opc); fold those into
    # "other" rather than guessing.
    entry_kind_map = {
        "equipment": "equipment",
        "instrument": "instrument",
        "line": "line",
        "connection": "connector",
    }
    entry_kind = entry_kind_map.get(annotation.kind, "other")

    if legend_kind:
        attrs.setdefault("legend_kind", legend_kind)

    try:
        return LegendEntry(
            label=label,
            description=description,
            symbol_class=symbol_class or "unclassified_equipment",
            kind=entry_kind,  # type: ignore[arg-type]
            standard=standard,
            image_b64=image_b64,
            attributes={k: str(v) for k, v in attrs.items()},
            source="legend_extracted",
        )
    except ValidationError:
        return None


def _default_symbol_class_for_kind(kind: str) -> str:
    """Fallback when the agent forgot `legend_symbol_class`."""
    return {
        "instrument": "unclassified_instrument",
        "equipment": "unclassified_equipment",
        "line": "line",
        "connection": "connector",
    }.get(kind, "unclassified_equipment")


# ---------------------------------------------------------------------------
# Top-level entry point
# ---------------------------------------------------------------------------


def resolve_legend(
    *,
    source: DiagramSource,
    symbol_standard: SymbolStandard,
    cfg: Config,
    client: LLMClient,
    cost_tracker: CostTracker,
    legend_path: Optional[Path] = None,
    legend_pages: Optional[list[int]] = None,
    legend_region: Optional[tuple[int, int, int, int, int]] = None,
    no_legend: bool = False,
    legend_key: Optional[str] = None,
    runs_dir_for_stem: Optional[Path] = None,
) -> LegendResolution:
    """Resolve, extract, cache, merge, and budget-split the legend.

    See module docstring for the resolution order. Returns a LegendResolution
    the Phase 2 orchestrator feeds into `build_pid_system_prompt` + the
    lookup_symbol tool registration.
    """
    # Input-selector mutual exclusion. `legend_key` and `runs_dir_for_stem`
    # are cache modifiers; they don't count.
    selectors = [
        legend_path is not None,
        legend_pages is not None,
        legend_region is not None,
        no_legend,
    ]
    if sum(selectors) > 1:
        raise ValueError(
            "resolve_legend: --legend / --legend-pages / --legend-region / "
            "--no-legend are mutually exclusive."
        )

    builtin = load_builtin_pack(symbol_standard)
    cache_path = _cache_path_for(
        legend_key=legend_key,
        cfg_pid=cfg.pid,
        runs_dir_for_stem=runs_dir_for_stem,
    )

    # --- rule 4: --no-legend -------------------------------------------------
    if no_legend:
        merged = LegendPack(
            standard=symbol_standard,
            source_ref=f"{source.path.stem}#no-legend",
            notes="--no-legend; built-in only" if builtin.entries else "--no-legend; empty",
        ).merge(builtin)
        return LegendResolution(
            pack=merged,
            budget=apply_budget(merged, cfg.pid),
            source="no_legend",
            cache_path=None,
        )

    # --- rule 1: explicit --legend <path> -----------------------------------
    if legend_path is not None:
        return _resolve_from_explicit_path(
            source=source,
            legend_path=legend_path,
            symbol_standard=symbol_standard,
            builtin=builtin,
            cfg=cfg,
            client=client,
            cost_tracker=cost_tracker,
            cache_path=cache_path,
        )

    # --- rule 2: --legend-pages ---------------------------------------------
    if legend_pages is not None:
        return _resolve_from_pages(
            source=source,
            page_indices=legend_pages,
            symbol_standard=symbol_standard,
            builtin=builtin,
            cfg=cfg,
            client=client,
            cost_tracker=cost_tracker,
            cache_path=cache_path,
        )

    # --- rule 3: --legend-region --------------------------------------------
    if legend_region is not None:
        return _resolve_from_region(
            source=source,
            region=legend_region,
            symbol_standard=symbol_standard,
            builtin=builtin,
            cfg=cfg,
            client=client,
            cost_tracker=cost_tracker,
            cache_path=cache_path,
        )

    # --- rule 5 (default): auto-detect --------------------------------------
    return _resolve_auto(
        source=source,
        symbol_standard=symbol_standard,
        builtin=builtin,
        cfg=cfg,
        client=client,
        cost_tracker=cost_tracker,
        cache_path=cache_path,
    )


# ---------------------------------------------------------------------------
# Per-rule helpers
# ---------------------------------------------------------------------------


def _finalise(
    *,
    extracted: LegendPack,
    builtin: LegendPack,
    symbol_standard: SymbolStandard,
    cfg_pid: PidConfig,
    source_label: str,
    cache_path: Optional[Path],
) -> LegendResolution:
    """Persist extracted, merge with built-in (extracted wins), budget-split."""
    persisted = _persist(cache_path, extracted)
    merged = extracted.merge(builtin)
    # Merge does not overwrite `standard`; force it to the caller-requested
    # value so downstream consumers always see a concrete standard.
    merged = LegendPack(
        schema_version=merged.schema_version,
        source_hash=merged.source_hash,
        source_ref=merged.source_ref,
        standard=symbol_standard,
        entries=merged.entries,
        notes=merged.notes,
    )
    return LegendResolution(
        pack=merged,
        budget=apply_budget(merged, cfg_pid),
        source=source_label,
        cache_path=persisted,
    )


def _resolve_from_explicit_path(
    *,
    source: DiagramSource,
    legend_path: Path,
    symbol_standard: SymbolStandard,
    builtin: LegendPack,
    cfg: Config,
    client: LLMClient,
    cost_tracker: CostTracker,
    cache_path: Optional[Path],
) -> LegendResolution:
    if not legend_path.exists():
        raise FileNotFoundError(f"--legend file not found: {legend_path}")
    src_hash = compute_source_hash(path=legend_path)

    cached = _load_cached(cache_path, src_hash)
    if cached is not None:
        return _finalise(
            extracted=cached,
            builtin=builtin,
            symbol_standard=symbol_standard,
            cfg_pid=cfg.pid,
            source_label="cache_hit",
            cache_path=cache_path,
        )

    # Extract: load the legend file as its own DiagramSource; walk every page.
    from diagex.vision.loader import load as _load  # local import; avoids cycle

    legend_source = _load(legend_path, tiling=cfg.tiling, scan_cfg=cfg.scan)
    all_entries: list[LegendEntry] = []
    notes = ""
    for page in iter_pages(legend_source):
        try:
            entries = _extract_from_page(
                page=page,
                region=None,
                client=client,
                cost_tracker=cost_tracker,
                cfg=cfg,
            )
        except Exception as exc:
            notes = f"extraction failed on page {page.page_index}: {exc}".strip()
            continue
        all_entries.extend(entries)

    extracted = LegendPack(
        source_hash=src_hash,
        source_ref=f"file:{legend_path.name}",
        standard=symbol_standard,
        entries=_dedupe(all_entries),
        notes=notes,
    )
    if not extracted.entries and not notes:
        extracted.notes = "no legend entries extracted"
    return _finalise(
        extracted=extracted,
        builtin=builtin,
        symbol_standard=symbol_standard,
        cfg_pid=cfg.pid,
        source_label="explicit_file",
        cache_path=cache_path,
    )


def _resolve_from_pages(
    *,
    source: DiagramSource,
    page_indices: list[int],
    symbol_standard: SymbolStandard,
    builtin: LegendPack,
    cfg: Config,
    client: LLMClient,
    cost_tracker: CostTracker,
    cache_path: Optional[Path],
) -> LegendResolution:
    pages = _iter_legend_pages(source, page_indices)
    if not pages:
        raise ValueError(f"--legend-pages {page_indices} not found in {source.path.name}")

    # Hash over concatenated page PNGs (stable: same page list -> same hash).
    page_pngs = [_page_png_bytes(p) for p in pages]
    src_hash = compute_source_hash(page_bytes=page_pngs)

    cached = _load_cached(cache_path, src_hash)
    if cached is not None:
        return _finalise(
            extracted=cached,
            builtin=builtin,
            symbol_standard=symbol_standard,
            cfg_pid=cfg.pid,
            source_label="cache_hit",
            cache_path=cache_path,
        )

    all_entries: list[LegendEntry] = []
    notes = ""
    for page in pages:
        try:
            entries = _extract_from_page(
                page=page,
                region=None,
                client=client,
                cost_tracker=cost_tracker,
                cfg=cfg,
            )
        except Exception as exc:
            notes = f"extraction failed on page {page.page_index}: {exc}".strip()
            continue
        all_entries.extend(entries)

    extracted = LegendPack(
        source_hash=src_hash,
        source_ref=f"{source.path.stem}#pages={','.join(str(i) for i in page_indices)}",
        standard=symbol_standard,
        entries=_dedupe(all_entries),
        notes=notes,
    )
    return _finalise(
        extracted=extracted,
        builtin=builtin,
        symbol_standard=symbol_standard,
        cfg_pid=cfg.pid,
        source_label="explicit_pages",
        cache_path=cache_path,
    )


def _resolve_from_region(
    *,
    source: DiagramSource,
    region: tuple[int, int, int, int, int],
    symbol_standard: SymbolStandard,
    builtin: LegendPack,
    cfg: Config,
    client: LLMClient,
    cost_tracker: CostTracker,
    cache_path: Optional[Path],
) -> LegendResolution:
    page_idx, x, y, w, h = region
    pages = _iter_legend_pages(source, [page_idx])
    if not pages:
        raise ValueError(f"--legend-region page {page_idx} not found in {source.path.name}")
    page = pages[0]

    crop = _crop_region(page, x, y, w, h)
    buf = io.BytesIO()
    crop.save(buf, format="PNG")
    src_hash = compute_source_hash(region_bytes=buf.getvalue())

    cached = _load_cached(cache_path, src_hash)
    if cached is not None:
        return _finalise(
            extracted=cached,
            builtin=builtin,
            symbol_standard=symbol_standard,
            cfg_pid=cfg.pid,
            source_label="cache_hit",
            cache_path=cache_path,
        )

    try:
        entries = _extract_from_page(
            page=page,
            region=(x, y, w, h),
            client=client,
            cost_tracker=cost_tracker,
            cfg=cfg,
        )
        notes = ""
    except Exception as exc:
        entries = []
        notes = f"extraction failed: {exc}"

    extracted = LegendPack(
        source_hash=src_hash,
        source_ref=f"{source.path.stem}#region=p{page_idx}:{x},{y},{w},{h}",
        standard=symbol_standard,
        entries=_dedupe(entries),
        notes=notes,
    )
    return _finalise(
        extracted=extracted,
        builtin=builtin,
        symbol_standard=symbol_standard,
        cfg_pid=cfg.pid,
        source_label="explicit_region",
        cache_path=cache_path,
    )


def _resolve_auto(
    *,
    source: DiagramSource,
    symbol_standard: SymbolStandard,
    builtin: LegendPack,
    cfg: Config,
    client: LLMClient,
    cost_tracker: CostTracker,
    cache_path: Optional[Path],
) -> LegendResolution:
    """Default path: classify each page, extract detected legends, merge."""
    detected: list[tuple[DiagramPage, Optional[tuple[int, int, int, int]]]] = []
    detected_page_bytes: list[bytes] = []
    for page in iter_pages(source):
        is_legend, bbox = _auto_detect_page(
            page=page,
            client=client,
            cost_tracker=cost_tracker,
        )
        if is_legend:
            detected.append((page, bbox))
            detected_page_bytes.append(_page_png_bytes(page))

    if not detected:
        merged = LegendPack(
            standard=symbol_standard,
            source_ref=f"{source.path.stem}#no-legend-detected",
            notes="auto-detect found no legend page",
        ).merge(builtin)
        return LegendResolution(
            pack=merged,
            budget=apply_budget(merged, cfg.pid),
            source="built_in_only",
            cache_path=None,
        )

    # Cache key includes the detected page bytes AND each bbox (or 'full')
    # so changing either forces re-extraction.
    h = hashlib.sha256()
    for (_, bbox), b in zip(detected, detected_page_bytes):
        h.update(len(b).to_bytes(4, "big"))
        h.update(b)
        marker = b"full" if bbox is None else f"{bbox[0]},{bbox[1]},{bbox[2]},{bbox[3]}".encode()
        h.update(len(marker).to_bytes(2, "big"))
        h.update(marker)
    src_hash = h.hexdigest()

    cached = _load_cached(cache_path, src_hash)
    if cached is not None:
        return _finalise(
            extracted=cached,
            builtin=builtin,
            symbol_standard=symbol_standard,
            cfg_pid=cfg.pid,
            source_label="cache_hit",
            cache_path=cache_path,
        )

    all_entries: list[LegendEntry] = []
    notes_parts: list[str] = []
    for page, bbox in detected:
        try:
            entries = _extract_from_page(
                page=page,
                region=bbox,
                client=client,
                cost_tracker=cost_tracker,
                cfg=cfg,
            )
        except Exception as exc:
            notes_parts.append(f"page {page.page_index}: {exc}")
            continue
        all_entries.extend(entries)

    extracted = LegendPack(
        source_hash=src_hash,
        source_ref=f"{source.path.stem}#auto-detected",
        standard=symbol_standard,
        entries=_dedupe(all_entries),
        notes="; ".join(notes_parts),
    )
    return _finalise(
        extracted=extracted,
        builtin=builtin,
        symbol_standard=symbol_standard,
        cfg_pid=cfg.pid,
        source_label="auto_detected",
        cache_path=cache_path,
    )


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------


def _dedupe(entries: list[LegendEntry]) -> list[LegendEntry]:
    """Dedupe on case-folded label, preserving first occurrence order."""
    seen: set[str] = set()
    out: list[LegendEntry] = []
    for e in entries:
        key = e.label.strip().lower()
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(e)
    return out
