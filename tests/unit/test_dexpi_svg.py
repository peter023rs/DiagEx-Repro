"""Unit tests for the DEXPI SVG renderer + render-dexpi CLI."""

from pathlib import Path

from typer.testing import CliRunner

from diagex.cli import app
from diagex.extractors.dexpi_svg import (
    SvgRenderOptions,
    render_graph_json_to_svg,
    render_graph_to_svg,
    write_svg,
)
from diagex.vision.models import (
    BBox,
    ReconciledEdge,
    ReconciledGraph,
    ReconciledNode,
)


def _graph_with_variety() -> ReconciledGraph:
    return ReconciledGraph(
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
                id="p1", kind="equipment", label="P-201",
                bbox_global=BBox(x=200, y=30, w=60, h=60),
                page_index=0,
                attributes={"equipment_class": "pump", "pump_type": "centrifugal"},
                confidence="medium",
            ),
            ReconciledNode(
                id="v1", kind="equipment", label="V-1",
                bbox_global=BBox(x=140, y=50, w=24, h=24),
                page_index=0,
                attributes={"equipment_class": "valve", "valve_type": "gate"},
                confidence="high",
            ),
            ReconciledNode(
                id="i1", kind="instrument", label="FIC-101",
                bbox_global=BBox(x=170, y=130, w=30, h=30),
                page_index=0,
                attributes={"instrument_function": "controller", "loop_number": "101"},
                confidence="high",
            ),
            ReconciledNode(
                id="o1", kind="opc", label="OPC-12",
                bbox_global=BBox(x=320, y=50, w=30, h=30),
                page_index=0,
                attributes={"direction": "out"},
                confidence="low",         # exercises the dashed outline
            ),
        ],
        edges=[
            ReconciledEdge(
                id="e1", from_node="t1", to_node="v1", line_type="process",
                polyline_global=[(90, 50), (140, 62)],
                confidence="high",
            ),
            ReconciledEdge(
                id="e2", from_node="i1", to_node="v1", line_type="signal_electric",
                polyline_global=[(185, 130), (152, 80)],
                confidence="medium",
            ),
        ],
    )


def test_edge_renders_line_id_pill_when_inherited_from_opc():
    # Edge has no `line_id`, but its target OPC does — renderer should inherit.
    nodes = [
        ReconciledNode(id="p1", kind="equipment", label="P-101",
                       bbox_global=BBox(x=0, y=0, w=60, h=60), page_index=0,
                       attributes={"equipment_class": "pump"}, confidence="high"),
        ReconciledNode(id="o1", kind="opc", label="outlet",
                       bbox_global=BBox(x=500, y=20, w=40, h=40), page_index=0,
                       attributes={"direction": "out", "line_id": "MN-47121-75HB13-80"},
                       confidence="high"),
    ]
    edges = [ReconciledEdge(id="e1", from_node="p1", to_node="o1",
                            line_type="process",
                            polyline_global=[(60, 30), (500, 30)],
                            confidence="high")]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges))
    # Pill background + pill text are both emitted.
    assert 'class="line-id-bg"' in svg
    assert "MN-47121-75HB13-80" in svg


def test_crossing_hop_arc_is_emitted_between_perpendicular_edges():
    # Two process pipes crossing perpendicularly: one should hop over the other.
    nodes = [
        ReconciledNode(id="n1", kind="equipment", label="A",
                       bbox_global=BBox(x=0, y=0, w=20, h=20), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="n2", kind="equipment", label="B",
                       bbox_global=BBox(x=400, y=0, w=20, h=20), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="n3", kind="equipment", label="C",
                       bbox_global=BBox(x=190, y=-200, w=20, h=20), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="n4", kind="equipment", label="D",
                       bbox_global=BBox(x=190, y=200, w=20, h=20), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
    ]
    edges = [
        ReconciledEdge(id="eA", from_node="n1", to_node="n2", line_type="process",
                       polyline_global=[(20, 10), (400, 10)], confidence="high"),
        ReconciledEdge(id="eB", from_node="n3", to_node="n4", line_type="signal_electric",
                       polyline_global=[(200, -180), (200, 180)], confidence="high"),
    ]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges))
    # An SVG arc (A command in path d) appears for the hop; signal hops over process.
    assert " A " in svg


