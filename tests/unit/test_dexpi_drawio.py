"""Unit tests for the draw.io exporter + render-drawio CLI."""

import xml.etree.ElementTree as ET
from pathlib import Path

import pytest
from typer.testing import CliRunner

from diagex.cli import app
from diagex.dexpi_schema import (
    EQUIPMENT_REGISTRY,
    INSTRUMENT_REGISTRY,
    VALVE_REGISTRY,
)
from diagex.extractors.dexpi_drawio import (
    render_graph_json_to_drawio,
    render_graph_to_drawio,
    write_drawio,
)
from diagex.vision.models import (
    BBox,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)

# ---------------------------------------------------------------------------
# Schema-table tests — every registry entry must have a working drawio_shape.
# ---------------------------------------------------------------------------


_EQUIPMENT_FALLBACK_KEYS = {"unclassified_equipment"}


def test_every_real_equipment_has_drawio_shape():
    """Every real equipment spec carries a non-empty drawio_shape."""
    missing = [
        s.key for s in EQUIPMENT_REGISTRY
        if s.key not in _EQUIPMENT_FALLBACK_KEYS and not s.drawio_shape
    ]
    assert not missing, f"equipment specs missing drawio_shape: {missing}"


def test_every_valve_has_drawio_shape():
    """Every valve spec (including 'other') carries a drawio shape."""
    missing = [s.key for s in VALVE_REGISTRY if not s.drawio_shape]
    assert not missing, f"valve specs missing drawio_shape: {missing}"


def test_drawio_shapes_use_known_namespaces():
    """Sanity check: shape strings start with mxgraph.pid* (or are subtypes thereof)."""
    seen = set()
    for s in EQUIPMENT_REGISTRY:
        if s.drawio_shape:
            seen.add(s.drawio_shape)
        seen.update(s.drawio_subtype_shapes.values())
    for s in VALVE_REGISTRY:
        if s.drawio_shape:
            seen.add(s.drawio_shape)
    bad = [v for v in seen if not v.startswith("mxgraph.pid")]
    assert not bad, f"non-mxgraph.pid shapes: {bad}"


def test_instruments_have_valid_mounting():
    """Mounting flags must be one of the four drawio-supported values."""
    valid = {"room", "field", "inaccessible", "local"}
    bad = [s.key for s in INSTRUMENT_REGISTRY if s.drawio_mounting not in valid]
    assert not bad, f"instruments with invalid mounting: {bad}"


def test_controllers_mounted_in_control_room():
    """Tagging convention: 'controller' / 'recorder' / 'alarm' draw the divider line."""
    by_key = {s.key: s for s in INSTRUMENT_REGISTRY}
    for k in ("controller", "recorder", "alarm"):
        assert by_key[k].drawio_mounting == "room", k
    for k in ("indicator", "transmitter", "element"):
        assert by_key[k].drawio_mounting == "field", k


# ---------------------------------------------------------------------------
# Renderer fixtures
# ---------------------------------------------------------------------------


