from __future__ import annotations

import base64
import io
import json
from pathlib import Path
from types import SimpleNamespace

import anthropic
import fitz
import httpx
import pytest
from PIL import Image, ImageDraw

from diagex.config import Config, LLMConfig, PidConfig
from diagex.extractors.evidence_checkpoint import (
    CheckpointStore,
    find_resumable_run,
    find_resumable_run_with_report,
)
from diagex.extractors.pid_evidence import _native_line_legend_images, run_pid_evidence_extract
from diagex.llm.cost import CostTracker
from diagex.review.core import ReviewStore
from diagex.ui.progress import NullReporter
from diagex.vision.evidence import (
    PageEvidence,
    PathEvidence,
    TextEvidence,
    classify_page,
    classify_pdf_dash_pattern,
    extract_page_evidence,
)
from diagex.vision.fusion import assemble_graph, fuse_objects
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.vision.models import (
    BBox,
    DiagramPage,
    DiagramSource,
    ReconciledGraph,
    ReconciledNode,
    Tile,
)
from diagex.vision.native_text import build_native_text_inventory
from diagex.vision.perception import (
    _SUBMIT_TOOL,
    DetectionRecord,
    NormalizedBBox,
    PerceivedObject,
    PerceptionResponseFormatError,
    parse_perception_response,
    perceive_tile,
    project_batch,
)
from diagex.vision.quality import assess_quality
from diagex.vision.tiling import FixedGridStrategy, ownership_core, tile
from diagex.vision.topology import TopologyResult, build_page_topology
from diagex.vision.views import ViewInfo


def _page_evidence(*, paths: list[PathEvidence] | None = None) -> PageEvidence:
    return PageEvidence(
        page_index=0,
        source_ref="drawing#page=1",
        width=1000,
        height=600,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        role="pid",
        role_confidence="high",
        role_reason="test",
        fail_open=False,
        paths=paths or [],
    )


def _node(node_id: str, x: int, *, kind: str = "equipment") -> ReconciledNode:
    return ReconciledNode(
        id=node_id,
        kind=kind,  # type: ignore[arg-type]
        label=node_id,
        bbox_global=BBox(x=x, y=270, w=40, h=60),
        page_index=0,
        confidence="high",
    )


def _fuse_evidence(
    *,
    source_name: str,
    pages: list[PageEvidence],
    detections: list[DetectionRecord],
    topology: list[TopologyResult],
    per_page_status: dict[int, str],
):
    objects = fuse_objects(
        source_name=source_name,
        pages=pages,
        detections=detections,
        per_page_status=per_page_status,
    )
    return assemble_graph(
        objects=objects,
        pages=pages,
        topology=topology,
        page_graph_results=[],
        per_page_status=per_page_status,
    )


def test_vector_legend_rows_are_recropped_from_positioned_native_text() -> None:
    image = Image.new("RGB", (900, 300), "white")
    draw = ImageDraw.Draw(image)
    for x in range(120, 380, 45):
        draw.line((x, 120, x + 25, 120), fill="black", width=3)
    draw.text((430, 105), "Electric signal", fill="black")
    diagram_page = DiagramPage(
        page_index=0,
        image=image,
        width=image.width,
        height=image.height,
        dpi=150,
        effective_dpi=150,
        is_scanned=False,
        source_ref="legend#page=1",
    )
    source = DiagramSource(path=Path("legend.pdf"), kind="pdf", pages=[diagram_page])
    evidence = PageEvidence(
        page_index=0,
        source_ref="legend#page=1",
        width=image.width,
        height=image.height,
        dpi=150,
        effective_dpi=150,
        is_scanned=False,
        role="legend",
        role_confidence="high",
        role_reason="test",
        fail_open=False,
        text_spans=[
            TextEvidence(
                id="txt-1",
                text="Electric signal",
                bbox=BBox(x=430, y=100, w=120, h=30),
            )
        ],
    )
    pack = LegendPack(
        entries=[
            LegendEntry(
                label="Electric signal",
                symbol_class="line",
                kind="line",
            )
        ]
    )

    rows = _native_line_legend_images(source=source, pages=[evidence], legend_pack=pack)

    assert len(rows) == 1
    assert rows[0]["source"] == "native_vector_legend_row"
    crop = Image.open(io.BytesIO(base64.b64decode(rows[0]["image_b64"])))
    assert crop.width >= 540
    assert crop.height >= 80
    assert crop.convert("L").getextrema()[0] < 255