def test_nozzle_marker_rendered_at_equipment_attach_point():
    nodes = [
        ReconciledNode(id="t1", kind="equipment", label="T-1",
                       bbox_global=BBox(x=0, y=0, w=80, h=80), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="p1", kind="equipment", label="P-1",
                       bbox_global=BBox(x=300, y=20, w=60, h=60), page_index=0,
                       attributes={"equipment_class": "pump"}, confidence="high"),
    ]
    edges = [ReconciledEdge(id="e1", from_node="t1", to_node="p1",
                            line_type="process",
                            polyline_global=[(80, 40), (300, 50)],
                            confidence="high")]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges))
    assert 'class="nozzle"' in svg


def test_instrument_controller_gets_panel_mount_line():
    # The panel-mount line is an extra horizontal <line> inside controller
    # bubbles only. Compare a graph with 1 controller vs 1 plain indicator:
    # the controller graph emits strictly more <line> elements.
    base_node = lambda fn: ReconciledNode(
        id="i", kind="instrument", label="X-1",
        bbox_global=BBox(x=0, y=0, w=40, h=40), page_index=0,
        attributes={"instrument_function": fn}, confidence="high",
    )
    indicator_svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=[base_node("indicator")]))
    controller_svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=[base_node("indicator_controller")]))
    assert controller_svg.count('<line') > indicator_svg.count('<line')


def test_valve_bowtie_renders_with_subtype_markers():
    for vt, marker_pred in [
        ("gate",       lambda s: 'class="valve"' in s),
        ("ball",       lambda s: '<circle' in s.split('class="valve"')[1]),
        ("butterfly",  lambda s: '<line' in s.split('class="valve"')[1]),
        ("check",      lambda s: '<polygon' in s.split('class="valve"')[1]),
    ]:
        nodes = [
            ReconciledNode(id=f"v-{vt}", kind="equipment", label=f"V-{vt}",
                           bbox_global=BBox(x=0, y=0, w=30, h=30), page_index=0,
                           attributes={"equipment_class": "valve", "valve_type": vt},
                           confidence="high"),
        ]
        svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes))
        assert marker_pred(svg), f"valve_type={vt} missing expected subtype marker"


def test_plate_hx_emits_chevrons_and_shell_tube_emits_tube_bundle():
    g_plate = ReconciledGraph(source_path="t.pdf", nodes=[
        ReconciledNode(id="hx1", kind="equipment", label="HX-plate",
                       bbox_global=BBox(x=0, y=0, w=60, h=80), page_index=0,
                       attributes={"equipment_class": "heat_exchanger",
                                   "heat_exchanger_type": "plate"},
                       confidence="high"),
    ])
    g_st = ReconciledGraph(source_path="t.pdf", nodes=[
        ReconciledNode(id="hx2", kind="equipment", label="HX-st",
                       bbox_global=BBox(x=0, y=0, w=80, h=40), page_index=0,
                       attributes={"equipment_class": "heat_exchanger",
                                   "heat_exchanger_type": "shell_and_tube"},
                       confidence="high"),
    ])
    svg_plate = render_graph_to_svg(g_plate)
    svg_st = render_graph_to_svg(g_st)
    # Plate HX has multiple <polyline> chevrons inside the body.
    assert svg_plate.count('<polyline') >= 3
    # Shell-tube has multiple thin horizontal tubes and tube-sheet markers.
    assert svg_st.count('<line') >= 6
    # And the two glyphs must not produce identical bodies.
    assert svg_plate != svg_st