def _graph_with_variety() -> ReconciledGraph:
    return ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="t1", kind="equipment", label="T-101",
                bbox_global=BBox(x=100, y=100, w=80, h=120),
                page_index=0,
                attributes={"equipment_class": "tank"},
                confidence="high",
            ),
            ReconciledNode(
                id="p1", kind="equipment", label="P-201",
                bbox_global=BBox(x=300, y=140, w=60, h=60),
                page_index=0,
                attributes={"equipment_class": "pump", "pump_type": "centrifugal"},
                confidence="medium",
            ),
            ReconciledNode(
                id="hx1", kind="equipment", label="HX-1",
                bbox_global=BBox(x=500, y=80, w=120, h=80),
                page_index=0,
                attributes={
                    "equipment_class": "heat_exchanger",
                    "heat_exchanger_type": "plate",
                },
                confidence="high",
            ),
            ReconciledNode(
                id="v1", kind="equipment", label="V-1",
                bbox_global=BBox(x=220, y=150, w=40, h=40),
                page_index=0,
                attributes={"valve_type": "gate", "actuation": "manual"},
                confidence="high",
            ),
            ReconciledNode(
                id="cv1", kind="equipment", label="CV-1",
                bbox_global=BBox(x=400, y=150, w=40, h=40),
                page_index=0,
                attributes={"valve_type": "control"},
                confidence="high",
            ),
            ReconciledNode(
                id="i1", kind="instrument", label="FIC-101",
                bbox_global=BBox(x=200, y=70, w=40, h=40),
                page_index=0,
                attributes={"instrument_function": "controller"},
                confidence="high",
            ),
            ReconciledNode(
                id="i2", kind="instrument", label="FT-101",
                bbox_global=BBox(x=260, y=70, w=40, h=40),
                page_index=0,
                attributes={"instrument_function": "transmitter"},
                confidence="low",         # exercises the dashed outline
            ),
            ReconciledNode(
                id="o1", kind="opc", label="OPC-12",
                bbox_global=BBox(x=620, y=120, w=40, h=30),
                page_index=0,
                attributes={"direction": "out"},
                confidence="high",
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e1", from_node="t1", to_node="v1", line_type="process",
                polyline_global=[(140, 160), (220, 170)],
                confidence="high",
            ),
            ReconciledEdge(
                id="e2", from_node="v1", to_node="p1", line_type="process",
                polyline_global=[(260, 170), (300, 170)],
                confidence="high",
            ),
            ReconciledEdge(
                id="e3", from_node="i1", to_node="cv1", line_type="signal_electric",
                polyline_global=[(220, 110), (420, 150)],
                confidence="medium",
            ),
        ],
    )


def _parse(xml: str) -> ET.Element:
    return ET.fromstring(xml)


def _cells(root: ET.Element) -> list[ET.Element]:
    return root.findall(".//mxCell")


# ---------------------------------------------------------------------------
# Smoke test: structure of the emitted XML.
# ---------------------------------------------------------------------------


def test_render_emits_valid_mxfile_structure():
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g, title="demo")
    root = _parse(xml)
    assert root.tag == "mxfile"
    assert root.find("./diagram") is not None
    model = root.find(".//mxGraphModel")
    assert model is not None
    # Two boilerplate cells (id 0, 1) + one per node + one per edge + title + footer.
    cells = _cells(root)
    assert len(cells) >= 2 + 8 + 3 + 2     # boilerplate, nodes, edges, title, footer

    # Two boilerplate cells.
    assert any(c.get("id") == "0" for c in cells)
    assert any(c.get("id") == "1" and c.get("parent") == "0" for c in cells)


def test_equipment_uses_correct_drawio_shape():
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    # Tank → mxgraph.pid.vessels.tank
    tank_style = cells["n-t1"].get("style")
    assert "mxgraph.pid.vessels.tank" in tank_style
    # Pump (centrifugal) → mxgraph.pid.pumps.centrifugal_pump_1
    pump_style = cells["n-p1"].get("style")
    assert "mxgraph.pid.pumps.centrifugal_pump_1" in pump_style
    # Plate heat exchanger → subtype shape
    hx_style = cells["n-hx1"].get("style")
    assert "mxgraph.pid.heat_exchangers.heat_exchanger_(plate)" in hx_style


def test_valve_resolves_to_pid2valves_with_actuator():
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    # Manual gate valve.
    gate_style = cells["n-v1"].get("style")
    assert "mxgraph.pid2valves.valve" in gate_style
    assert "valveType=gate" in gate_style
    assert "actuator=man" in gate_style
    # Control valve defaults to globe + diaphragm.
    cv_style = cells["n-cv1"].get("style")
    assert "valveType=globe" in cv_style
    assert "actuator=diaph" in cv_style


def test_instrument_uses_disc_inst_with_mounting():
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    # Controller → control-room-mounted bubble.
    ctrl_style = cells["n-i1"].get("style")
    assert "mxgraph.pid2inst.discInst" in ctrl_style
    assert "mounting=room" in ctrl_style
    # Transmitter → field-mounted bubble.
    tx_style = cells["n-i2"].get("style")
    assert "mounting=field" in tx_style