def test_native_pdf_evidence_extracts_words_paths_and_pid_role(tmp_path: Path) -> None:
    pdf = tmp_path / "native.pdf"
    document = fitz.open()
    page = document.new_page(width=300, height=200)
    page.insert_text((20, 20), "P&ID P-101")
    page.draw_line((30, 100), (270, 100))
    document.save(pdf)
    document.close()

    with fitz.open(pdf) as reopened:
        rendered = reopened[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        diagram_page = DiagramPage(
            page_index=0,
            width=rendered.width,
            height=rendered.height,
            dpi=144,
            effective_dpi=144,
            is_scanned=False,
            source_ref="native#page=1",
        )
        evidence = extract_page_evidence(
            page=diagram_page,
            source_path=pdf,
            pdf_page=reopened[0],
        )

    assert evidence.role == "pid"
    assert evidence.role_confidence == "high"
    assert any(span.text == "P-101" for span in evidence.text_spans)
    assert any(path.primitive == "line" for path in evidence.paths)
    assert all(path.bbox.x2 <= evidence.width for path in evidence.paths)


def test_pdf_dash_pattern_records_appearance_without_assigning_signal_semantics() -> None:
    assert classify_pdf_dash_pattern("[] 0") == ("solid", 0.99, "pdf_path")
    style, confidence, source = classify_pdf_dash_pattern(
        "[12 6] 0",
        stroke_width=1.5,
    )
    assert style == "dashed"
    assert confidence > 0.9
    assert source == "pdf_dash_metadata"

    style, _, _ = classify_pdf_dash_pattern("[16 5 2 5] 0", stroke_width=1.5)
    assert style == "dash_dot"


def test_page_router_is_conservative_and_fail_open() -> None:
    legend_span = TextEvidence(id="txt-1", text="仪表符号图例", bbox=BBox(x=0, y=0, w=30, h=10))
    role, confidence, _, fail_open = classify_page(
        page_index=2,
        text_spans=[legend_span],
        paths=[],
    )
    assert (role, confidence, fail_open) == ("legend", "high", False)

    role, confidence, _, fail_open = classify_page(
        page_index=3,
        text_spans=[TextEvidence(id="txt-2", text="misc", bbox=BBox(x=0, y=0, w=10, h=10))],
        paths=[],
    )
    assert (role, confidence, fail_open) == ("pid", "low", True)


def test_checkpoint_resume_requires_matching_hashes(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "drawing" / "2026-test_r-abcd"
    run.mkdir(parents=True)
    store = CheckpointStore.create(
        run_dir=run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-abcd",
    )
    store.write_json_artifact("inspection", "page-0001", {"ok": True})
    store.set_status("partial")

    found = find_resumable_run(
        runs_root=run.parent,
        source_sha256="source",
        config_sha256="config",
    )
    assert found is not None
    assert found.is_done("inspection", "page-0001")
    assert found.read_json_artifact("inspection", "page-0001") == {"ok": True}
    assert (
        find_resumable_run(
            runs_root=run.parent,
            source_sha256="other",
            config_sha256="config",
        )
        is None
    )


def test_resume_report_explains_complete_and_config_mismatch(tmp_path: Path) -> None:
    complete_run = tmp_path / "runs" / "drawing" / "2026-complete"
    complete_run.mkdir(parents=True)
    complete = CheckpointStore.create(
        run_dir=complete_run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-complete",
    )
    complete.set_status("complete")

    found, report = find_resumable_run_with_report(
        runs_root=complete_run.parent,
        source_sha256="source",
        config_sha256="config",
    )
    assert found is None
    assert report["matching_complete_runs"] == 1
    assert "complete" in report["reason"]

    found, report = find_resumable_run_with_report(
        runs_root=complete_run.parent,
        source_sha256="source",
        config_sha256="changed",
    )
    assert found is None
    assert report["config_mismatches"] == 1
    assert "configuration" in report["reason"]


def test_checkpoint_runtime_summary_counts_actual_reads_and_writes(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    created = CheckpointStore.create(
        run_dir=run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-test",
    )
    created.write_json_artifact("perception", "tile-1", {"detections": []})

    resumed = CheckpointStore.load(run)
    assert resumed.read_json_artifact("perception", "tile-1") == {"detections": []}
    resumed.write_json_artifact("topology", "page-1", {"edges": []})
    summary = resumed.reuse_summary()

    assert summary == {
        "reused_by_stage": {"perception": 1},
        "computed_by_stage": {"topology": 1},
        "reused_total": 1,
        "computed_total": 1,
        "reuse_percent": 50.0,
    }


def test_old_adaptive_checkpoint_schema_is_not_resumed(tmp_path: Path) -> None:
    run = tmp_path / "runs" / "drawing" / "old-run"
    run.mkdir(parents=True)
    store = CheckpointStore.create(
        run_dir=run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-old",
    )
    manifest_path = store.path
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    manifest["schema_version"] = "1.0.0"
    manifest_path.write_text(json.dumps(manifest), encoding="utf-8")

    assert (
        find_resumable_run(
            runs_root=run.parent,
            source_sha256="source",
            config_sha256="config",
        )
        is None
    )


def test_checkpoint_invalidates_downstream_stages_after_upstream_recovery(tmp_path: Path) -> None:
    run = tmp_path / "run"
    run.mkdir()
    store = CheckpointStore.create(
        run_dir=run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-test",
    )
    store.write_json_artifact("topology", "page-0001", {"old": True})
    store.write_json_artifact("page_graph", "page-0001", {"old": True})

    store.invalidate("topology", "page_graph", "assembly")

    assert not store.is_done("topology", "page-0001")
    assert not store.is_done("page_graph", "page-0001")


def test_checkpoint_stage_version_reuses_perception_but_rebuilds_postprocess(
    tmp_path: Path,
) -> None:
    run = tmp_path / "run"
    run.mkdir()
    store = CheckpointStore.create(
        run_dir=run,
        source_sha256="source",
        config_sha256="config",
        run_id="r-test",
    )
    store.write_json_artifact("perception", "tile-1", {"detections": []})
    store.write_json_artifact("topology", "page-1", {"edges": []})
    store.write_json_artifact("page_graph", "page-0001", {"graph": {}})

    assert store.ensure_stage_version(
        "page_graph_pipeline",
        "1.0.0",
        invalidate=("topology", "page_graph", "assembly"),
    )
    assert store.is_done("perception", "tile-1")
    assert not store.is_done("topology", "page-1")
    assert not store.is_done("page_graph", "page-0001")
    assert not store.ensure_stage_version(
        "page_graph_pipeline",
        "1.0.0",
        invalidate=("topology", "page_graph", "assembly"),
    )


def test_perception_tool_advertises_only_typed_object_output() -> None:
    schema = _SUBMIT_TOOL["input_schema"]
    assert set(schema["properties"]) == {"objects"}
    object_properties = schema["properties"]["objects"]["items"]["properties"]
    assert "printed_tag" in object_properties
    assert "canonical_tag" in object_properties
    assert "opc_direction" in object_properties
    assert "actuation" in object_properties
    assert "attributes" not in object_properties
    assert "observations" not in schema["properties"]


def test_perception_legacy_shape_maps_into_typed_graph_attributes() -> None:
    obj = PerceivedObject.model_validate(
        {
            "kind": "opc",
            "label": "CA TO V-002",
            "raw_text": "CA  TO  V-002",
            "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
            "attributes": {"direction": "out", "service": "compressed air"},
        }
    )

    assert obj.printed_tag == "CA TO V-002"
    assert obj.canonical_tag == "CA TO V-002"
    assert obj.graph_attributes()["direction"] == "out"
    assert obj.graph_attributes()["service"] == "compressed air"


def test_perception_preserves_typed_valve_actuation() -> None:
    obj = PerceivedObject.model_validate(
        {
            "kind": "equipment",
            "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
            "valve_type": "other",
            "actuation": "solenoid",
        }
    )

    assert obj.graph_attributes()["actuation"] == "solenoid"


def test_perception_salvages_valid_siblings_from_mixed_batch() -> None:
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "instrument",
                            "printed_tag": "PI-101",
                            "bbox": {"x": 0.1, "y": 0.1, "w": 0.1, "h": 0.1},
                        },
                        {
                            "printed_tag": "missing kind",
                            "bbox": {"x": 0.3, "y": 0.1, "w": 0.1, "h": 0.1},
                        },
                    ]
                },
            }
        ]
    )

    batch = parse_perception_response(response)

    assert [item.printed_tag for item in batch.objects] == ["PI-101"]
    assert batch.rejected_objects[0]["index"] == 1