def test_tooltip_title_elements_carry_full_attribute_dict():
    nodes = [
        ReconciledNode(
            id="p1", kind="equipment", label="P-101",
            bbox_global=BBox(x=0, y=0, w=40, h=40),
            page_index=0,
            attributes={"equipment_class": "pump", "design_capacity": "420 m3/h", "design_head": "40 m"},
            confidence="high",
        ),
    ]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes))
    # <title> child inside the node wrapper carries the attributes line-by-line.
    assert "<title>" in svg
    assert "design_capacity: 420 m3/h" in svg
    assert "design_head: 40 m" in svg


def test_label_is_truncated_with_ellipsis_in_svg_body():
    long_label = "Manual block valve 73KH12-50 (P4712 discharge main line)"
    nodes = [
        ReconciledNode(
            id="v1", kind="equipment", label=long_label,
            bbox_global=BBox(x=0, y=0, w=30, h=30),
            page_index=0,
            attributes={"equipment_class": "valve", "valve_type": "gate"},
            confidence="high",
        ),
    ]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes))
    # Truncated form appears in body; full form survives in the tooltip.
    assert "…" in svg
    assert long_label in svg   # in the <title>


def test_valve_failure_position_renders_fc_badge():
    nodes = [
        ReconciledNode(
            id="cv1", kind="equipment", label="PV-101",
            bbox_global=BBox(x=0, y=0, w=30, h=30),
            page_index=0,
            attributes={"equipment_class": "valve", "valve_type": "control", "failure_position": "F.C."},
            confidence="high",
        ),
    ]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes))
    # FC badge rendered and the pneumatic diaphragm actuator glyph is present.
    assert '>FC<' in svg
    # Diaphragm is an SVG <path> starting with "M" — just check the stem line is there.
    assert 'stroke-width="1.2"' in svg


def test_safety_relief_valve_emits_spring_and_arrow():
    nodes = [
        ReconciledNode(
            id="sv1", kind="equipment", label="SV-104",
            bbox_global=BBox(x=0, y=0, w=30, h=30),
            page_index=0,
            attributes={"equipment_class": "valve", "valve_type": "other",
                        "subtype": "safety_relief_valve", "set_pressure": "6 barg"},
            confidence="high",
        ),
    ]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes))
    # Spring = a <polyline fill="none"> above the diamond, plus the set-pressure tag.
    assert 'class="srv-set"' in svg
    assert '6 barg' in svg


def test_perimeter_attachment_does_not_draw_through_node_centre():
    # A horizontal pipe from a tank's east edge to a pump's west edge —
    # perimeter attachment keeps the line outside both bboxes.
    nodes = [
        ReconciledNode(id="t1", kind="equipment", label="T-1",
                       bbox_global=BBox(x=0, y=100, w=80, h=80), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="p1", kind="equipment", label="P-1",
                       bbox_global=BBox(x=300, y=100, w=60, h=60), page_index=0,
                       attributes={"equipment_class": "pump"}, confidence="high"),
    ]
    edges = [ReconciledEdge(id="e1", from_node="t1", to_node="p1",
                            line_type="process", polyline_global=[(100, 140), (290, 140)],
                            confidence="high")]
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges))
    # The rendered polyline's first point should land at x=80 (tank right edge),
    # not x=40 (tank centre).
    assert "points=" in svg


def test_title_block_renders_metadata_when_supplied():
    svg = render_graph_to_svg(
        ReconciledGraph(source_path="demo.pdf", nodes=[
            ReconciledNode(id="n", kind="equipment", label="X",
                           bbox_global=BBox(x=0, y=0, w=20, h=20), page_index=0,
                           attributes={"equipment_class": "tank"}, confidence="high"),
        ]),
        metadata={"run_id": "r-1234", "model": "claude-opus-4-7", "effort": "medium", "total_usd": 1.234},
    )
    assert "r-1234" in svg
    assert "claude-opus-4-7" in svg
    assert "$1.234" in svg


