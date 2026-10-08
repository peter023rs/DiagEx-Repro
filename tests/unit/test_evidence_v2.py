from __future__ import annotations

import json
from pathlib import Path
from types import SimpleNamespace

import anthropic
import fitz
import httpx
import pytest
from PIL import Image

from diagex.config import Config, LLMConfig
from diagex.extractors.evidence_checkpoint import (
    CheckpointStore,
    find_resumable_run,
    find_resumable_run_with_report,
)
from diagex.extractors.symbol_detection import run_symbol_detection
from diagex.llm.cost import CostTracker
from diagex.ui.progress import NullReporter
from diagex.vision.evidence import (
    PageEvidence,
    PathEvidence,
    TextEvidence,
    classify_page,
    classify_pdf_dash_pattern,
    extract_page_evidence,
)
from diagex.vision.models import (
    BBox,
    DiagramPage,
    Tile,
)
from diagex.vision.perception import (
    _SUBMIT_TOOL,
    NormalizedBBox,
    PerceivedObject,
    PerceptionResponseFormatError,
    parse_perception_response,
    perceive_tile,
    project_batch,
)
from diagex.vision.tiling import FixedGridStrategy, ownership_core, tile
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
    assert set(schema["properties"]) == {"candidate_results", "proposals"}
    object_properties = schema["properties"]["candidate_results"]["items"]["properties"]
    assert "candidate_id" in object_properties
    assert "symbol" not in object_properties
    assert "bbox" not in object_properties
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
    assert outcome.detections == []
    assert outcome.batch.candidate_reviews[0]["object"]["printed_tag"] == "PI-101"
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
    assert outcome.detections == []
    assert outcome.batch.candidate_reviews[0]["object"]["printed_tag"] == "PI-101"
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

    monkeypatch.setattr("diagex.extractors.symbol_detection.LLMClient", FatalClient)
    cfg = Config(llm=LLMConfig(model="fake", anthropic_api_key="unused"))

    with pytest.raises(anthropic.APIStatusError):
        run_symbol_detection(
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
            console=None,
        )

    assert FatalClient.calls == 1


@pytest.mark.parametrize(
    "rotation,expected",
    [
        (0, [(60, 200), (540, 200)]),
        (90, [(200, 60), (200, 540)]),
        (180, [(540, 200), (60, 200)]),
        (270, [(200, 540), (200, 60)]),
    ],
)
def test_native_geometry_aligns_with_rotated_render(tmp_path, rotation, expected):
    pdf = tmp_path / "rotated.pdf"
    with fitz.open() as doc:
        native = doc.new_page(width=300, height=200)
        native.draw_line((30, 100), (270, 100))
        native.insert_text((30, 40), "V-101")
        native.set_rotation(rotation)
        doc.save(pdf)
    with fitz.open(pdf) as doc:
        pix = doc[0].get_pixmap(matrix=fitz.Matrix(2, 2))
        rendered = DiagramPage(
            page_index=0,
            width=pix.width,
            height=pix.height,
            dpi=144,
            effective_dpi=144,
            is_scanned=False,
            source_ref="rotated",
        )
        evidence = extract_page_evidence(page=rendered, source_path=pdf, pdf_page=doc[0])
        assert evidence.paths[0].points == expected
        midpoint = tuple(round((a + b) / 2) for a, b in zip(*expected, strict=True))
        assert min(pix.pixel(*midpoint)) < 100
        span = next(s for s in evidence.text_spans if s.text == "V-101")
        assert 0 <= span.bbox.x < span.bbox.x2 <= pix.width
        assert 0 <= span.bbox.y < span.bbox.y2 <= pix.height
        assert any(
            min(pix.pixel(x, y)) < 100
            for x in range(span.bbox.x, span.bbox.x2)
            for y in range(span.bbox.y, span.bbox.y2)
        )
        assert evidence.native_coordinate_frame == "rendered_page"


def test_cached_rotated_evidence_is_repaired_without_discarding_perception(tmp_path):
    from diagex.extractors.evidence_checkpoint import CheckpointStore
    from diagex.extractors.symbol_detection import _inspect_pages
    from diagex.vision.loader import load

    pdf = tmp_path / "cached.pdf"
    with fitz.open() as doc:
        native = doc.new_page(width=300, height=200)
        native.draw_line((30, 100), (270, 100))
        native.set_rotation(90)
        doc.save(pdf)
    run = tmp_path / "run"
    store = CheckpointStore.create(
        run_dir=run, source_sha256="source", config_sha256="config", run_id="run"
    )
    first, _ = _inspect_pages(
        source=load(pdf), diagram=pdf, store=store, run_dir=run, reporter=NullReporter()
    )
    public = run / "evidence/page-0001.json"
    expected = first[0].paths[0].points
    first[0].native_coordinate_frame = "legacy"
    first[0].paths[0].points = [(1, 1), (2, 2)]
    public.write_text(first[0].model_dump_json())
    store.write_json_artifact("perception", "saved", {"observations": ["retain"]})
    repaired, _ = _inspect_pages(
        source=load(pdf), diagram=pdf, store=store, run_dir=run, reporter=NullReporter()
    )
    assert repaired[0].paths[0].points == expected
    assert repaired[0].native_coordinate_frame == "rendered_page"
    assert store.read_json_artifact("perception", "saved") == {"observations": ["retain"]}


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
            tool_name = kwargs["tools"][0]["name"]
            assert tool_name == "submit_pid_objects"
            self.requests.append((tool_name, self.config.reasoning_mode, kwargs))
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
                                    "candidate_id": json.loads(
                                        kwargs["messages"][0]["content"][1]["text"].split("\n", 1)[
                                            1
                                        ]
                                    )["native_symbol_candidates"][0]["candidate_id"],
                                    "confidence": "high",
                                    "attributes": {"equipment_class": "vessel"},
                                },
                                {
                                    "kind": "equipment",
                                    "label": "V-102",
                                    "candidate_id": json.loads(
                                        kwargs["messages"][0]["content"][1]["text"].split("\n", 1)[
                                            1
                                        ]
                                    )["native_symbol_candidates"][1]["candidate_id"],
                                    "confidence": "high",
                                    "attributes": {"equipment_class": "vessel"},
                                },
                            ]
                        },
                    }
                ],
            )

    monkeypatch.setattr("diagex.extractors.symbol_detection.LLMClient", FakeClient)
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

    result = run_symbol_detection(
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
        fresh=True,
        console=None,
    )

    assert result.observation_count == 2
    assert result.quality_status == "complete"
    assert not (result.run_dir / "graph.json").exists()
    before = (result.run_dir / "detection.json").read_bytes()
    calls = len(FakeClient.requests)
    resumed = run_symbol_detection(
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
        fresh=False,
        console=None,
    )
    assert resumed.run_dir != result.run_dir
    assert resumed.observation_count == 2
    assert len(FakeClient.requests) == calls
    assert (result.run_dir / "detection.json").read_bytes() == before
    fresh = run_symbol_detection(
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
        fresh=True,
        console=None,
    )
    assert fresh.run_dir not in {result.run_dir, resumed.run_dir}
    assert len(FakeClient.requests) > calls