def test_perception_forces_tool_and_recovers_once_from_prose() -> None:
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=20,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )
    responses = [
        SimpleNamespace(
            id="bad-1",
            model="vision-model",
            stop_reason="end_turn",
            usage=usage,
            content=[{"type": "text", "text": "I will analyze the image first."}],
        ),
        SimpleNamespace(
            id="good-2",
            model="vision-model",
            stop_reason="tool_use",
            usage=usage,
            content=[
                {
                    "type": "tool_use",
                    "name": "submit_pid_objects",
                    "input": {
                        "objects": [
                            {
                                "kind": "instrument",
                                "printed_tag": "PI-101",
                                "bbox": {"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1},
                            }
                        ]
                    },
                }
            ],
        ),
    ]

    class RecoveringClient:
        def __init__(self) -> None:
            self.requests: list[dict[str, object]] = []

        def messages_create(self, **kwargs: object) -> object:
            self.requests.append(kwargs)
            return responses[len(self.requests) - 1]

    client = RecoveringClient()
    page = _page_evidence()
    current_tile = Tile(
        id="p0-r0-c0",
        page_index=0,
        bbox=BBox(x=0, y=0, w=1000, h=600),
    )
    view = ViewInfo(
        source_view="tile",
        origin=(0, 0),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(1000, 600),
        page_bbox=current_tile.bbox,
        tile_id=current_tile.id,
    )
    attempts: list[None] = []
    cost = CostTracker()

    outcome = perceive_tile(
        client=client,  # type: ignore[arg-type]
        cost_tracker=cost,
        reporter=NullReporter(),
        page=page,
        tile=current_tile,
        view_image=Image.new("RGB", (1000, 600), "white"),
        view_info=view,
        ownership_bbox=current_tile.bbox,
        legend_summary=[],
        step=10,
        on_attempt=lambda: attempts.append(None),
    )

    assert outcome.attempts == 2
    assert [item.label for item in outcome.detections] == ["PI-101"]
    assert len(outcome.recovery_diagnostics) == 1
    assert outcome.recovery_diagnostics[0]["response"]["content"][0]["text"] == (
        "I will analyze the image first."
    )
    assert len(attempts) == 2
    assert [row.step for row in cost.steps] == [10, 11]
    assert all(
        request["tool_choice"] == {"type": "tool", "name": "submit_pid_objects"}
        for request in client.requests
    )
    retry_text = client.requests[1]["messages"][0]["content"][1]["text"]  # type: ignore[index]
    assert "Do not explain or narrate" in retry_text


def test_perception_stops_after_one_recovery_attempt_and_retains_responses() -> None:
    usage = SimpleNamespace(
        input_tokens=10,
        output_tokens=5,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )

    class ProseOnlyClient:
        calls = 0

        def messages_create(self, **kwargs: object) -> object:
            type(self).calls += 1
            return SimpleNamespace(
                id=f"bad-{self.calls}",
                model="vision-model",
                stop_reason="end_turn",
                usage=usage,
                content=[{"type": "text", "text": f"prose attempt {self.calls}"}],
            )

    page = _page_evidence()
    current_tile = Tile(
        id="p0-r0-c0",
        page_index=0,
        bbox=BBox(x=0, y=0, w=1000, h=600),
    )
    view = ViewInfo(
        source_view="tile",
        origin=(0, 0),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(1000, 600),
        page_bbox=current_tile.bbox,
        tile_id=current_tile.id,
    )

    with pytest.raises(PerceptionResponseFormatError) as caught:
        perceive_tile(
            client=ProseOnlyClient(),  # type: ignore[arg-type]
            cost_tracker=CostTracker(),
            reporter=NullReporter(),
            page=page,
            tile=current_tile,
            view_image=Image.new("RGB", (1000, 600), "white"),
            view_info=view,
            ownership_bbox=current_tile.bbox,
            legend_summary=[],
            step=1,
        )

    assert ProseOnlyClient.calls == 2
    assert caught.value.attempts == 2
    assert [item["response"]["content"][0]["text"] for item in caught.value.diagnostics] == [
        "prose attempt 1",
        "prose attempt 2",
    ]


def test_perception_retries_malformed_provider_tool_json_once() -> None:
    usage = SimpleNamespace(
        input_tokens=100,
        output_tokens=20,
        cache_read_input_tokens=0,
        cache_creation_input_tokens=0,
    )

    class MalformedThenValidClient:
        calls = 0

        def messages_create(self, **kwargs: object) -> object:
            type(self).calls += 1
            if self.calls == 1:
                raise ValueError("key must be a string at line 1 column 2378")
            return SimpleNamespace(
                id="good-2",
                model="vision-model",
                stop_reason="tool_use",
                usage=usage,
                content=[
                    {
                        "type": "tool_use",
                        "name": "submit_pid_objects",
                        "input": {
                            "objects": [
                                {
                                    "kind": "instrument",
                                    "printed_tag": "PI-101",
                                    "bbox": {"x": 0.2, "y": 0.2, "w": 0.1, "h": 0.1},
                                }
                            ]
                        },
                    }
                ],
            )

    page = _page_evidence()
    current_tile = Tile(
        id="p0-r0-c0",
        page_index=0,
        bbox=BBox(x=0, y=0, w=1000, h=600),
    )
    view = ViewInfo(
        source_view="tile",
        origin=(0, 0),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(1000, 600),
        page_bbox=current_tile.bbox,
        tile_id=current_tile.id,
    )

    outcome = perceive_tile(
        client=MalformedThenValidClient(),  # type: ignore[arg-type]
        cost_tracker=CostTracker(),
        reporter=NullReporter(),
        page=page,
        tile=current_tile,
        view_image=Image.new("RGB", (1000, 600), "white"),
        view_info=view,
        ownership_bbox=current_tile.bbox,
        legend_summary=[],
        step=1,
    )

    assert MalformedThenValidClient.calls == 2
    assert outcome.attempts == 2
    assert [item.label for item in outcome.detections] == ["PI-101"]
    assert outcome.recovery_diagnostics == [
        {
            "attempt": 1,
            "error": "key must be a string at line 1 column 2378",
            "phase": "provider_tool_json_decode",
            "response": None,
        }
    ]


def test_perception_does_not_retry_unrelated_value_error() -> None:
    class BrokenClient:
        calls = 0

        def messages_create(self, **kwargs: object) -> object:
            type(self).calls += 1
            raise ValueError("unsupported image media type")

    page = _page_evidence()
    current_tile = Tile(
        id="p0-r0-c0",
        page_index=0,
        bbox=BBox(x=0, y=0, w=1000, h=600),
    )
    view = ViewInfo(
        source_view="tile",
        origin=(0, 0),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(1000, 600),
        page_bbox=current_tile.bbox,
        tile_id=current_tile.id,
    )

    with pytest.raises(ValueError, match="unsupported image media type"):
        perceive_tile(
            client=BrokenClient(),  # type: ignore[arg-type]
            cost_tracker=CostTracker(),
            reporter=NullReporter(),
            page=page,
            tile=current_tile,
            view_image=Image.new("RGB", (1000, 600), "white"),
            view_info=view,
            ownership_bbox=current_tile.bbox,
            legend_summary=[],
            step=1,
        )

    assert BrokenClient.calls == 1


def test_tile_ownership_cores_partition_overlap_and_filter_projection() -> None:
    page = DiagramPage(
        page_index=0,
        width=1000,
        height=600,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        source_ref="drawing#page=1",
    )
    tiles = tile(page, FixedGridStrategy(tile_w=600, tile_h=600, overlap_frac=0.2))
    left, right = tiles
    left_core = ownership_core(left, tiles)
    right_core = ownership_core(right, tiles)
    assert left_core.x2 == right_core.x
    assert left_core.w + right_core.w == page.width

    view = ViewInfo(
        source_view="tile",
        origin=(left.bbox.x, left.bbox.y),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(left.bbox.w, left.bbox.h),
        page_bbox=left.bbox,
        tile_id=left.id,
    )
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "equipment",
                            "printed_tag": "P-OWNED-BY-RIGHT",
                            "bbox": {"x": 0.9, "y": 0.4, "w": 0.05, "h": 0.1},
                        }
                    ]
                },
            }
        ]
    )
    records = project_batch(
        batch=parse_perception_response(response),
        page=_page_evidence(),
        tile=left,
        view_info=view,
        nearby_text_ids=set(),
        ownership_bbox=left_core,
    )
    assert records == []


def test_perception_response_projects_normalized_coordinates_without_model_tile_id() -> None:
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "equipment",
                            "label": "P-101",
                            "bbox": {"x": 0.25, "y": 0.2, "w": 0.5, "h": 0.4},
                            "confidence": "high",
                        }
                    ]
                },
            }
        ]
    )
    batch = parse_perception_response(response)
    page = _page_evidence()
    tile = Tile(
        id="p0-r0-c0",
        page_index=0,
        bbox=BBox(x=100, y=50, w=400, h=200),
    )
    view = ViewInfo(
        source_view="tile",
        origin=(100, 50),
        scale_x=0.5,
        scale_y=0.5,
        view_size=(200, 100),
        page_bbox=tile.bbox,
        tile_id=tile.id,
    )
    records = project_batch(
        batch=batch,
        page=page,
        tile=tile,
        view_info=view,
        nearby_text_ids=set(),
    )
    assert records[0].tile_id == "p0-r0-c0"
    assert records[0].bbox == BBox(x=200, y=90, w=200, h=80)


def test_perception_response_normalises_string_diagnostics_without_weakening_objects() -> None:
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "instrument",
                            "label": "PI-00203",
                            "bbox": {"x": 0.1, "y": 0.2, "w": 0.1, "h": 0.1},
                            "confidence": "high",
                        }
                    ],
                    "observations": '["panel-mounted instrument"]',
                    "uncertainties": "Exact mounting detail is unclear.",
                },
            }
        ]
    )

    batch = parse_perception_response(response)

    assert batch.observations == ["panel-mounted instrument"]
    assert batch.uncertainties == ["Exact mounting detail is unclear."]
    assert batch.objects[0].label == "PI-00203"

    invalid = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "instrument",
                            "bbox": {"x": 0.95, "y": 0.2, "w": 0.1, "h": 0.1},
                        }
                    ],
                    "observations": "diagnostic text",
                },
            }
        ]
    )
    with pytest.raises(ValueError, match="normalised bbox must fit"):
        parse_perception_response(invalid)

    with pytest.raises(ValueError):
        NormalizedBBox(x=0.9, y=0, w=0.2, h=0.2)