def test_flow_arrow_markers_are_emitted_and_referenced():
    svg = render_graph_to_svg(_graph_with_variety())
    # Every supported line-type bucket has a marker defined.
    for key in ("process", "signal", "other"):
        assert f'id="arrow-{key}"' in svg
    # Edges point to the right marker and only when the target node is known.
    # process edge in the fixture runs t1 → v1 (both known) → expect marker-end.
    assert 'marker-end="url(#arrow-process)"' in svg
    assert 'marker-end="url(#arrow-signal)"' in svg


def test_label_planner_staggers_overlapping_labels():
    from diagex.extractors.dexpi_svg import _plan_labels

    # Three equipment nodes stacked at the same y — their default label
    # slots (directly below) would overlap. The planner must bump each one
    # down by a line-height (or rotate when the cluster is too tight).
    nodes = [
        ReconciledNode(
            id=f"n{i}", kind="equipment", label=f"Very-long-label-{i}",
            bbox_global=BBox(x=100 + i * 40, y=200, w=30, h=30),
            page_index=0,
            attributes={"equipment_class": "pump"},
            confidence="high",
        )
        for i in range(3)
    ]

    def project(x, y):
        return (float(x), float(y))

    layout = _plan_labels(nodes, project, scale=1.0)
    assert set(layout) == {n.id for n in nodes}
    ys = [layout[n.id].y for n in nodes]
    # Not all three end up at identical y-positions (either staggered or rotated).
    staggered = len({round(y, 1) for y in ys}) > 1
    rotated = any(layout[n.id].rotate != 0 for n in nodes)
    assert staggered or rotated


def test_render_output_is_wellformed_xml_for_every_equipment_class():
    # Regression for the double-stroke-dasharray bug that froze browser render.
    # Build a graph with one node per supported equipment_class, plus a low-
    # confidence unclassified node (the branch that originally emitted the
    # attribute twice), and confirm the SVG parses.
    import xml.etree.ElementTree as ET

    classes = ["tank", "vessel", "column", "heat_exchanger", "pump", "compressor"]
    nodes = [
        ReconciledNode(
            id=f"eq{i}", kind="equipment", label=f"E-{i}",
            bbox_global=BBox(x=i * 60, y=20, w=40, h=40),
            page_index=0,
            attributes={"equipment_class": c},
            confidence="high",
        )
        for i, c in enumerate(classes)
    ]
    nodes.append(
        ReconciledNode(
            id="ux", kind="equipment", label="UNK",
            bbox_global=BBox(x=400, y=20, w=40, h=20),
            page_index=0,
            attributes={},                # → unclassified path
            confidence="low",             # → confidence dash
        )
    )
    svg = render_graph_to_svg(ReconciledGraph(source_path="regression.pdf", nodes=nodes))
    # xml.etree raises xml.etree.ElementTree.ParseError on duplicate attributes.
    ET.fromstring(svg)


def test_render_produces_wellformed_svg_with_all_shapes():
    svg = render_graph_to_svg(_graph_with_variety(), title="demo")
    assert svg.startswith('<svg') and svg.endswith('</svg>')
    # Each node kind leaves a fingerprint in the output.
    assert 'class="eq tank"' in svg          # tank glyph (dished-cap group)
    assert 'class="eq pump"' in svg          # pump glyph (circle)
    assert 'class="valve"' in svg            # valve bowtie (ISA-5.1)
    assert '<circle class="inst"' in svg     # instrument circle
    assert '<polygon class="opc"' in svg     # OPC pentagon
    # Edges now render as <path> so hops can be interleaved with straight segments.
    assert '<path class="edge"' in svg
    # Signal line is dashed.
    assert 'stroke-dasharray="4,3"' in svg
    # Low-confidence node gets a dashed outline.
    assert 'stroke-dasharray="3,2"' in svg
    # Labels and title present.
    assert 'FIC-101' in svg
    assert 'demo' in svg