def test_low_confidence_nodes_use_opacity_not_dashing():
    """Low-confidence nodes are visually demoted via opacity, not dashing —
    `dashed=1` is reserved for line-type semantics so the two never collide
    on the same cell (which was confusing reviewers on T4750)."""
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    tx_style = cells["n-i2"].get("style")          # confidence='low'
    assert "opacity=" in tx_style
    # Crucial: low-confidence must NOT add dashed=1 (that meaning is now
    # reserved for line_type encoding on edges).
    assert "dashed=1" not in tx_style


def test_edges_carry_endpoint_and_style():
    g = _graph_with_variety()
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = _cells(root)
    edges = [c for c in cells if c.get("edge") == "1"]
    assert len(edges) == 3
    by_id = {c.get("id"): c for c in edges}
    # Process edge connects tank → valve.
    e1 = by_id["e-e1"]
    assert e1.get("source") == "n-t1"
    assert e1.get("target") == "n-v1"
    assert "strokeColor=#1f2937" in e1.get("style")
    # Signal-electric edge has dashed style + blue stroke.
    e3 = by_id["e-e3"]
    assert "dashed=1" in e3.get("style")
    assert "#2563eb" in e3.get("style")


def test_inferred_edge_gets_orthogonal_waypoints():
    """An edge with no bootstrap polyline becomes Manhattan-routed; bend points
    appear as <mxPoint> waypoints (start/end perimeter points are NOT included
    because drawio computes those from the source/target cell perimeters)."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="t1", kind="equipment", label="T-1",
                bbox_global=BBox(x=0, y=0, w=40, h=40),
                page_index=0, attributes={"equipment_class": "tank"}, confidence="high",
            ),
            ReconciledNode(
                id="t2", kind="equipment", label="T-2",
                bbox_global=BBox(x=200, y=200, w=40, h=40),
                page_index=0, attributes={"equipment_class": "tank"}, confidence="high",
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e1", from_node="t1", to_node="t2", line_type="process",
                polyline_global=[],   # inferred → router computes waypoints
                confidence="high",
            ),
        ],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    edge = next(c for c in _cells(root) if c.get("edge") == "1")
    waypoints = edge.findall(".//mxPoint")
    # Diagonal Z-route between two non-colinear bboxes → exactly two interior
    # bend points (the four-point Manhattan poly minus its perimeter ends).
    assert len(waypoints) == 2


def test_polyline_waypoints_are_projected_into_canvas_coords():
    """Bootstrap polyline coordinates must shift by the page margin so the
    waypoints land relative to the projected vertex cells, not at the original
    page-pixel origin."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="a", kind="equipment", label="A",
                bbox_global=BBox(x=500, y=500, w=20, h=20),
                page_index=0, attributes={"equipment_class": "tank"}, confidence="high",
            ),
            ReconciledNode(
                id="b", kind="equipment", label="B",
                bbox_global=BBox(x=600, y=600, w=20, h=20),
                page_index=0, attributes={"equipment_class": "tank"}, confidence="high",
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e1", from_node="a", to_node="b", line_type="process",
                polyline_global=[(550, 550)],   # one interior bend point
                confidence="high",
            ),
        ],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    edge = next(c for c in _cells(root) if c.get("edge") == "1")
    pts = edge.findall(".//mxPoint")
    # The original polyline's interior point sits at (550, 550) in page-pixel
    # space. After projection (x_min=500, margin=40), it should land at (90, 90).
    coords = [(float(p.get("x")), float(p.get("y"))) for p in pts]
    assert (90.0, 90.0) in coords, coords


