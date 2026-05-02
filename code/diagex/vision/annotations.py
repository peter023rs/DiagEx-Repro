"""Spec §5.4 — AnnotationStore + runtime-side projection helper.

The agent emits annotations with `bbox_local` and `endpoints[i].{x,y}_local`;
`fill_globals` projects them into page-pixel space and sets `on_view_edge`
within 4 px of any view boundary.
"""

from __future__ import annotations

from collections import defaultdict
from typing import Any, Iterable

from diagex.vision.models import Annotation, AnnotationId, BBox, Kind, Point
from diagex.vision.views import ViewInfo, project_point, project_to_global

# Spec §5.4: "within 4 px of any view boundary."
EDGE_EPS_PX = 4


class AnnotationStore:
    def __init__(self) -> None:
        self._items: dict[AnnotationId, Annotation] = {}
        # Lightweight indexes to keep the common filters O(k).
        self._by_page: dict[int, list[AnnotationId]] = defaultdict(list)
        self._by_kind: dict[str, list[AnnotationId]] = defaultdict(list)

    def add(self, annotation: Annotation) -> None:
        self._items[annotation.id] = annotation
        self._by_page[annotation.page_index].append(annotation.id)
        self._by_kind[annotation.kind].append(annotation.id)

    def extend(self, annotations: Iterable[Annotation]) -> None:
        for a in annotations:
            self.add(a)

    def all(self) -> list[Annotation]:
        return list(self._items.values())

    def by_page(self, idx: int) -> list[Annotation]:
        return [self._items[aid] for aid in self._by_page.get(idx, [])]

    def by_kind(self, kind: Kind) -> list[Annotation]:
        return [self._items[aid] for aid in self._by_kind.get(kind, [])]

    def filter(self, **kwargs: Any) -> list[Annotation]:
        """Filter by any top-level attribute on Annotation (exact-match).

        Unknown keys yield an empty result rather than raising so the agent's
        `list_annotations` tool can't crash the runtime on a typo.
        """
        out: list[Annotation] = []
        for a in self._items.values():
            hit = True
            for k, v in kwargs.items():
                if not hasattr(a, k) or getattr(a, k) != v:
                    hit = False
                    break
            if hit:
                out.append(a)
        return out

    def __len__(self) -> int:
        return len(self._items)

    def __iter__(self) -> Iterable[Annotation]:
        return iter(self._items.values())


def _on_edge(view: ViewInfo, x_local: float, y_local: float, eps: int = EDGE_EPS_PX) -> bool:
    w, h = view.view_size
    return (
        x_local <= eps
        or y_local <= eps
        or x_local >= w - eps
        or y_local >= h - eps
    )


def fill_globals(annotation: Annotation, view: ViewInfo) -> Annotation:
    """Project `bbox_local` / endpoints.*_local onto page-pixel space.

    Also sets `page_index` from the view's containing page (caller-provided
    earlier via the runtime) — but we leave `page_index` alone if already set.
    Mutates and returns `annotation`.
    """
    # Bbox projection.
    global_bbox = project_to_global(view, annotation.bbox_local)
    annotation.bbox_global = global_bbox

    # Endpoint projection + on_view_edge.
    projected: list[Point] = []
    for ep in annotation.endpoints:
        gx, gy = project_point(view, ep.x_local, ep.y_local)
        ep.x_global = float(gx)
        ep.y_global = float(gy)
        ep.on_view_edge = _on_edge(view, ep.x_local, ep.y_local)
        projected.append(ep)
    annotation.endpoints = projected

    # source_view / tile_id: align with the view that produced the annotation.
    sv = view.source_view
    if sv in ("overview", "tile", "region"):
        annotation.source_view = sv  # type: ignore[assignment]
    if view.tile_id is not None:
        annotation.tile_id = view.tile_id

    return annotation


def make_annotation(
    *,
    page_index: int,
    kind: Kind,
    label: str,
    bbox_local: BBox,
    view: ViewInfo,
    confidence: str = "medium",
    endpoints: list[Point] | None = None,
    **fields: Any,
) -> Annotation:
    """Convenience constructor that builds an Annotation and fills globals."""
    a = Annotation(
        page_index=page_index,
        kind=kind,
        source_view=view.source_view,  # type: ignore[arg-type]
        tile_id=view.tile_id,
        bbox_local=bbox_local,
        bbox_global=bbox_local,  # placeholder, overwritten by fill_globals
        endpoints=endpoints or [],
        label=label,
        confidence=confidence,  # type: ignore[arg-type]
        **fields,
    )
    return fill_globals(a, view)
