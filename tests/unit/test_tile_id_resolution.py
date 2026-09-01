"""Regression tests for model-rewritten tile identifiers."""

from __future__ import annotations

from PIL import Image

from diagex.agent.state import AgentState
from diagex.agent.tools import dispatch
from diagex.vision.models import BBox, DiagramPage, Tile
from diagex.vision.views import ViewProvider


def _provider(tiles: list[Tile]) -> ViewProvider:
    page = DiagramPage(
        page_index=0,
        image=Image.new("RGB", (500, 500), "white"),
        width=500,
        height=500,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        source_ref="test#page=1",
    )
    return ViewProvider(page, tiles)


def _tile(tile_id: str, *, x: int, y: int) -> Tile:
    return Tile(
        id=tile_id,
        page_index=0,
        bbox=BBox(x=x, y=y, w=100, h=100),
    )


def test_resolve_tile_id_preserves_canonical_and_accepts_unique_aliases() -> None:
    provider = _provider([
        _tile("p0-r0-c0", x=0, y=0),
        _tile("p0-r0-c1", x=2444, y=0),
        _tile("p0-r1-c0", x=0, y=863),
    ])

    assert provider.resolve_tile_id("p0-r0-c0") == "p0-r0-c0"
    assert provider.resolve_tile_id("  p0-r0-c0  ") == "p0-r0-c0"
    assert provider.resolve_tile_id("0_0") == "p0-r0-c0"
    assert provider.resolve_tile_id("0,0") == "p0-r0-c0"
    assert provider.resolve_tile_id("tile_0_1") == "p0-r0-c1"
    assert provider.resolve_tile_id("2444_0") == "p0-r0-c1"
    assert provider.resolve_tile_id("x2444_y0") == "p0-r0-c1"
    assert provider.resolve_tile_id("0_863") == "p0-r1-c0"


def test_resolve_tile_id_rejects_ambiguous_alias() -> None:
    provider = _provider([
        _tile("p0-r0-c1", x=100, y=0),
        _tile("p0-r5-c5", x=0, y=1),
    ])

    # 0_1 could mean row 0 / column 1 or bbox origin x=0 / y=1.
    assert provider.resolve_tile_id("0_1") is None


def test_get_tile_alias_uses_canonical_tracking_and_view_tag() -> None:
    provider = _provider([_tile("p0-r0-c0", x=0, y=0)])
    state = AgentState(question="extract", page=provider.page)
    state.required_tile_ids = {"p0-r0-c0"}

    result = dispatch("get_tile", {"tile_id": "tile_0_0"}, state, provider)

    assert result.is_error is False
    assert state.tile_fetch_counts == {"p0-r0-c0": 1}
    assert state.last_view_tag == "tile:p0-r0-c0"
    assert "resolved to canonical" in result.content[0]["text"]


def test_unknown_tile_id_is_recoverable_and_lists_valid_ids() -> None:
    provider = _provider([_tile("p0-r0-c0", x=0, y=0)])
    state = AgentState(question="extract", page=provider.page)

    result = dispatch("get_tile", {"tile_id": "made-up"}, state, provider)

    assert result.is_error is True
    assert "unknown or ambiguous" in result.content[0]["text"]
    assert "p0-r0-c0" in result.content[0]["text"]
    assert state.tile_fetch_counts == {}
    assert state.last_view_tag is None


def test_alias_cannot_bypass_canonical_fetch_limit() -> None:
    provider = _provider([_tile("p0-r0-c0", x=0, y=0)])
    state = AgentState(question="extract", page=provider.page)
    state.tile_fetch_counts["p0-r0-c0"] = 3

    result = dispatch("get_tile", {"tile_id": "0_0"}, state, provider)

    assert result.is_error is True
    assert "already fetched 3 times" in result.content[0]["text"]
    assert state.tile_fetch_counts == {"p0-r0-c0": 3}