def test_labels_with_quotes_produce_well_formed_xml():
    """A label containing a literal " (e.g. an inch mark like 8"-Is) must not
    break the value="..." attribute. Caught a regression on butane1."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="o1", kind="opc", label='2A~D (P-234-03016-F3D-8"-Is)',
                bbox_global=BBox(x=10, y=10, w=40, h=30),
                page_index=0, attributes={"direction": "out"}, confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    # If the quote leaks unescaped, ElementTree raises ParseError here.
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    # ElementTree decodes the &quot; back to a real " in attribute values.
    assert cells["n-o1"].get("value") == '2A~D (P-234-03016-F3D-8"-Is)'


def _geom(cell: ET.Element) -> tuple[float, float, float, float]:
    g = cell.find("mxGeometry")
    return (
        float(g.get("x")),
        float(g.get("y")),
        float(g.get("width")),
        float(g.get("height")),
    )


def test_pump_caps_at_natural_size_when_bbox_is_huge():
    """A pump stencil has natural size 60×60. Even if the agent's bbox is
    200×200, the rendered cell stays 60×60 (stencil doesn't balloon). The
    cell is centered within the original bbox."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="p1", kind="equipment", label="P-101",
                bbox_global=BBox(x=500, y=500, w=200, h=200),
                page_index=0,
                attributes={"equipment_class": "pump", "pump_type": "centrifugal"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cell = next(c for c in _cells(root) if c.get("id") == "n-p1")
    x, y, w, h = _geom(cell)
    assert (w, h) == (60.0, 60.0), (w, h)
    # Bbox top-left projects to (40, 40) (margin) since x_min=y_min=500.
    # Cell is centered: top-left at (40 + (200-60)/2, 40 + (200-60)/2) = (110, 110).
    assert x == 110.0 and y == 110.0


def test_pump_preserves_aspect_when_bbox_is_skewed():
    """Wide-and-short bbox: pump (1:1 natural) must stay 1:1, scaled to the
    shorter side, centered in the bbox."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="p1", kind="equipment", label="P-101",
                bbox_global=BBox(x=0, y=0, w=200, h=40),
                page_index=0,
                attributes={"equipment_class": "pump", "pump_type": "centrifugal"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cell = next(c for c in _cells(root) if c.get("id") == "n-p1")
    _, _, w, h = _geom(cell)
    # scale = min(200/60, 40/60, 1.0) = 0.667 → cell becomes 40×40 (1:1 preserved).
    assert w == h
    assert abs(w - 40.0) < 0.01


def test_pump_style_pins_aspect_to_fixed():
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="p1", kind="equipment", label="P",
                bbox_global=BBox(x=0, y=0, w=80, h=80),
                page_index=0,
                attributes={"equipment_class": "pump"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    style = next(c for c in _cells(root) if c.get("id") == "n-p1").get("style")
    # aspect=fixed prevents drawio from skewing the stencil if the user later
    # resizes the cell asymmetrically inside diagrams.net.
    assert "aspect=fixed" in style


def test_tank_uses_bbox_dimensions_verbatim():
    """Tanks/vessels/columns are designed to scale — drawio_natural_size is
    None, so the cell fills the agent's bbox (no auto-fit)."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="t1", kind="equipment", label="T-101",
                bbox_global=BBox(x=10, y=20, w=300, h=140),
                page_index=0,
                attributes={"equipment_class": "tank"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    _, _, w, h = _geom(next(c for c in _cells(root) if c.get("id") == "n-t1"))
    assert (w, h) == (300.0, 140.0)


def test_valve_height_grows_when_actuator_present():
    """A bare gate valve has natural 100×60; with an actuator, it grows to
    100×100 to leave room for the actuator stack on top."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="v_plain", kind="equipment", label="V1",
                bbox_global=BBox(x=0, y=0, w=200, h=200),
                page_index=0,
                attributes={"valve_type": "gate"},
                confidence="high",
            ),
            ReconciledNode(
                id="v_man", kind="equipment", label="V2",
                bbox_global=BBox(x=300, y=0, w=200, h=200),
                page_index=0,
                attributes={"valve_type": "gate", "actuation": "manual"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    _, _, plain_w, plain_h = _geom(cells["n-v_plain"])
    _, _, man_w, man_h = _geom(cells["n-v_man"])
    # 100×60 vs 100×100 — both capped at natural; bbox is 200×200 so neither grows.
    assert (plain_w, plain_h) == (100.0, 60.0)
    assert (man_w, man_h) == (100.0, 100.0)


def test_instrument_capped_at_50x50_circle():
    """Instrument bubbles render as 50×50 circles regardless of bbox size."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="i1", kind="instrument", label="FIC-101",
                bbox_global=BBox(x=0, y=0, w=120, h=120),
                page_index=0,
                attributes={"instrument_function": "controller"},
                confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    _, _, w, h = _geom(next(c for c in _cells(root) if c.get("id") == "n-i1"))
    assert (w, h) == (50.0, 50.0)


def test_opc_uses_step_shape_with_direction():
    """OPCs render as the built-in mxgraph `step` shape (rectangle with a
    directional spike), not a hexagon. Spike points east for outbound flow,
    west for inbound — matches the ISA tag-with-arrow convention."""
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="o_out", kind="opc", label="OUT",
                bbox_global=BBox(x=0, y=0, w=40, h=30),
                page_index=0, attributes={"direction": "out"}, confidence="high",
            ),
            ReconciledNode(
                id="o_in", kind="opc", label="IN",
                bbox_global=BBox(x=200, y=0, w=40, h=30),
                page_index=0, attributes={"direction": "in"}, confidence="high",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    out_style = cells["n-o_out"].get("style")
    in_style = cells["n-o_in"].get("style")
    assert "shape=step" in out_style
    assert "shape=step" in in_style
    assert "direction=east" in out_style
    assert "direction=west" in in_style
    # Sanity: no leftover hexagon style from the previous fallback.
    assert "hexagon" not in out_style + in_style


def test_legend_appears_only_for_line_types_actually_used():
    """The legend lists only the line_types present on edges in this graph
    (process-only diagrams don't carry six unused signal rows). Always
    includes a `low-confidence` row when any node/edge has confidence=low."""
    g = _graph_with_variety()           # has process + signal_electric + low-conf node
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = _cells(root)
    legend_label_values = [
        c.get("value") for c in cells
        if c.get("id", "").startswith("legend-label-")
    ]
    assert "Process" in legend_label_values
    assert "Electric signal" in legend_label_values
    # Pneumatic/capillary not used in this fixture → must not be in the legend.
    assert "Pneumatic signal" not in legend_label_values
    # Low-confidence row present (i2 is low-confidence).
    assert "Low-confidence (faded)" in legend_label_values


def test_legend_skipped_when_options_show_legend_false():
    g = _graph_with_variety()
    from diagex.extractors.dexpi_drawio import DrawioRenderOptions
    xml = render_graph_to_drawio(g, options=DrawioRenderOptions(show_legend=False))
    root = _parse(xml)
    cells = _cells(root)
    # No legend container, no legend-* cells.
    assert not any(c.get("id", "").startswith("legend") for c in cells)


def test_unclassified_equipment_falls_back_to_rectangle():
    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="x1", kind="equipment", label="???",
                bbox_global=BBox(x=10, y=10, w=40, h=40),
                page_index=0,
                attributes={"equipment_class": "unclassified_equipment"},
                confidence="medium",
            ),
        ],
        edges=[],
    )
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    cells = {c.get("id"): c for c in _cells(root)}
    style = cells["n-x1"].get("style")
    # No mxgraph.pid stencil — generic rectangle styling.
    assert "mxgraph.pid" not in style
    assert "rounded=0" in style