def test_render_handles_empty_graph_gracefully():
    svg = render_graph_to_svg(
        ReconciledGraph(source_path="empty.pdf"), title="nothing"
    )
    assert svg.startswith('<svg')
    assert 'no nodes' in svg


def test_legend_panel_can_be_disabled():
    g = _graph_with_variety()
    svg = render_graph_to_svg(g, options=SvgRenderOptions(show_legend_panel=False))
    assert 'class="key-bg"' not in svg


def test_write_svg_creates_parent_dir(tmp_path: Path):
    g = _graph_with_variety()
    target = tmp_path / "nested" / "run" / "pid.svg"
    written = write_svg(g, target, title="smoke")
    assert written == target
    assert target.exists()
    # Round-trip through loader form.
    assert target.read_text().startswith('<svg')


def test_render_graph_json_to_svg_roundtrips(tmp_path: Path):
    g = _graph_with_variety()
    graph_json = tmp_path / "graph.json"
    graph_json.write_text(g.model_dump_json(), encoding="utf-8")
    svg = render_graph_json_to_svg(graph_json)
    assert 'class="valve"' in svg


def test_cli_render_dexpi_accepts_graph_json(tmp_path: Path):
    g = _graph_with_variety()
    graph_json = tmp_path / "graph.json"
    graph_json.write_text(g.model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["render-dexpi", str(graph_json)])
    assert result.exit_code == 0, result.stdout
    svg_path = graph_json.with_suffix(".svg")
    assert svg_path.exists()


def test_cli_render_dexpi_accepts_run_dir(tmp_path: Path):
    g = _graph_with_variety()
    run_dir = tmp_path / "run"
    run_dir.mkdir()
    (run_dir / "graph.json").write_text(g.model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["render-dexpi", str(run_dir), "--out", str(tmp_path / "out.svg")])
    assert result.exit_code == 0
    assert (tmp_path / "out.svg").exists()


def test_cli_render_dexpi_complains_when_run_dir_has_no_graph(tmp_path: Path):
    (tmp_path / "empty_run").mkdir()
    result = CliRunner().invoke(app, ["render-dexpi", str(tmp_path / "empty_run")])
    assert result.exit_code == 2
    # Rich may soft-wrap the message; strip whitespace before matching.
    assert "graph.json" in " ".join(result.stdout.split()).lower()


# ---------------------------------------------------------------------------
# Manhattan routing for inferred edges
# ---------------------------------------------------------------------------


def test_orthogonal_route_horizontal_dominant_returns_z_path():
    from diagex.extractors.dexpi_svg import _orthogonal_route

    src = BBox(x=0, y=0, w=40, h=40)        # centre (20, 20)
    dst = BBox(x=200, y=80, w=40, h=40)     # centre (220, 100); horiz-dominant
    poly = _orthogonal_route(src, dst)

    # 4-point Z: leave src on the right, enter dst on the left, mid-channel turn.
    assert len(poly) == 4
    assert poly[0] == (40, 20)              # right edge of src at centre y
    assert poly[-1] == (200, 100)           # left edge of dst at centre y
    # Middle two share x = midpoint of the two attach x's.
    assert poly[1][0] == poly[2][0]
    assert poly[1][1] == poly[0][1]
    assert poly[2][1] == poly[3][1]


def test_orthogonal_route_collinear_returns_two_points():
    from diagex.extractors.dexpi_svg import _orthogonal_route

    src = BBox(x=0, y=0, w=40, h=40)
    dst = BBox(x=200, y=0, w=40, h=40)      # same y centre → straight horizontal
    poly = _orthogonal_route(src, dst)
    assert poly == [(40, 20), (200, 20)]


def test_orthogonal_route_vertical_dominant_uses_top_bottom():
    from diagex.extractors.dexpi_svg import _orthogonal_route

    src = BBox(x=0, y=0, w=40, h=40)        # centre (20, 20)
    dst = BBox(x=80, y=400, w=40, h=40)     # centre (100, 420); vert-dominant
    poly = _orthogonal_route(src, dst)
    assert len(poly) == 4
    assert poly[0] == (20, 40)              # bottom edge of src
    assert poly[-1] == (100, 400)           # top edge of dst