def test_perception_response_recovers_supported_coordinate_frames() -> None:
    page = PageEvidence(
        page_index=10,
        source_ref="drawing#page=11",
        width=6000,
        height=4238,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
    )
    page_view = ViewInfo(
        source_view="tile",
        origin=(0, 3400),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(2000, 838),
        page_bbox=BBox(x=0, y=3400, w=2000, h=838),
        tile_id="p10-r4-c0",
    )
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": '[{"kind":"instrument","label":"PI-1",'
                    '"bbox":{"x":1395,"y":3920,"w":60,"h":40}}]',
                    "observations": [{"text": "page coordinate response"}],
                },
            }
        ]
    )

    batch = parse_perception_response(response, page=page, view_info=page_view)

    assert batch.objects[0].bbox == NormalizedBBox(
        x=1395 / 2000, y=520 / 838, w=60 / 2000, h=40 / 838
    )
    assert batch.objects[0].attributes["coordinate_recovery"] == "page_pixels"
    assert batch.observations == ["page coordinate response"]

    local_view = ViewInfo(
        source_view="tile",
        origin=(4000, 3400),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(2000, 838),
        page_bbox=BBox(x=4000, y=3400, w=2000, h=838),
        tile_id="p10-r4-c3",
    )
    local_response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "equipment",
                            "bbox": {"x": 470, "y": 138, "w": 90, "h": 162},
                        }
                    ]
                },
            }
        ]
    )

    batch = parse_perception_response(local_response, page=page, view_info=local_view)

    assert batch.objects[0].bbox == NormalizedBBox(
        x=470 / 2000, y=138 / 838, w=90 / 2000, h=162 / 838
    )
    assert batch.objects[0].attributes["coordinate_recovery"] == "tile_pixels"


def test_perception_response_clips_small_normalized_overflow_but_rejects_ambiguity() -> None:
    page = _page_evidence()
    view = ViewInfo(
        source_view="tile",
        origin=(100, 100),
        scale_x=1.0,
        scale_y=1.0,
        view_size=(400, 300),
        page_bbox=BBox(x=100, y=100, w=400, h=300),
        tile_id="p0-r1-c1",
    )
    clipped_response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "instrument",
                            "bbox": {"x": 0.19, "y": 0.92, "w": 0.06, "h": 0.09},
                        }
                    ]
                },
            }
        ]
    )

    batch = parse_perception_response(clipped_response, page=page, view_info=view)

    assert batch.objects[0].bbox.y + batch.objects[0].bbox.h == pytest.approx(1.0)
    assert batch.objects[0].attributes["coordinate_recovery"] == "normalized_clipped"

    ambiguous_response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "name": "submit_pid_objects",
                "input": {
                    "objects": [
                        {
                            "kind": "equipment",
                            "bbox": {"x": 150, "y": 150, "w": 20, "h": 20},
                        }
                    ]
                },
            }
        ]
    )
    with pytest.raises(ValueError, match="ambiguous between page-global and tile-local"):
        parse_perception_response(ambiguous_response, page=page, view_info=view)


def test_vector_topology_connects_only_engineering_nodes_and_has_no_self_loop() -> None:
    path = PathEvidence(
        id="vec-main",
        page_index=0,
        points=[(100, 300), (900, 300)],
        bbox=BBox(x=100, y=300, w=800, h=1),
        origin="pdf_vector",
        primitive="line",
    )
    page = _page_evidence(paths=[path])
    left = _node("n-left", 80)
    right = _node("n-right", 880)
    text = _node("n-text", 480, kind="text")

    topology = build_page_topology(page=page, nodes=[left, right, text])

    assert len(topology.edges) == 1
    assert {topology.edges[0].from_node, topology.edges[0].to_node} == {
        "n-left",
        "n-right",
    }
    assert topology.edges[0].from_node != topology.edges[0].to_node
    assert "n-text" not in {
        topology.edges[0].from_node,
        topology.edges[0].to_node,
    }


def test_vector_topology_recovers_dashed_route_from_separate_solid_fragments() -> None:
    paths = [
        PathEvidence(
            id=f"vec-dash-{index}",
            page_index=0,
            points=[(start, 300), (end, 300)],
            bbox=BBox(x=start, y=300, w=end - start, h=1),
            origin="pdf_vector",
            primitive="line",
            stroke_width=2.0,
        )
        for index, (start, end) in enumerate(
            [(100, 160), (180, 240), (260, 320), (340, 400), (420, 480)]
        )
    ]
    result = build_page_topology(
        page=_page_evidence(paths=paths),
        nodes=[_node("n-left", 80), _node("n-right", 460)],
    )

    assert len(result.line_style_evidence) == 1
    style = result.line_style_evidence[0]
    assert style.visual_style == "dashed"
    assert style.source == "vector_fragment_pattern"
    assert style.source_path_ids == [f"vec-dash-{index}" for index in range(5)]
    assert len(result.edges) == 1
    assert result.edges[0].line_type == "other"
    assert result.edges[0].attributes["visual_style"] == "dashed"
    assert result.edges[0].attributes["visual_style_confidence"] > 0.7
    assert result.edges[0].source_evidence_ids == style.source_path_ids