def test_empty_graph_renders_without_crashing():
    g = ReconciledGraph(source_path="empty.pdf", nodes=[], edges=[])
    xml = render_graph_to_drawio(g)
    root = _parse(xml)
    assert root.tag == "mxfile"


def test_write_drawio_creates_file(tmp_path: Path):
    g = _graph_with_variety()
    out = tmp_path / "subdir" / "out.drawio"
    write_drawio(g, out, title="demo")
    assert out.exists()
    text = out.read_text(encoding="utf-8")
    assert text.startswith("<mxfile")
    # Round-trip through ElementTree to confirm well-formed XML.
    ET.fromstring(text)


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------


def test_render_drawio_cli_writes_file(tmp_path: Path):
    g = _graph_with_variety()
    graph_json = tmp_path / "graph.json"
    graph_json.write_text(g.model_dump_json(), encoding="utf-8")

    runner = CliRunner()
    result = runner.invoke(app, ["render-drawio", str(graph_json)])
    assert result.exit_code == 0, result.stdout
    out_path = graph_json.with_suffix(".drawio")
    assert out_path.exists()
    text = out_path.read_text(encoding="utf-8")
    assert "mxgraph.pid" in text


def test_render_drawio_cli_accepts_run_dir(tmp_path: Path):
    g = _graph_with_variety()
    run_dir = tmp_path / "runs" / "abc"
    run_dir.mkdir(parents=True)
    (run_dir / "graph.json").write_text(g.model_dump_json(), encoding="utf-8")
    out = tmp_path / "out.drawio"
    runner = CliRunner()
    result = runner.invoke(app, ["render-drawio", str(run_dir), "--out", str(out)])
    assert result.exit_code == 0, result.stdout
    assert out.exists()


