"""Spec §5.3 — views offered to the agent.

ViewProvider encapsulates the three view types (overview / tile / region) and
records the page-to-view transform so the runtime can project local -> global
coordinates. Agent sees only the view; math stays here.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from PIL import Image

from diagex.vision.models import BBox, DiagramPage, Tile, TileId

# Anthropic API many-image-batch limit (any side; per-image).
# Larger crops fail with "image dimensions exceed max allowed size for
# many-image requests: 2000 pixels". Cap proactively to avoid 400s.
_API_MAX_DIM: int = 2000


def _cap_dim(img: Image.Image, max_dim: int) -> tuple[Image.Image, float, float]:
    """Downsample img so its longer side <= max_dim. Returns (img, sx, sy)
    where sx/sy are the view-px / source-px scale factors (1.0 if no resize).
    """
    w, h = img.size
    long_side = max(w, h)
    if long_side <= max_dim:
        return img, 1.0, 1.0
    scale = max_dim / float(long_side)
    new_w = max(1, int(w * scale))
    new_h = max(1, int(h * scale))
    resized = img.resize((new_w, new_h), Image.BILINEAR)
    return resized, new_w / float(w), new_h / float(h)


@dataclass
class ViewInfo:
    """Transform from view-local pixel space to page-global pixel space.

    global = origin + local / scale. (scale < 1 means view is downsampled
    relative to the page.)
    """

    source_view: str               # "overview" | "tile" | "region"
    origin: tuple[int, int]        # page-pixel top-left of what the view covers
    scale_x: float                 # view_px / page_px along x
    scale_y: float                 # view_px / page_px along y
    view_size: tuple[int, int]     # (w, h) of the view image in view pixels
    page_bbox: BBox                # page-pixel bbox the view covers
    tile_id: TileId | None = None


class ViewProvider:
    def __init__(self, page: DiagramPage, tiles: list[Tile]):
        self.page = page
        self.tiles = tiles
        self._tiles_by_id: dict[TileId, Tile] = {t.id: t for t in tiles}
        self._overview_cache: tuple[Image.Image, ViewInfo] | None = None

    # --- views ---------------------------------------------------------------

    def get_overview(self, max_dim: int = 2000) -> tuple[Image.Image, ViewInfo]:
        if self._overview_cache is not None:
            cached_img, cached_info = self._overview_cache
            if max(cached_info.view_size) == max_dim or max(cached_img.size) <= max_dim:
                return cached_img, cached_info

        src: Image.Image | None = self.page.image
        if src is None:
            raise ValueError("DiagramPage.image is None; cannot produce overview")

        w, h = src.size
        long_side = max(w, h)
        if long_side <= max_dim:
            view_img = src.copy()
            scale = 1.0
        else:
            scale = max_dim / long_side
            new_size = (max(1, int(w * scale)), max(1, int(h * scale)))
            view_img = src.resize(new_size, Image.BILINEAR)

        info = ViewInfo(
            source_view="overview",
            origin=(0, 0),
            scale_x=view_img.size[0] / max(1, w),
            scale_y=view_img.size[1] / max(1, h),
            view_size=view_img.size,
            page_bbox=BBox(x=0, y=0, w=w, h=h),
        )
        self._overview_cache = (view_img, info)
        return view_img, info

    def get_tile(self, tile_id: TileId) -> tuple[Image.Image, ViewInfo]:
        t = self._tiles_by_id.get(tile_id)
        if t is None:
            raise KeyError(f"Unknown tile_id: {tile_id}")
        img: Image.Image | None = t.image
        if img is None:
            # Recrop from page if the tile's image wasn't materialised.
            if self.page.image is None:
                raise ValueError(f"Tile {tile_id} has no image and page has no image")
            img = self.page.image.crop(
                (t.bbox.x, t.bbox.y, t.bbox.x2, t.bbox.y2)
            )
        # Cap at API-friendly max dim (Anthropic many-image batch limit = 2000px).
        img, scale_x, scale_y = _cap_dim(img, _API_MAX_DIM)
        info = ViewInfo(
            source_view="tile",
            origin=(t.bbox.x, t.bbox.y),
            scale_x=scale_x,
            scale_y=scale_y,
            view_size=img.size,
            page_bbox=BBox(x=t.bbox.x, y=t.bbox.y, w=t.bbox.w, h=t.bbox.h),
            tile_id=tile_id,
        )
        return img, info

    def resolve_tile_id(self, requested_id: str) -> TileId | None:
        """Resolve a model-supplied tile identifier without guessing.

        Canonical IDs returned by :meth:`list_tiles` always win.  Some models
        rewrite opaque IDs such as ``p0-r0-c0`` into row/column (``0_0`` or
        ``tile_0_0``) or bbox-origin (``x0_y0``) notation.  Accept those forms
        only when every supported interpretation points to the same tile.
        Ambiguous and unknown values deliberately remain unresolved.
        """
        raw = str(requested_id)
        if raw in self._tiles_by_id:
            return raw

        value = raw.strip()
        if value in self._tiles_by_id:
            return value

        candidates: set[TileId] = set()

        # Explicit bbox-origin form, e.g. x2444_y0.
        origin_match = re.fullmatch(r"x(\d+)[_,-]?y(\d+)", value, re.IGNORECASE)
        if origin_match:
            x, y = (int(part) for part in origin_match.groups())
            candidates.update(
                tile.id for tile in self.tiles
                if tile.bbox.x == x and tile.bbox.y == y
            )
        else:
            # Gemini has emitted 0_0, 0,0, tile_0_0, and bbox origins such as
            # 2444_0.  Evaluate both possible meanings and accept only a
            # unique result.
            pair_match = re.fullmatch(
                r"(?:tile[_-]?)?(\d+)\s*[_,]\s*(\d+)",
                value,
                re.IGNORECASE,
            )
            if pair_match:
                first, second = (int(part) for part in pair_match.groups())
                row_col_id = f"p{self.page.page_index}-r{first}-c{second}"
                if row_col_id in self._tiles_by_id:
                    candidates.add(row_col_id)
                candidates.update(
                    tile.id for tile in self.tiles
                    if tile.bbox.x == first and tile.bbox.y == second
                )

        if len(candidates) == 1:
            return next(iter(candidates))
        return None

    def get_region(self, x: int, y: int, w: int, h: int) -> tuple[Image.Image, ViewInfo]:
        if self.page.image is None:
            raise ValueError("DiagramPage.image is None; cannot produce region")
        # Clip to page bounds so the agent cannot request off-canvas pixels.
        x0 = max(0, int(x))
        y0 = max(0, int(y))
        x1 = min(self.page.width, int(x) + int(w))
        y1 = min(self.page.height, int(y) + int(h))
        if x1 <= x0 or y1 <= y0:
            raise ValueError(f"Empty region: {(x, y, w, h)} on page {self.page.width}x{self.page.height}")
        img = self.page.image.crop((x0, y0, x1, y1))
        # Cap at API-friendly max dim. The LLM may request crops bigger than
        # the API's per-image limit (2000px any side); downsample so the
        # request still succeeds.
        img, scale_x, scale_y = _cap_dim(img, _API_MAX_DIM)
        info = ViewInfo(
            source_view="region",
            origin=(x0, y0),
            scale_x=scale_x,
            scale_y=scale_y,
            view_size=img.size,
            page_bbox=BBox(x=x0, y=y0, w=x1 - x0, h=y1 - y0),
        )
        return img, info

    def list_tiles(self) -> list[dict[str, Any]]:
        """Metadata-only listing for the agent's planning step (no images)."""
        return [
            {
                "id": t.id,
                "bbox": {"x": t.bbox.x, "y": t.bbox.y, "w": t.bbox.w, "h": t.bbox.h},
            }
            for t in self.tiles
        ]


# --- projection helpers -----------------------------------------------------


def project_point(view: ViewInfo, x_local: float, y_local: float) -> tuple[float, float]:
    """view-pixel -> page-pixel."""
    sx = view.scale_x if view.scale_x != 0 else 1.0
    sy = view.scale_y if view.scale_y != 0 else 1.0
    gx = view.origin[0] + x_local / sx
    gy = view.origin[1] + y_local / sy
    return gx, gy


def project_to_global(view: ViewInfo, local_bbox: BBox) -> BBox:
    x0, y0 = project_point(view, local_bbox.x, local_bbox.y)
    x1, y1 = project_point(view, local_bbox.x + local_bbox.w, local_bbox.y + local_bbox.h)
    gx = int(round(min(x0, x1)))
    gy = int(round(min(y0, y1)))
    gw = int(round(abs(x1 - x0)))
    gh = int(round(abs(y1 - y0)))
    return BBox(x=gx, y=gy, w=max(0, gw), h=max(0, gh))