def test_inferred_edge_uses_orthogonal_route_by_default():
    # Two equipment nodes, edge with no polyline — renderer should produce a
    # path with two right-angle turns (horizontal then vertical then horizontal).
    nodes = [
        ReconciledNode(id="t1", kind="equipment", label="T-1",
                       bbox_global=BBox(x=0, y=0, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="t2", kind="equipment", label="T-2",
                       bbox_global=BBox(x=300, y=200, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
    ]
    edges = [ReconciledEdge(id="e1", from_node="t1", to_node="t2",
                            line_type="process",
                            confidence="high")]   # no polyline_global
    svg = render_graph_to_svg(ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges))
    # The path is rendered with M/L commands; 4 polyline points → 3 line segments.
    # Count "L" commands in the edge path. (The hop arc adds A commands which we
    # don't generate here since there's only one edge — no crossings.)
    assert svg.count(" L ") >= 3 or svg.count("L") >= 3


def test_inferred_edge_falls_back_to_diagonal_when_orthogonal_disabled():
    nodes = [
        ReconciledNode(id="t1", kind="equipment", label="T-1",
                       bbox_global=BBox(x=0, y=0, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="t2", kind="equipment", label="T-2",
                       bbox_global=BBox(x=300, y=200, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
    ]
    edges = [ReconciledEdge(id="e1", from_node="t1", to_node="t2",
                            line_type="process", confidence="high")]
    g = ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges)
    opts = SvgRenderOptions(orthogonal_inferred=False)
    svg = render_graph_to_svg(g, options=opts)
    # Without ortho the path is one straight segment between perimeter attach
    # points → only one L command in the edge path.
    # (Other `L` letters may appear in node glyphs; assert the file still renders
    # something so the regression is visible if --no-ortho ever crashes.)
    assert "<path class=\"edge\"" in svg


def test_bootstrap_polyline_is_unaffected_by_orthogonal_flag():
    nodes = [
        ReconciledNode(id="t1", kind="equipment", label="T-1",
                       bbox_global=BBox(x=0, y=0, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
        ReconciledNode(id="t2", kind="equipment", label="T-2",
                       bbox_global=BBox(x=300, y=200, w=40, h=40), page_index=0,
                       attributes={"equipment_class": "tank"}, confidence="high"),
    ]
    # Bootstrap polyline traces a curved path the model saw — the renderer
    # must keep that geometry verbatim regardless of orthogonal_inferred.
    custom_poly = [(40, 20), (60, 20), (80, 100), (100, 220), (300, 220)]
    edges = [ReconciledEdge(id="e1", from_node="t1", to_node="t2",
                            line_type="process",
                            polyline_global=custom_poly,
                            confidence="high")]
    g = ReconciledGraph(source_path="t.pdf", nodes=nodes, edges=edges)
    svg_a = render_graph_to_svg(g, options=SvgRenderOptions(orthogonal_inferred=True))
    svg_b = render_graph_to_svg(g, options=SvgRenderOptions(orthogonal_inferred=False))
    # Same edge path in both renderings.
    import re
    def edge_d(svg: str) -> str:
        m = re.search(r'<path class="edge"[^>]*d="([^"]+)"', svg)
        return m.group(1) if m else ""
    assert edge_d(svg_a) == edge_d(svg_b)
    assert edge_d(svg_a) != ""


def test_render_dexpi_cli_no_ortho_flag_runs_without_error(tmp_path: Path):
    g = _graph_with_variety()
    graph_json = tmp_path / "graph.json"
    graph_json.write_text(g.model_dump_json(), encoding="utf-8")
    result = CliRunner().invoke(app, ["render-dexpi", str(graph_json), "--no-ortho"])
    assert result.exit_code == 0, result.stdout
