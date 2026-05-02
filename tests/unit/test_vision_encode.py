"""Regression tests for ``vision.encode`` — guards Anthropic's 5 MiB inline-
image cap. The cap caused a Phase-1 query failure on `two-tanks-q2 trial=2`
(2026-04-27) when a detail-rich 2000×2000 PNG hit 5,359,388 bytes."""

from __future__ import annotations

import base64

import numpy as np
from PIL import Image

from diagex.vision.encode import (
    ANTHROPIC_IMAGE_BYTE_LIMIT,
    encode_image_block,
)


def _block_bytes(block: dict) -> int:
    return len(base64.standard_b64decode(block["source"]["data"]))


def test_small_image_round_trips_as_png() -> None:
    img = Image.new("RGB", (32, 32), color=(255, 0, 0))
    block = encode_image_block(img)
    assert block["source"]["media_type"] == "image/png"
    assert _block_bytes(block) < 1024


def test_high_entropy_large_image_fits_under_cap() -> None:
    """Random noise at 2000x2000 PNG-encodes to ~12 MB, exceeding the cap.
    The encoder must fall back to JPEG and produce a block that fits."""
    rng = np.random.default_rng(seed=0)
    arr = rng.integers(0, 256, size=(2000, 2000, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    block = encode_image_block(img)
    assert _block_bytes(block) < ANTHROPIC_IMAGE_BYTE_LIMIT
    # JPEG fallback expected for this entropy regime.
    assert block["source"]["media_type"] == "image/jpeg"


def test_explicit_max_bytes_forces_jpeg_fallback() -> None:
    """High-entropy 500x500 PNG-encodes to ~750 KB — well over a 50 KiB cap.
    The encoder must downshift to JPEG."""
    rng = np.random.default_rng(seed=42)
    arr = rng.integers(0, 256, size=(500, 500, 3), dtype=np.uint8)
    img = Image.fromarray(arr, mode="RGB")
    block = encode_image_block(img, max_bytes=50_000)
    assert _block_bytes(block) <= 50_000
    assert block["source"]["media_type"] == "image/jpeg"


def test_block_shape_matches_anthropic_schema() -> None:
    img = Image.new("RGB", (16, 16), color=(0, 0, 0))
    block = encode_image_block(img)
    assert block["type"] == "image"
    src = block["source"]
    assert src["type"] == "base64"
    assert src["media_type"] in ("image/png", "image/jpeg")
    assert isinstance(src["data"], str) and len(src["data"]) > 0
