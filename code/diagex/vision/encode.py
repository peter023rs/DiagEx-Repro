"""Size-safe encoding of PIL images to Anthropic image content-blocks.

The Anthropic API rejects inline images whose decoded bytes exceed 5 MiB
(``messages.*.content.*.image.source.base64: image exceeds 5 MB maximum``).
``vision/views.py`` caps pixel dimensions at 2000 px per side, but a detail-
rich 2000×2000 PNG can still exceed that byte cap. This module is the single
choke-point that guarantees the encoded bytes fit.

Strategy:
  1. PNG (lossless) — the default for diagrams.
  2. If PNG > limit, JPEG q=90 (still high-fidelity for visual reasoning).
  3. If JPEG q=90 > limit, iteratively downscale the image by 0.85× and
     retry JPEG until it fits or pixel dims fall below 256 px.
"""

from __future__ import annotations

import base64
import io
from typing import Any

from PIL import Image

# Anthropic's documented inline-image cap is 5 MiB on the decoded bytes.
# Leave a small safety margin for SDK serialization overhead.
ANTHROPIC_IMAGE_BYTE_LIMIT: int = 5 * 1024 * 1024
_SAFETY_MARGIN: int = 64 * 1024  # 64 KiB
_EFFECTIVE_LIMIT: int = ANTHROPIC_IMAGE_BYTE_LIMIT - _SAFETY_MARGIN

_MIN_PIXEL_DIM: int = 256
_DOWNSCALE_FACTOR: float = 0.85
_JPEG_QUALITY: int = 90


def _png_bytes(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="PNG", optimize=False)
    return buf.getvalue()


def _jpeg_bytes(img: Image.Image, quality: int = _JPEG_QUALITY) -> bytes:
    buf = io.BytesIO()
    rgb = img.convert("RGB") if img.mode not in ("RGB", "L") else img
    rgb.save(buf, format="JPEG", quality=quality, optimize=True)
    return buf.getvalue()


def encode_image_block(
    img: Image.Image,
    *,
    max_bytes: int = _EFFECTIVE_LIMIT,
) -> dict[str, Any]:
    """Encode `img` as an Anthropic image content-block fitting under
    `max_bytes` decoded bytes.

    Tries PNG first, then JPEG q=90, then progressively downscaled JPEG.
    """
    data = _png_bytes(img)
    if len(data) <= max_bytes:
        return _block(data, "image/png")

    data = _jpeg_bytes(img)
    if len(data) <= max_bytes:
        return _block(data, "image/jpeg")

    # Pathological case: even JPEG q=90 at full resolution is too big.
    # Downscale until it fits.
    cur = img
    while max(cur.size) > _MIN_PIXEL_DIM:
        new_size = (
            max(1, int(cur.size[0] * _DOWNSCALE_FACTOR)),
            max(1, int(cur.size[1] * _DOWNSCALE_FACTOR)),
        )
        cur = cur.resize(new_size, Image.BILINEAR)
        data = _jpeg_bytes(cur)
        if len(data) <= max_bytes:
            return _block(data, "image/jpeg")
    return _block(data, "image/jpeg")


def _block(data: bytes, media_type: str) -> dict[str, Any]:
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": base64.standard_b64encode(data).decode("ascii"),
        },
    }