def test_vector_topology_does_not_guess_style_from_two_broken_segments() -> None:
    paths = [
        PathEvidence(
            id="vec-left-part",
            page_index=0,
            points=[(100, 300), (260, 300)],
            bbox=BBox(x=100, y=300, w=160, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
        PathEvidence(
            id="vec-right-part",
            page_index=0,
            points=[(280, 300), (480, 300)],
            bbox=BBox(x=280, y=300, w=200, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
    ]
    result = build_page_topology(
        page=_page_evidence(paths=paths),
        nodes=[_node("n-left", 80), _node("n-right", 460)],
    )

    assert result.line_style_evidence == []


def test_topology_attaches_both_sides_of_an_inline_component() -> None:
    paths = [
        PathEvidence(
            id="vec-left",
            page_index=0,
            points=[(100, 300), (490, 300)],
            bbox=BBox(x=100, y=300, w=390, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
        PathEvidence(
            id="vec-right",
            page_index=0,
            points=[(510, 300), (900, 300)],
            bbox=BBox(x=510, y=300, w=390, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
    ]
    page = _page_evidence(paths=paths)
    left = _node("n-left", 80)
    valve = _node("n-valve", 480)
    right = _node("n-right", 880)

    result = build_page_topology(page=page, nodes=[left, valve, right])

    endpoint_pairs = {frozenset((edge.from_node, edge.to_node)) for edge in result.edges}
    assert endpoint_pairs == {
        frozenset(("n-left", "n-valve")),
        frozenset(("n-valve", "n-right")),
    }


def test_proper_crossing_is_reported_but_not_joined() -> None:
    paths = [
        PathEvidence(
            id="vec-horizontal",
            page_index=0,
            points=[(100, 300), (900, 300)],
            bbox=BBox(x=100, y=300, w=800, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
        PathEvidence(
            id="vec-vertical",
            page_index=0,
            points=[(500, 100), (500, 500)],
            bbox=BBox(x=500, y=100, w=1, h=400),
            origin="pdf_vector",
            primitive="line",
        ),
    ]
    page = _page_evidence(paths=paths)
    nodes = [
        _node("n-left", 80),
        _node("n-right", 880),
        ReconciledNode(
            id="n-top",
            kind="equipment",
            label="top",
            bbox_global=BBox(x=480, y=80, w=40, h=40),
            page_index=0,
            confidence="high",
        ),
        ReconciledNode(
            id="n-bottom",
            kind="equipment",
            label="bottom",
            bbox_global=BBox(x=480, y=480, w=40, h=40),
            page_index=0,
            confidence="high",
        ),
    ]

    result = build_page_topology(page=page, nodes=nodes)

    assert len(result.edges) == 2
    assert any(item["type"] == "crossing_or_junction" for item in result.ambiguities)


def test_unused_symbol_stroke_does_not_create_crossing_review_task() -> None:
    paths = [
        PathEvidence(
            id="vec-pipe",
            page_index=0,
            points=[(100, 300), (900, 300)],
            bbox=BBox(x=100, y=300, w=800, h=1),
            origin="pdf_vector",
            primitive="line",
        ),
        PathEvidence(
            id="vec-symbol-stroke",
            page_index=0,
            points=[(500, 200), (500, 400)],
            bbox=BBox(x=500, y=200, w=1, h=200),
            origin="pdf_vector",
            primitive="line",
        ),
    ]
    result = build_page_topology(
        page=_page_evidence(paths=paths),
        nodes=[_node("n-left", 80), _node("n-right", 880)],
    )

    assert len(result.edges) == 1
    assert result.used_path_ids == ["vec-pipe"]
    assert not result.ambiguities


def test_fusion_deduplicates_overlap_and_quality_enforces_structure() -> None:
    page = _page_evidence()
    detections = [
        DetectionRecord(
            id="det-a",
            page_index=0,
            tile_id="p0-r0-c0",
            kind="equipment",
            label="P-101",
            bbox=BBox(x=100, y=100, w=50, h=50),
            confidence="high",
        ),
        DetectionRecord(
            id="det-b",
            page_index=0,
            tile_id="p0-r0-c1",
            kind="equipment",
            label="P-101",
            bbox=BBox(x=105, y=102, w=50, h=50),
            confidence="medium",
        ),
    ]
    fused = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[page],
        detections=detections,
        topology=[],
        per_page_status={0: "ok"},
    )
    assert len(fused.graph.nodes) == 1
    assert fused.graph.nodes[0].confidence == "high"
    assert fused.graph.nodes[0].system_confidence is not None
    assert fused.graph.nodes[0].attributes["source_tiles"] == ["p0-r0-c0", "p0-r0-c1"]

    report = assess_quality(graph=fused.graph, pages=[page], topology=[])
    assert not report.critical_violations


def test_fusion_rejects_unsupported_opc_and_normalises_taxonomy() -> None:
    page = _page_evidence()
    detections = [
        DetectionRecord(
            id="det-opc-unsupported",
            page_index=0,
            tile_id="p0-r1-c1",
            kind="opc",
            label="QV01",
            bbox=BBox(x=450, y=250, w=80, h=40),
            confidence="high",
        ),
        DetectionRecord(
            id="det-opc-supported",
            page_index=0,
            tile_id="p0-r1-c4",
            kind="opc",
            label="DW02-0007",
            bbox=BBox(x=940, y=250, w=50, h=40),
            confidence="high",
            attributes={"direction": "outgoing"},
        ),
        DetectionRecord(
            id="det-valve",
            page_index=0,
            tile_id="p0-r1-c2",
            kind="equipment",
            label="XV-101",
            bbox=BBox(x=300, y=250, w=50, h=40),
            confidence="high",
            attributes={"equipment_class": "valve", "valve_type": "ball_valve"},
        ),
        DetectionRecord(
            id="det-instrument",
            page_index=0,
            tile_id="p0-r1-c3",
            kind="instrument",
            label="PT-101",
            bbox=BBox(x=600, y=200, w=60, h=60),
            confidence="high",
            attributes={"instrument_class": "pressure_transmitter"},
        ),
    ]

    fused = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[page],
        detections=detections,
        topology=[],
        per_page_status={0: "ok"},
    )

    assert "det-opc-unsupported" not in {
        annotation_id for node in fused.graph.nodes for annotation_id in node.source_annotation_ids
    }
    assert any(
        conflict["type"] == "rejected_opc_without_boundary_evidence"
        and conflict["status"] == "resolved"
        for conflict in fused.graph.conflicts
    )
    supported_opc = next(node for node in fused.graph.nodes if node.kind == "opc")
    assert supported_opc.attributes["direction"] == "out"
    valve = next(node for node in fused.graph.nodes if node.label == "XV-101")
    assert valve.attributes["valve_type"] == "ball"
    instrument = next(node for node in fused.graph.nodes if node.label == "PT-101")
    assert instrument.attributes["instrument_function"] == "transmitter"
    assert instrument.attributes["measured_variable"] == "pressure"
    assert "instrument_class" not in instrument.attributes


def test_fusion_cautiously_filters_native_text_and_retypes_instrument_tag() -> None:
    page = _page_evidence().model_copy(
        update={
            "text_spans": [
                TextEvidence(
                    id="text-line",
                    text="100-GA-00101-M15B-N",
                    bbox=BBox(x=100, y=100, w=180, h=14),
                ),
                TextEvidence(
                    id="text-pi",
                    text="PI-00203",
                    bbox=BBox(x=400, y=100, w=70, h=14),
                ),
            ]
        }
    )
    fused = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[page],
        detections=[
            DetectionRecord(
                id="det-line-label",
                page_index=0,
                tile_id="p0-full",
                kind="equipment",
                label="100-GA-00101-M15B-N",
                bbox=BBox(x=95, y=95, w=190, h=24),
                confidence="medium",
            ),
            DetectionRecord(
                id="det-pi",
                page_index=0,
                tile_id="p0-full",
                kind="equipment",
                label="PI-00203",
                bbox=BBox(x=390, y=80, w=90, h=70),
                confidence="high",
            ),
        ],
        topology=[],
        per_page_status={0: "ok"},
    )

    assert [node.label for node in fused.graph.nodes] == ["PI-00203"]
    instrument = fused.graph.nodes[0]
    assert instrument.kind == "instrument"
    assert instrument.attributes["instrument_function"] == "indicator"
    assert instrument.attributes["measured_variable"] == "pressure"
    assert any(
        conflict["type"] == "rejected_non_connectable_text" for conflict in fused.graph.conflicts
    )
    assert any(
        conflict["type"] == "deterministic_kind_correction" for conflict in fused.graph.conflicts
    )


def test_project_legend_tag_retypes_and_enriches_unknown_instrument_prefix() -> None:
    legend = LegendPack(
        entries=[
            LegendEntry(
                label="QZ",
                description="project-specific quality transmitter",
                symbol_class="transmitter",
                kind="instrument",
                attributes={
                    "instrument_function": "transmitter",
                    "measured_variable": "analysis",
                },
                source="legend_extracted",
            )
        ]
    )
    fused = fuse_objects(
        source_name="drawing.pdf",
        pages=[_page_evidence()],
        detections=[
            DetectionRecord(
                id="det-qz",
                page_index=0,
                tile_id="p0-full",
                kind="equipment",
                label="QZ-101",
                bbox=BBox(x=300, y=200, w=80, h=70),
                confidence="high",
            )
        ],
        per_page_status={0: "ok"},
        legend_pack=legend,
    )

    node = fused.graph.nodes[0]
    assert node.kind == "instrument"
    assert node.attributes["instrument_function"] == "transmitter"
    assert node.attributes["measured_variable"] == "analysis"
    assert node.attributes["tag_semantics_basis"] == "project_legend"


def test_final_element_tag_normalises_equipment_as_a_control_valve() -> None:
    fused = fuse_objects(
        source_name="drawing.pdf",
        pages=[_page_evidence()],
        detections=[
            DetectionRecord(
                id="det-fv",
                page_index=0,
                tile_id="p0-full",
                kind="equipment",
                label="FV-101",
                bbox=BBox(x=300, y=200, w=80, h=70),
                confidence="high",
            )
        ],
        per_page_status={0: "ok"},
    )

    node = fused.graph.nodes[0]
    assert node.kind == "equipment"
    assert node.attributes["valve_type"] == "control"
    assert node.attributes["instrument_function"] == "valve_actuator"


def test_native_identity_prevents_nearby_tag_attributes_from_contaminating_node() -> None:
    page = _page_evidence().model_copy(
        update={
            "text_spans": [
                TextEvidence(
                    id="txt-vessel",
                    text="2401-V-001",
                    bbox=BBox(x=305, y=205, w=85, h=16),
                )
            ]
        }
    )
    fused = fuse_objects(
        source_name="drawing.pdf",
        pages=[page],
        detections=[
            DetectionRecord(
                id="det-vessel",
                page_index=0,
                tile_id="p0-r1-c1",
                kind="equipment",
                label="2401-V-001",
                raw_text="2401-V-001",
                bbox=BBox(x=300, y=190, w=110, h=90),
                confidence="high",
                attributes={"equipment_class": "vessel"},
            ),
            DetectionRecord(
                id="det-nearby-fv",
                page_index=0,
                tile_id="p0-r1-c2",
                kind="equipment",
                label="FV-00301",
                raw_text="FV-00301",
                bbox=BBox(x=304, y=194, w=108, h=88),
                confidence="medium",
                attributes={
                    "valve_type": "control",
                    "instrument_function": "valve_actuator",
                    "loop_number": "00301",
                },
            ),
        ],
        per_page_status={0: "ok"},
    )

    assert len(fused.graph.nodes) == 1
    node = fused.graph.nodes[0]
    assert node.label == "2401-V-001"
    assert node.attributes["equipment_class"] == "vessel"
    assert "valve_type" not in node.attributes
    assert "instrument_function" not in node.attributes
    assert "loop_number" not in node.attributes
    assert any(conflict["type"] == "evidence_label_conflict" for conflict in fused.graph.conflicts)


def test_native_text_inventory_separates_assigned_unresolved_and_excluded_text() -> None:
    page = _page_evidence().model_copy(
        update={
            "text_spans": [
                TextEvidence(
                    id="txt-pi-prefix",
                    text="PI",
                    bbox=BBox(x=120, y=70, w=20, h=20),
                    block_index=1,
                    line_index=0,
                ),
                TextEvidence(
                    id="txt-pi-number",
                    text="00203",
                    bbox=BBox(x=105, y=95, w=50, h=20),
                    block_index=9,
                    line_index=3,
                ),
                TextEvidence(id="txt-unknown", text="QZ-009", bbox=BBox(x=300, y=80, w=70, h=20)),
                TextEvidence(id="txt-dn", text="DN20", bbox=BBox(x=500, y=80, w=50, h=20)),
            ]
        }
    )
    graph = ReconciledGraph(
        source_path="drawing.pdf",
        nodes=[
            ReconciledNode(
                id="n-pi",
                kind="instrument",
                label="PI-00203",
                bbox_global=BBox(x=90, y=70, w=100, h=60),
                page_index=0,
                confidence="high",
                source_evidence_ids=["txt-pi-prefix", "txt-pi-number"],
            )
        ],
        per_page_status={0: "ok"},
    )

    inventory = build_native_text_inventory(pages=[page], graph=graph)

    assert inventory.summary["reviewable_tag_count"] == 2
    assert inventory.summary["assigned_tag_count"] == 1
    assert inventory.summary["unresolved_tag_count"] == 1
    by_text = {item.text: item for item in inventory.items}
    assert by_text["PI 00203"].status == "assigned"
    assert by_text["QZ-009"].status == "unresolved"
    assert by_text["QZ-009"].candidate_kind == "unknown_tag"
    assert by_text["DN20"].status == "excluded"
    assert not by_text["DN20"].blocking


def test_fusion_rejects_dn_size_as_a_node_even_when_bbox_misses_native_text() -> None:
    fused = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[_page_evidence()],
        detections=[
            DetectionRecord(
                id="det-dn20",
                page_index=0,
                tile_id="p0-full",
                kind="equipment",
                label="DN20",
                bbox=BBox(x=700, y=400, w=80, h=40),
                confidence="medium",
            )
        ],
        topology=[],
        per_page_status={0: "ok"},
    )

    assert not fused.graph.nodes
    assert fused.graph.conflicts[0]["type"] == "rejected_non_connectable_text"


def test_interior_opc_with_explicit_reference_is_kept_for_page_graph_review() -> None:
    fused = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[_page_evidence()],
        detections=[
            DetectionRecord(
                id="det-opc-interior",
                page_index=0,
                tile_id="p0-r1-c2",
                kind="opc",
                label="DW02-0007",
                bbox=BBox(x=450, y=250, w=100, h=40),
                confidence="medium",
                attributes={
                    "direction": "out",
                    "drawing_ref": "DW02-0007",
                    "service": "compressed air",
                },
            )
        ],
        topology=[],
        per_page_status={0: "ok"},
    )

    opc = next(node for node in fused.graph.nodes if node.kind == "opc")
    assert opc.attributes["opc_context_required"] is True
    conflict = next(
        item for item in fused.graph.conflicts if item["type"] == "opc_context_validation"
    )
    assert conflict["node_id"] == opc.id
    assert conflict["status"] == "unresolved"


def test_shared_opc_reference_creates_only_a_bounded_pairing_question() -> None:
    first_page = _page_evidence()
    second_page = _page_evidence().model_copy(
        update={"page_index": 1, "source_ref": "drawing#page=2"}
    )
    detections = [
        DetectionRecord(
            id="det-opc-out",
            page_index=0,
            tile_id="p0-r1-c2",
            kind="opc",
            label="DW02-0003",
            bbox=BBox(x=450, y=250, w=100, h=40),
            confidence="medium",
            attributes={"direction": "out", "service": "compressed air to V-001"},
        ),
        DetectionRecord(
            id="det-opc-in",
            page_index=1,
            tile_id="p1-r1-c2",
            kind="opc",
            label="DW02-0003",
            bbox=BBox(x=450, y=250, w=100, h=40),
            confidence="medium",
            attributes={"direction": "in", "service": "compressed air from V-002"},
        ),
    ]

    graph = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[first_page, second_page],
        detections=detections,
        topology=[],
        per_page_status={0: "ok", 1: "ok"},
    ).graph

    pairing = [
        conflict for conflict in graph.conflicts if conflict["type"] == "ambiguous_opc_evidence"
    ]
    assert len(pairing) == 1
    assert len(pairing[0]["node_ids"]) == 2
    assert graph.edges == []


def test_reciprocal_title_block_opcs_create_high_confidence_cross_sheet_edge() -> None:
    page_a = _page_evidence().model_copy(
        update={
            "text_spans": [
                TextEvidence(
                    id="title-a",
                    text="240100ST-DW02-0003",
                    bbox=BBox(x=800, y=520, w=160, h=20),
                )
            ]
        }
    )
    page_b = _page_evidence().model_copy(
        update={
            "page_index": 1,
            "source_ref": "drawing#page=2",
            "text_spans": [
                TextEvidence(
                    id="title-b",
                    text="240100ST-DW02-0004",
                    bbox=BBox(x=800, y=520, w=160, h=20),
                )
            ],
        }
    )
    graph = _fuse_evidence(
        source_name="drawing.pdf",
        pages=[page_a, page_b],
        detections=[
            DetectionRecord(
                id="det-out",
                page_index=0,
                tile_id="p0-full",
                kind="opc",
                label="DW02-0004",
                bbox=BBox(x=940, y=250, w=50, h=40),
                confidence="high",
                attributes={"direction": "out", "service": "压缩空气至2401-V-001"},
            ),
            DetectionRecord(
                id="det-in",
                page_index=1,
                tile_id="p1-full",
                kind="opc",
                label="DW02-0003",
                bbox=BBox(x=10, y=250, w=50, h=40),
                confidence="high",
                attributes={"direction": "in", "service": "压缩空气自2401-V-002"},
            ),
        ],
        topology=[],
        per_page_status={0: "ok", 1: "ok"},
    ).graph

    assert len(graph.edges) == 1
    edge = graph.edges[0]
    assert edge.cross_sheet is True
    assert edge.confidence == "high"
    assert edge.attributes["match_basis"] == "reciprocal_title_block_references"
    assert graph.dangling_opcs == []


def test_opc_pairing_uses_group_candidates_and_one_to_one_assignment() -> None:
    pages = [
        _page_evidence().model_copy(
            update={"page_index": index, "source_ref": f"drawing#page={index + 1}"}
        )
        for index in range(3)
    ]
    detections = [
        DetectionRecord(
            id=f"det-opc-{index}",
            page_index=index,
            tile_id=f"p{index}-r1-c2",
            kind="opc",
            label="DW02-0003",
            bbox=BBox(x=450, y=250, w=100, h=40),
            confidence="medium",
            attributes={
                "direction": "out" if index == 0 else "in",
                "service": ["compressed air", "compressed air to V-1", "instrument air"][index],
            },
        )
        for index in range(3)
    ]

    graph = _fuse_evidence(
        source_name="drawing.pdf",
        pages=pages,
        detections=detections,
        topology=[],
        per_page_status={index: "ok" for index in range(3)},
    ).graph

    pairing = [
        conflict for conflict in graph.conflicts if conflict["type"] == "ambiguous_opc_evidence"
    ]
    assert len(pairing) == 1
    assert pairing[0]["candidate_group_size"] == 3
    assert len(pairing[0]["candidate_pairs"]) == 3
    assert pairing[0]["candidate_score"] == max(
        candidate["score"] for candidate in pairing[0]["candidate_pairs"]
    )


def test_quality_marks_ambiguity_duplicates_and_isolation_partial() -> None:
    page = _page_evidence()
    graph = ReconciledGraph(
        source_path="drawing.pdf",
        nodes=[
            ReconciledNode(
                id="n-a",
                kind="instrument",
                label="PT-101",
                bbox_global=BBox(x=100, y=100, w=50, h=50),
                page_index=0,
                confidence="high",
            ),
            ReconciledNode(
                id="n-b",
                kind="instrument",
                label="PT 101",
                bbox_global=BBox(x=300, y=100, w=50, h=50),
                page_index=0,
                confidence="high",
            ),
        ],
        conflicts=[{"type": "evidence_label_conflict", "status": "unresolved"}],
        per_page_status={0: "ok"},
    )

    report = assess_quality(graph=graph, pages=[page], topology=[])

    warning_types = {warning["type"] for warning in report.warnings}
    assert report.status == "partial"
    assert "unresolved_ambiguities" in warning_types
    assert "duplicate_same_page_tags" in warning_types
    assert "excessive_isolated_nodes" in warning_types


def test_pid_engine_defaults_to_legacy(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("DIAGEX_PID_ENGINE", raising=False)
    assert PidConfig().engine == "legacy"
    monkeypatch.setenv("DIAGEX_PID_ENGINE", "v2")
    assert PidConfig().engine == "evidence-v2"


def test_phase_specific_models_are_loaded_from_environment(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setenv("DIAGEX_LLM_PROVIDER", "openrouter")
    monkeypatch.setenv("OPENROUTER_API_KEY", "test-key")
    monkeypatch.setenv("DIAGEX_MODEL", "fallback/model")
    monkeypatch.setenv("DIAGEX_VISION_MODEL", "fast/vision")
    monkeypatch.setenv("DIAGEX_REASONING_MODEL", "strong/reasoner")

    config = LLMConfig.from_env()

    assert config.model == "fallback/model"
    assert config.vision_model == "fast/vision"
    assert config.reasoning_model == "strong/reasoner"


def test_evidence_v2_stops_after_first_non_retryable_perception_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = tmp_path / "fatal-perception.pdf"
    document = fitz.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((20, 20), "P&ID TEST")
    document.save(pdf)
    document.close()
    response = httpx.Response(
        404,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/messages"),
    )
    error = anthropic.APIStatusError("no route", response=response, body=None)

    class FatalClient:
        calls = 0

        def __init__(self, config: object, budgets: object = None) -> None:
            self.config = config
            self.retries_total = 0

        def reset_retry_counter(self) -> None:
            self.retries_total = 0

        def messages_create(self, **kwargs: object) -> object:
            type(self).calls += 1
            raise error

    monkeypatch.setattr("diagex.extractors.pid_evidence.LLMClient", FatalClient)
    cfg = Config(llm=LLMConfig(model="fake", anthropic_api_key="unused"))

    with pytest.raises(anthropic.APIStatusError):
        run_pid_evidence_extract(
            diagram=pdf,
            symbol_standard="isa-5.1",
            legend_path=None,
            legend_pages=None,
            legend_region=None,
            no_legend=True,
            legend_key=None,
            effort="medium",
            config=cfg,
            persist=False,
            out_path=None,
            confidence_report_path=None,
            console=None,
        )

    assert FatalClient.calls == 1


def test_evidence_v2_stops_after_first_non_retryable_page_graph_error(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = tmp_path / "fatal-page-graph.pdf"
    document = fitz.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((20, 20), "P&ID TEST")
    page.draw_rect(fitz.Rect(35, 80, 65, 120))
    page.draw_rect(fitz.Rect(335, 80, 365, 120))
    page.draw_line((65, 100), (335, 100))
    document.save(pdf)
    document.close()
    response = httpx.Response(
        404,
        request=httpx.Request("POST", "https://openrouter.ai/api/v1/messages"),
    )
    error = anthropic.APIStatusError("no image endpoint", response=response, body=None)

    class PageGraphFatalClient:
        tools_seen: list[str] = []

        def __init__(self, config: object, budgets: object = None) -> None:
            self.config = config
            self.retries_total = 0

        def reset_retry_counter(self) -> None:
            self.retries_total = 0

        def messages_create(self, **kwargs: object) -> object:
            if not kwargs.get("tools"):
                type(self).tools_seen.append("page_graph_reasoning")
                return SimpleNamespace(
                    usage=SimpleNamespace(
                        input_tokens=100,
                        output_tokens=20,
                        cache_read_input_tokens=0,
                        cache_creation_input_tokens=0,
                    ),
                    stop_reason="end_turn",
                    content=[{"type": "text", "text": "E001 | keep | - | forward"}],
                )
            tool_name = kwargs["tools"][0]["name"]  # type: ignore[index]
            type(self).tools_seen.append(tool_name)
            if tool_name == "submit_page_graph":
                raise error
            if tool_name == "submit_line_evidence":
                return SimpleNamespace(
                    usage=SimpleNamespace(
                        input_tokens=100,
                        output_tokens=20,
                        cache_read_input_tokens=0,
                        cache_creation_input_tokens=0,
                    ),
                    content=[
                        {
                            "type": "tool_use",
                            "name": tool_name,
                            "input": {
                                "assessments": [
                                    {
                                        "candidate_ref": "E001",
                                        "route_visible": "yes",
                                        "endpoint_alignment": "both",
                                        "observed_style": "solid",
                                        "confidence": "high",
                                    }
                                ]
                            },
                        }
                    ],
                )
            return SimpleNamespace(
                usage=SimpleNamespace(
                    input_tokens=100,
                    output_tokens=20,
                    cache_read_input_tokens=0,
                    cache_creation_input_tokens=0,
                ),
                content=[
                    {
                        "type": "tool_use",
                        "name": "submit_pid_objects",
                        "input": {
                            "objects": [
                                {
                                    "kind": "equipment",
                                    "label": "V-101",
                                    "bbox": {"x": 0.08, "y": 0.38, "w": 0.09, "h": 0.24},
                                    "confidence": "high",
                                },
                                {
                                    "kind": "equipment",
                                    "label": "V-102",
                                    "bbox": {"x": 0.83, "y": 0.38, "w": 0.09, "h": 0.24},
                                    "confidence": "high",
                                },
                            ]
                        },
                    }
                ],
            )

    monkeypatch.setattr("diagex.extractors.pid_evidence.LLMClient", PageGraphFatalClient)
    cfg = Config(llm=LLMConfig(model="fake", anthropic_api_key="unused"))

    with pytest.raises(anthropic.APIStatusError):
        run_pid_evidence_extract(
            diagram=pdf,
            symbol_standard="isa-5.1",
            legend_path=None,
            legend_pages=None,
            legend_region=None,
            no_legend=True,
            legend_key=None,
            effort="medium",
            config=cfg,
            persist=False,
            out_path=None,
            confidence_report_path=None,
            console=None,
        )

    assert PageGraphFatalClient.tools_seen == [
        "submit_pid_objects",
        "submit_line_evidence",
        "page_graph_reasoning",
        "submit_page_graph",
    ]


def test_evidence_v2_end_to_end_with_stateless_fake_model(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    pdf = tmp_path / "simple.pdf"
    document = fitz.open()
    page = document.new_page(width=400, height=200)
    page.insert_text((20, 20), "P&ID TEST")
    page.draw_rect(fitz.Rect(35, 80, 65, 120))
    page.draw_rect(fitz.Rect(335, 80, 365, 120))
    page.draw_line((65, 100), (335, 100))
    document.save(pdf)
    document.close()

    class FakeClient:
        requests: list[tuple[str, str, dict[str, object]]] = []

        def __init__(self, config: object, budgets: object = None) -> None:
            self.config = config
            self.retries_total = 0

        def reset_retry_counter(self) -> None:
            self.retries_total = 0

        def messages_create(self, **kwargs: object) -> object:
            usage = SimpleNamespace(
                input_tokens=100,
                output_tokens=20,
                cache_read_input_tokens=0,
                cache_creation_input_tokens=0,
            )
            if not kwargs.get("tools"):
                self.requests.append(
                    (
                        "page_graph_reasoning",
                        self.config.reasoning_mode,  # type: ignore[attr-defined]
                        kwargs,
                    )
                )
                return SimpleNamespace(
                    usage=usage,
                    stop_reason="end_turn",
                    content=[
                        {
                            "type": "text",
                            "text": "E001 | keep | process | forward | high | visible solid line",
                        }
                    ],
                )
            tool_name = kwargs["tools"][0]["name"]  # type: ignore[index]
            self.requests.append(
                (
                    tool_name,
                    self.config.reasoning_mode,  # type: ignore[attr-defined]
                    kwargs,
                )
            )
            if tool_name == "submit_page_graph":
                return SimpleNamespace(
                    usage=usage,
                    content=[
                        {
                            "type": "tool_use",
                            "name": tool_name,
                            "input": {
                                "candidate_decisions": [
                                    {
                                        "candidate_ref": "E001",
                                        "decision": "keep",
                                        "confidence": "high",
                                        "evidence": ["visible solid line"],
                                    }
                                ],
                            },
                        }
                    ],
                )
            if tool_name == "submit_line_evidence":
                return SimpleNamespace(
                    usage=usage,
                    content=[
                        {
                            "type": "tool_use",
                            "name": tool_name,
                            "input": {
                                "assessments": [
                                    {
                                        "candidate_ref": "E001",
                                        "route_visible": "yes",
                                        "endpoint_alignment": "both",
                                        "observed_style": "solid",
                                        "confidence": "high",
                                    }
                                ]
                            },
                        }
                    ],
                )
            return SimpleNamespace(
                usage=usage,
                content=[
                    {
                        "type": "tool_use",
                        "name": "submit_pid_objects",
                        "input": {
                            "objects": [
                                {
                                    "kind": "equipment",
                                    "label": "V-101",
                                    "bbox": {"x": 0.08, "y": 0.38, "w": 0.09, "h": 0.24},
                                    "confidence": "high",
                                    "attributes": {"equipment_class": "vessel"},
                                },
                                {
                                    "kind": "equipment",
                                    "label": "V-102",
                                    "bbox": {"x": 0.83, "y": 0.38, "w": 0.09, "h": 0.24},
                                    "confidence": "high",
                                    "attributes": {"equipment_class": "vessel"},
                                },
                            ]
                        },
                    }
                ],
            )

    monkeypatch.setattr("diagex.extractors.pid_evidence.LLMClient", FakeClient)
    cfg = Config(
        llm=LLMConfig(
            model="fake",
            vision_model="fake-vision",
            reasoning_model="fake-reasoner",
            reasoning_mode="enabled",
            anthropic_api_key="unused",
        )
    )
    cfg.runs_dir = tmp_path / "runs"

    result = run_pid_evidence_extract(
        diagram=pdf,
        symbol_standard="isa-5.1",
        legend_path=None,
        legend_pages=None,
        legend_region=None,
        no_legend=True,
        legend_key=None,
        effort="medium",
        config=cfg,
        persist=True,
        out_path=None,
        confidence_report_path=None,
        console=None,
    )

    assert result.engine == "evidence-v2"
    assert result.run_dir is not None
    assert (result.run_dir / "evidence" / "page-0001.json").is_file()
    inventory_path = result.run_dir / "evidence" / "native-text-inventory.json"
    assert inventory_path.is_file()
    assert "summary" in json.loads(inventory_path.read_text(encoding="utf-8"))
    assert (result.run_dir / "checkpoints" / "page_graph" / "page-0001.json").is_file()
    assert (result.run_dir / "checkpoints" / "manifest.json").is_file()
    assert (result.run_dir / "quality.report.json").is_file()
    assert (result.run_dir / "graph.json").is_file()
    reuse_report = json.loads(
        (result.run_dir / "reuse.report.json").read_text(encoding="utf-8")
    )
    assert reuse_report["mode"] == "new"
    assert reuse_report["reused_total"] == 0
    assert reuse_report["computed_total"] > 0
    public_result = json.loads((result.run_dir / "result.json").read_text(encoding="utf-8"))
    assert public_result["reuse_report_path"] == str(result.run_dir / "reuse.report.json")
    assert len(result.graph.nodes) == 2
    assert result.cost_summary["tool_call_counts"]["submit_pid_objects"] == 1
    assert result.cost_summary["tool_call_counts"]["submit_page_graph"] == 2
    reasoning_request = next(
        request for request in FakeClient.requests if request[0] == "page_graph_reasoning"
    )
    assert reasoning_request[1] == "enabled"
    assert reasoning_request[2]["thinking"]["type"] == "adaptive"
    assert "tools" not in reasoning_request[2]
    page_graph_request = next(
        request for request in FakeClient.requests if request[0] == "submit_page_graph"
    )
    assert page_graph_request[1] == "enabled"
    assert page_graph_request[2]["thinking"]["type"] == "disabled"
    assert page_graph_request[2]["tool_choice"] == {
        "type": "tool",
        "name": "submit_page_graph",
    }
    page_graph_content = page_graph_request[2]["messages"][0]["content"]
    assert [block["type"] for block in page_graph_content] == ["text"]
    assert all(edge.from_node != edge.to_node for edge in result.graph.edges)
    review = ReviewStore.open(
        result.run_dir,
        source_path=pdf,
        rater="Verifier",
        out_dir=tmp_path / "review",
    )
    assert len(review.public_state()["graph"]["nodes"]) == 2
