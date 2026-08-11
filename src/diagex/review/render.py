"""Stable source and inference-frame page assets for the review UI."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import fitz
from PIL import Image

from diagex.config import ScanConfig, load_config
from diagex.vision.loader import iter_pages, load
from diagex.vision.scan_preprocess import preprocess_scan


def _raw_pdf_page(doc: fitz.Document, index: int, dpi: float) -> Image.Image:
    page = doc[index]
    pix = page.get_pixmap(matrix=fitz.Matrix(dpi / 72.0, dpi / 72.0), alpha=False)
    mode = "RGBA" if pix.alpha else ("L" if pix.n == 1 else "RGB")
    return Image.frombytes(mode, (pix.width, pix.height), pix.samples)


def prepare_page_assets(
    source_path: Path,
    pages_dir: Path,
    *,
    cached: list[dict[str, Any]] | None = None,
    expected: dict[str, Any] | None = None,
) -> list[dict[str, Any]]:
    """Render source + extraction-frame PNGs, reusing a complete cache."""
    pages_dir.mkdir(parents=True, exist_ok=True)
    if cached and all(
        (pages_dir / page["source_image"]).is_file()
        and (pages_dir / page["inference_image"]).is_file()
        for page in cached
    ):
        return cached

    cfg = load_config()
    expected_pages = (expected or {}).get("pages") or []
    scan_values = (expected or {}).get("scan") or {}
    scan_cfg = ScanConfig(
        deskew=bool(scan_values.get("deskew", cfg.scan.deskew)),
        contrast=bool(scan_values.get("contrast", cfg.scan.contrast)),
        despeckle=bool(scan_values.get("despeckle", cfg.scan.despeckle)),
    )
    processed_pages = [] if expected_pages else list(
        iter_pages(load(source_path, tiling=cfg.tiling, scan_cfg=cfg.scan))
    )
    pdf_doc = fitz.open(source_path) if source_path.suffix.lower() == ".pdf" else None
    original_image = None if pdf_doc is not None else Image.open(source_path)
    try:
        records: list[dict[str, Any]] = []
        page_specs = expected_pages or [
            {
                "page_index": page.page_index,
                "width": page.width,
                "height": page.height,
                "dpi": page.dpi,
                "effective_dpi": page.effective_dpi,
                "is_scanned": page.is_scanned,
                "rotation_deg": page.rotation_deg,
                "source_ref": page.source_ref,
                "_image": page.image,
            }
            for page in processed_pages
        ]
        for spec in page_specs:
            page_index = int(spec["page_index"])
            source_name = f"p{page_index:04d}.source.png"
            inference_name = f"p{page_index:04d}.inference.png"
            if pdf_doc is not None:
                raw = _raw_pdf_page(pdf_doc, page_index, float(spec["dpi"]))
            else:
                assert original_image is not None
                raw = original_image.convert("RGB")
                expected_size = (int(spec["width"]), int(spec["height"]))
                if raw.size != expected_size:
                    raw = raw.resize(expected_size, Image.Resampling.BILINEAR)
            processed = spec.get("_image")
            if processed is None:
                processed = preprocess_scan(raw, scan_cfg).image if spec.get("is_scanned") else raw.copy()
            raw.save(pages_dir / source_name)
            processed.save(pages_dir / inference_name)
            records.append(
                {
                    "page_index": page_index,
                    "width": int(spec["width"]),
                    "height": int(spec["height"]),
                    "dpi": float(spec["dpi"]),
                    "effective_dpi": float(spec["effective_dpi"]),
                    "is_scanned": bool(spec["is_scanned"]),
                    "rotation_deg": float(spec.get("rotation_deg", 0.0)),
                    "source_ref": str(spec.get("source_ref") or source_path.stem),
                    "source_image": source_name,
                    "inference_image": inference_name,
                }
            )
        return records
    finally:
        if pdf_doc is not None:
            pdf_doc.close()
        if original_image is not None:
            original_image.close()
