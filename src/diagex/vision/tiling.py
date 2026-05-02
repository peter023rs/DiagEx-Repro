"""Spec §5.2 — tile(page, strategy) -> list[Tile].

Tile IDs `p{page}-r{row}-c{col}` are stable across reruns. Overlap semantics:
two adjacent tiles share ONE strip of width `overlap_frac * tile_w` (not two).
Tiles never extend past the page boundary; corner tiles omit page-edge overlaps.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Protocol

from PIL import Image

from diagex.config import TilingConfig
from diagex.vision.models import BBox, DiagramPage, Tile, TileId


class TileStrategy(Protocol):
    def plan(self, page: DiagramPage) -> list[tuple[int, int, int, int]]:
        """Return a list of (x, y, w, h) tile bboxes in page-pixel space."""
        ...

    overlap_frac: float


@dataclass
class AspectAwareStrategy:
    """Default v0 strategy: sizes tiles to a token budget while covering the page."""

    max_tokens_per_tile: int = 2200
    overlap_frac: float = 0.20
    token_per_pixel: float = 1.0 / 750.0

    def _tile_dims(self, page_w: int, page_h: int) -> tuple[int, int]:
        budget_px = self.max_tokens_per_tile / self.token_per_pixel
        # Respect the page's aspect ratio to keep tiles roughly proportional.
        aspect = page_w / max(1, page_h)
        # tile_h * tile_w == budget_px; tile_w = aspect * tile_h  =>  tile_h = sqrt(budget/aspect)
        tile_h = int(math.floor(math.sqrt(budget_px / max(aspect, 1e-6))))
        tile_w = int(math.floor(aspect * tile_h))
        # Clamp: never exceed the page, but also avoid degenerate sizes.
        tile_w = max(128, min(tile_w, page_w))
        tile_h = max(128, min(tile_h, page_h))
        return tile_w, tile_h

    def plan(self, page: DiagramPage) -> list[tuple[int, int, int, int]]:
        return _plan_grid(page.width, page.height, *self._tile_dims(page.width, page.height), self.overlap_frac)


@dataclass
class FixedGridStrategy:
    """Fixed tile dimensions; used for small, predictable pages (A4 logic sheets)."""

    tile_w: int
    tile_h: int
    overlap_frac: float = 0.20

    def plan(self, page: DiagramPage) -> list[tuple[int, int, int, int]]:
        return _plan_grid(page.width, page.height, self.tile_w, self.tile_h, self.overlap_frac)


def _plan_grid(
    page_w: int,
    page_h: int,
    tile_w: int,
    tile_h: int,
    overlap_frac: float,
) -> list[tuple[int, int, int, int]]:
    """Grid layout with overlap.

    Step between tile origins is `(1 - overlap_frac) * tile_dim`. Two neighbours
    share exactly one strip of width `overlap_frac * tile_dim`. The final tile
    in each row/col is clamped so it ends at the page boundary (w/h reduced);
    it never extends past the page.
    """
    tile_w = max(1, min(tile_w, page_w))
    tile_h = max(1, min(tile_h, page_h))
    step_x = max(1, int(round(tile_w * (1.0 - overlap_frac))))
    step_y = max(1, int(round(tile_h * (1.0 - overlap_frac))))

    xs = _origins(page_w, tile_w, step_x)
    ys = _origins(page_h, tile_h, step_y)

    out: list[tuple[int, int, int, int]] = []
    for y in ys:
        for x in xs:
            w = min(tile_w, page_w - x)
            h = min(tile_h, page_h - y)
            if w <= 0 or h <= 0:
                continue
            out.append((x, y, w, h))
    return out


def _origins(extent: int, tile_extent: int, step: int) -> list[int]:
    if tile_extent >= extent:
        return [0]
    origins: list[int] = []
    x = 0
    while True:
        origins.append(x)
        if x + tile_extent >= extent:
            break
        x += step
    # If the final tile would run past the boundary, pull it back so it ends at `extent`.
    last_x = origins[-1]
    if last_x + tile_extent > extent:
        origins[-1] = max(0, extent - tile_extent)
        # Deduplicate in case the adjustment collided with the previous origin.
        if len(origins) >= 2 and origins[-1] <= origins[-2]:
            origins.pop()
    return origins


def _neighbor_ids(
    row: int,
    col: int,
    n_rows: int,
    n_cols: int,
    page_index: int,
) -> list[TileId]:
    ids: list[TileId] = []
    for dr in (-1, 0, 1):
        for dc in (-1, 0, 1):
            if dr == 0 and dc == 0:
                continue
            r = row + dr
            c = col + dc
            if 0 <= r < n_rows and 0 <= c < n_cols:
                ids.append(f"p{page_index}-r{r}-c{c}")
    return ids


def tile(page: DiagramPage, strategy: TileStrategy | None = None) -> list[Tile]:
    """Cut `page.image` into tiles per `strategy` (AspectAware default)."""
    if strategy is None:
        cfg = TilingConfig()
        strategy = AspectAwareStrategy(
            max_tokens_per_tile=cfg.max_tokens_per_tile,
            overlap_frac=cfg.overlap_frac,
            token_per_pixel=cfg.token_per_pixel,
        )

    plan = strategy.plan(page)
    if not plan:
        return []

    # Re-derive the (row, col) grid from the plan. We recompute origins so tile
    # IDs stay stable regardless of strategy implementation details.
    xs_sorted = sorted({x for (x, _, _, _) in plan})
    ys_sorted = sorted({y for (_, y, _, _) in plan})
    x_to_col = {x: c for c, x in enumerate(xs_sorted)}
    y_to_row = {y: r for r, y in enumerate(ys_sorted)}
    n_rows = len(ys_sorted)
    n_cols = len(xs_sorted)

    page_img: Image.Image | None = page.image
    tiles: list[Tile] = []
    for x, y, w, h in plan:
        row = y_to_row[y]
        col = x_to_col[x]
        tile_id = f"p{page.page_index}-r{row}-c{col}"
        crop = None
        if page_img is not None:
            crop = page_img.crop((x, y, x + w, y + h))
        bbox = BBox(x=int(x), y=int(y), w=int(w), h=int(h))
        tiles.append(
            Tile(
                id=tile_id,
                page_index=page.page_index,
                bbox=bbox,
                image=crop,
                overlap_neighbors=_neighbor_ids(row, col, n_rows, n_cols, page.page_index),
            )
        )
    return tiles