# ---------------------------------------------------------------------------
# End-to-end round-trip on the dexpi-reference ground-truth fixture.
# ---------------------------------------------------------------------------


def test_extract_pid_writes_pid_drawio_alongside_pid_svg(tmp_path: Path):
    """Phase 2 must emit pid.drawio next to pid.svg / graph.json so reviewers
    get the editable file by default — no extra render-drawio step needed."""
    from diagex.extractors.pid import _write_run_artefacts

    g = ReconciledGraph(
        source_path="demo.pdf",
        nodes=[
            ReconciledNode(
                id="t1", kind="equipment", label="T-101",
                bbox_global=BBox(x=10, y=10, w=80, h=80),
                page_index=0,
                attributes={"equipment_class": "tank"},
                confidence="high",
            ),
            ReconciledNode(
                id="p1", kind="equipment", label="P-101",
                bbox_global=BBox(x=200, y=10, w=60, h=60),
                page_index=0,
                attributes={"equipment_class": "pump", "pump_type": "centrifugal"},
                confidence="high",
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e1", from_node="t1", to_node="p1", line_type="process",
                polyline_global=[(90, 50), (200, 40)],
                confidence="high",
            ),
        ],
    )

    run_dir = tmp_path / "run-1"
    run_dir.mkdir()
    issues: list[str] = []
    _write_run_artefacts(
        run_dir=run_dir,
        runs_root=tmp_path,
        run_id="r-test",
        stem="demo",
        effort="medium",
        model="claude-opus-4-7",
        graph=g,
        cost_summary={"total_usd": 0.0},
        dexpi_stats={},
        dexpi_issues=issues,
        validation_issues=[],
        dexpi_json_path=None,
        legend_pack=None,
        legend_source_tag="none",
        states=[],
        per_page_status={0: "ok"},
        confidence_report_path=None,
    )

    # Both renderers run side-by-side; failure of either is a non-fatal issue
    # appended to dexpi_issues but should NOT happen in this clean fixture.
    assert (run_dir / "graph.json").exists()
    assert (run_dir / "pid.svg").exists()
    assert (run_dir / "pid.drawio").exists(), "pid.drawio missing — auto-render not wired up"
    assert not any("drawio" in i for i in issues), issues

    # And the file is well-formed mxfile XML.
    text = (run_dir / "pid.drawio").read_text(encoding="utf-8")
    assert text.startswith("<mxfile")
    ET.fromstring(text)


_FIXTURE = Path(__file__).resolve().parents[2] / "eval/datasets/dexpi-reference/graph.truth.json"


@pytest.mark.skipif(not _FIXTURE.exists(), reason="dexpi-reference truth graph not present")
def test_dexpi_reference_renders_cleanly():
    xml = render_graph_json_to_drawio(_FIXTURE, title="dexpi-reference")
    root = _parse(xml)
    cells = _cells(root)
    vertices = [c for c in cells if c.get("vertex") == "1"]
    edges = [c for c in cells if c.get("edge") == "1"]
    assert vertices, "no vertices rendered for dexpi-reference"
    assert edges, "no edges rendered for dexpi-reference"
    # Every edge must reference real source/target cell IDs.
    cell_ids = {c.get("id") for c in cells}
    for e in edges:
        assert e.get("source") in cell_ids, e.get("id")
        assert e.get("target") in cell_ids, e.get("id")
    # At least the tank → mxgraph.pid.vessels.tank stencil shows up.
    all_styles = " ".join(v.get("style", "") for v in vertices)
    assert "mxgraph.pid" in all_styles
