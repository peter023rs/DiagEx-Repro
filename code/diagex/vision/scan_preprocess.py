"""Minimal, non-perceptual preprocessing for scanned pages (spec §12.1.6).

Pillow + numpy only — classical CV dependencies are forbidden (see CLAUDE.md).
Each routine is cheap and idempotent; the orchestrator decides what to apply.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from PIL import Image

from diagex.config import ScanConfig


@dataclass
class PreprocessResult:
    image: Image.Image
    rotation_deg: float = 0.0


def _to_gray_array(img: Image.Image) -> np.ndarray:
    if img.mode != "L":
        g = img.convert("L")
    else:
        g = img
    return np.asarray(g, dtype=np.uint8)


def _row_variance(arr: np.ndarray) -> float:
    # High row-sum variance == text/structure lines align with image rows.
    row_sums = arr.sum(axis=1).astype(np.float64)
    return float(row_sums.var())


# Minimum fractional variance improvement over 0° that we require before
# trusting a non-zero best-angle. On vector P&IDs rendered as JPEG the
# row-variance objective is dominated by noise; without this margin the
# sweep snaps to ±step_deg on already-aligned pages.
DESKEW_VARIANCE_MARGIN = 0.02


def _white_fill(mode: str) -> int | tuple[int, ...]:
    # PIL treats an int fillcolor on RGB as the R channel only, so
    # fillcolor=255 on an RGB image leaves pure red in the exposed corners.
    if mode == "L":
        return 255
    if mode == "RGB":
        return (255, 255, 255)
    if mode == "RGBA":
        return (255, 255, 255, 255)
    return 255


def estimate_skew_deg(img: Image.Image, search_range_deg: float = 5.0, step_deg: float = 0.5) -> float:
    """Find rotation angle maximising horizontal-projection variance.

    Subsamples to speed up the sweep — full-res variance would be identical in sign.
    Returns the angle in degrees (positive == rotate counter-clockwise to deskew).
    Returns 0.0 when the sweep result is unreliable: no margin over 0°, or the
    optimum sits at the search boundary (objective is monotonic in the window,
    so the "peak" is an artifact, not a real skew).
    """
    # Subsample to <= 1000 px on long side for speed.
    src = img
    if max(src.size) > 1000:
        scale = 1000 / max(src.size)
        new_size = (max(1, int(src.size[0] * scale)), max(1, int(src.size[1] * scale)))
        src = src.resize(new_size, Image.BILINEAR)

    fill = _white_fill(src.mode)

    def _variance_at(angle: float) -> float:
        rotated = src.rotate(angle, resample=Image.BILINEAR, fillcolor=fill)
        arr = _to_gray_array(rotated)
        return _row_variance(255 - arr)

    zero_var = _variance_at(0.0)
    best_angle = 0.0
    best_var = zero_var
    angle = -search_range_deg
    while angle <= search_range_deg + 1e-9:
        var = _variance_at(angle)
        if var > best_var:
            best_var = var
            best_angle = angle
        angle += step_deg

    if best_angle == 0.0 or zero_var <= 0.0:
        return 0.0
    if (best_var - zero_var) / zero_var < DESKEW_VARIANCE_MARGIN:
        return 0.0
    if abs(abs(best_angle) - search_range_deg) < 1e-9:
        return 0.0
    return best_angle


def deskew(img: Image.Image, step_deg: float = 0.5) -> tuple[Image.Image, float]:
    angle = estimate_skew_deg(img, step_deg=step_deg)
    # Treat anything within one sweep step of zero as noise — the sweep resolves
    # at step_deg so sub-step "precision" has no basis.
    if abs(angle) <= step_deg:
        return img, 0.0
    # Rotate at full resolution; fill with white so downstream tiles look clean.
    return img.rotate(angle, resample=Image.BICUBIC, fillcolor=_white_fill(img.mode), expand=False), angle


def contrast_stretch(img: Image.Image, low_pct: float = 2.0, high_pct: float = 98.0) -> Image.Image:
    arr = np.asarray(img)
    if arr.ndim == 2:
        lo, hi = np.percentile(arr, [low_pct, high_pct])
        if hi <= lo:
            return img
        stretched = np.clip((arr.astype(np.float32) - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
        return Image.fromarray(stretched, mode="L")
    # RGB / RGBA: stretch each channel independently (alpha left alone).
    out = arr.copy()
    channels = 3 if arr.shape[-1] >= 3 else arr.shape[-1]
    for c in range(channels):
        ch = arr[..., c]
        lo, hi = np.percentile(ch, [low_pct, high_pct])
        if hi <= lo:
            continue
        out[..., c] = np.clip((ch.astype(np.float32) - lo) * 255.0 / (hi - lo), 0, 255).astype(np.uint8)
    return Image.fromarray(out, mode=img.mode)


def _noise_variance(img: Image.Image) -> float:
    # Laplacian-ish high-pass via numpy diff; CV-free.
    arr = _to_gray_array(img).astype(np.float32)
    dx = arr[:, 1:] - arr[:, :-1]
    dy = arr[1:, :] - arr[:-1, :]
    # Use mean of squared gradients as a proxy for noise energy.
    return float((dx * dx).mean() + (dy * dy).mean())


def despeckle(img: Image.Image, noise_threshold: float = 500.0) -> Image.Image:
    """3x3 median only if noise exceeds threshold — median on clean scans blurs text."""
    if _noise_variance(img) < noise_threshold:
        return img
    from PIL import ImageFilter
    return img.filter(ImageFilter.MedianFilter(size=3))


def preprocess_scan(img: Image.Image, cfg: ScanConfig) -> PreprocessResult:
    rotation = 0.0
    out = img
    if cfg.deskew:
        out, rotation = deskew(out)
    if cfg.contrast:
        out = contrast_stretch(out)
    if cfg.despeckle:
        out = despeckle(out)
    return PreprocessResult(image=out, rotation_deg=rotation)
