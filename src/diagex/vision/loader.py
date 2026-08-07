"""Spec §5.1 — load(path) -> DiagramSource.

Supports PDF (via pymupdf / fitz) and single-image inputs (PNG, JPG, TIFF, WebP).
Pages stream as a generator so 200-page logic-diagram PDFs do not OOM.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path
from typing import Any

import fitz  # pymupdf
from PIL import Image

from diagex.config import ScanConfig, TilingConfig, load_config
from diagex.vision.models import DiagramPage, DiagramSource
from diagex.vision.scan_preprocess import preprocess_scan

_IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".tif", ".tiff", ".webp", ".bmp"}
_PDF_EXTS = {".pdf"}


def _source_ref(path: Path, page_index: int | None) -> str:
    stem = path.stem
    if page_index is None:
        return stem
    return f"{stem}#page={page_index + 1}"


def _adaptive_dpi(page_w_pts: float, page_h_pts: float, cfg: TilingConfig) -> float:
    """Choose DPI so max(rendered_w, rendered_h) <= max_page_dim_px."""
    target = float(cfg.target_dpi)
    max_side_pts = max(page_w_pts, page_h_pts)
    if max_side_pts <= 0:
        return target
    # pymupdf: pixels = points * dpi / 72.
    max_dpi = cfg.max_page_dim_px * 72.0 / max_side_pts
    return min(target, max_dpi)


def _pixmap_to_pil(pix: fitz.Pixmap) -> Image.Image:
    if pix.alpha:
        mode = "RGBA"
    elif pix.n == 1:
        mode = "L"
    else:
        mode = "RGB"
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def _page_has_vector_overlay(page: fitz.Page, min_text_chars: int = 40) -> bool:
    """True if the page carries meaningful vector content on top of the raster.

    Hybrid P&ID scans commonly have tag numbers / line labels as crisp vector
    text overlaid on a low-DPI background image. Clamping the render DPI to the
    raster's source DPI blurs those labels. Detect this case so the caller can
    skip the clamp.
    """
    try:
        text = page.get_text("text") or ""
    except Exception:
        text = ""
    if len(text.strip()) >= min_text_chars:
        return True
    try:
        drawings = page.get_drawings()
    except Exception:
        drawings = []
    return len(drawings) > 0


def _detect_scan_and_effective_dpi(
    page: fitz.Page,
    rendered_dpi: float,
    page_w_pts: float,
    page_h_pts: float,
) -> tuple[bool, float]:
    """A page is 'scanned' if one image covers >80% of its area.

    Effective DPI for such pages is computed from that image stream's pixel
    dimensions vs page size in points — rendering above source DPI adds no info.
    """
    try:
        images = page.get_images(full=True)
    except Exception:
        return False, rendered_dpi
    if not images:
        return False, rendered_dpi

    page_area_pts = max(page_w_pts * page_h_pts, 1.0)
    best = None
    for info in images:
        xref = info[0]
        try:
            rects = page.get_image_rects(xref)
        except Exception:
            rects = []
        if not rects:
            continue
        # Area in points of the image's placement on the page.
        rect = rects[0]
        img_area_pts = abs(rect.width * rect.height)
        coverage = img_area_pts / page_area_pts
        # info[2], info[3] are the image stream's pixel width/height.
        img_w_px = info[2] if len(info) > 2 else 0
        img_h_px = info[3] if len(info) > 3 else 0
        if best is None or coverage > best[0]:
            best = (coverage, img_w_px, img_h_px, rect)

    if best is None:
        return False, rendered_dpi
    coverage, img_w_px, img_h_px, rect = best
    if coverage < 0.80:
        return False, rendered_dpi

    # Effective DPI: image pixels per inch of placement rect on the page.
    w_in = abs(rect.width) / 72.0
    h_in = abs(rect.height) / 72.0
    dpi_candidates = []
    if w_in > 0 and img_w_px > 0:
        dpi_candidates.append(img_w_px / w_in)
    if h_in > 0 and img_h_px > 0:
        dpi_candidates.append(img_h_px / h_in)
    if not dpi_candidates:
        return True, rendered_dpi
    return True, min(dpi_candidates)


def _iter_pdf_pages(
    path: Path,
    tiling: TilingConfig,
    scan_cfg: ScanConfig,
) -> Iterator[DiagramPage]:
    # Opening the doc inside the generator keeps the handle alive only while
    # iterating; closing happens when the generator is exhausted or GC'd.
    doc = fitz.open(path)
    try:
        for i, page in enumerate(doc):
            rect = page.rect
            page_w_pts = float(rect.width)
            page_h_pts = float(rect.height)

            render_dpi = _adaptive_dpi(page_w_pts, page_h_pts, tiling)
            is_scanned, effective_dpi = _detect_scan_and_effective_dpi(
                page, render_dpi, page_w_pts, page_h_pts
            )
            # Never render above source DPI on pure scans — wastes pixels. But
            # hybrid pages (vector labels over a raster background) need the
            # full target DPI so the vector text stays legible; the upscaled
            # raster background is the accepted cost.
            has_vector_overlay = _page_has_vector_overlay(page) if is_scanned else False
            if is_scanned and not has_vector_overlay:
                render_dpi = min(render_dpi, effective_dpi)

            zoom = render_dpi / 72.0
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = _pixmap_to_pil(pix)

            rotation_deg = 0.0
            if is_scanned:
                pre = preprocess_scan(img, scan_cfg)
                img = pre.image
                rotation_deg = pre.rotation_deg

            yield DiagramPage(
                page_index=i,
                image=img,
                width=img.size[0],
                height=img.size[1],
                dpi=float(render_dpi),
                effective_dpi=float(effective_dpi if is_scanned else render_dpi),
                is_scanned=is_scanned,
                rotation_deg=rotation_deg,
                source_ref=_source_ref(path, i),
            )
    finally:
        doc.close()


def _iter_image_page(
    path: Path,
    tiling: TilingConfig,
    scan_cfg: ScanConfig,
) -> Iterator[DiagramPage]:
    img = Image.open(path)
    img.load()  # force decode now; release the file handle
    if img.mode not in ("L", "RGB", "RGBA"):
        img = img.convert("RGB")

    # Downscale if the single image exceeds the rendering budget.
    max_dim = max(img.size)
    if max_dim > tiling.max_page_dim_px:
        scale = tiling.max_page_dim_px / max_dim
        new_size = (max(1, int(img.size[0] * scale)), max(1, int(img.size[1] * scale)))
        img = img.resize(new_size, Image.BILINEAR)

    # Assume image inputs are scans — run preprocessing per config.
    pre = preprocess_scan(img, scan_cfg)

    dpi_tuple: Any = img.info.get("dpi") if hasattr(img, "info") else None
    if isinstance(dpi_tuple, tuple) and dpi_tuple:
        effective_dpi = float(dpi_tuple[0]) or float(tiling.target_dpi)
    else:
        effective_dpi = float(tiling.target_dpi)

    yield DiagramPage(
        page_index=0,
        image=pre.image,
        width=pre.image.size[0],
        height=pre.image.size[1],
        dpi=effective_dpi,
        effective_dpi=effective_dpi,
        is_scanned=True,
        rotation_deg=pre.rotation_deg,
        source_ref=_source_ref(path, None),
    )


def load(
    path: Path | str,
    tiling: TilingConfig | None = None,
    scan_cfg: ScanConfig | None = None,
) -> DiagramSource:
    """Load a PDF or image into a DiagramSource with streaming pages."""
    p = Path(path)
    if not p.exists():
        raise FileNotFoundError(f"Input not found: {p}")

    if tiling is None or scan_cfg is None:
        cfg = load_config()
        tiling = tiling or cfg.tiling
        scan_cfg = scan_cfg or cfg.scan

    ext = p.suffix.lower()
    if ext in _PDF_EXTS:
        kind: str = "pdf"
        with fitz.open(p) as doc:
            page_count = int(doc.page_count)
        iter_factory = lambda: _iter_pdf_pages(p, tiling, scan_cfg)  # noqa: E731
    elif ext in _IMAGE_EXTS:
        kind = "image"
        page_count = 1
        iter_factory = lambda: _iter_image_page(p, tiling, scan_cfg)  # noqa: E731
    else:
        raise ValueError(f"Unsupported file type: {ext}")

    metadata: dict[str, Any] = {"source_stem": p.stem, "page_count": page_count}
    # `pages` is a zero-arg callable that returns a fresh iterator per call —
    # this lets callers re-iterate (e.g. resume from checkpoint) without
    # materialising all pages up front. Pydantic stores it opaquely.
    source = DiagramSource(
        path=p,
        kind=kind,  # type: ignore[arg-type]
        pages=iter_factory,
        metadata=metadata,
    )
    return source


def iter_pages(source: DiagramSource) -> Iterator[DiagramPage]:
    """Materialise a fresh iterator over a DiagramSource's pages.

    Accepts either the generator-callable form we produce here or an already-
    materialised iterable (for tests that stub pages inline).
    """
    pages = source.pages
    if callable(pages):
        return iter(pages())
    return iter(pages)
