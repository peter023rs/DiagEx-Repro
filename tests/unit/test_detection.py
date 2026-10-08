from __future__ import annotations

import hashlib
import io
import json
from types import SimpleNamespace

import fitz
import pytest

from diagex.config import Config, LLMConfig
from diagex.detection.artifacts import DetectionStore, write_detection_bundle
from diagex.extractors.evidence_checkpoint import atomic_write_json
from diagex.vision.evidence import PageEvidence
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.vision.models import BBox
from diagex.vision.perception import DetectionRecord
from diagex.web.server import Workbench, WorkbenchError


def inputs(tmp_path):
    source = tmp_path / "drawing.pdf"
    with fitz.open() as doc:
        page = doc.new_page(width=400, height=250)
        page.insert_text((15, 20), "P&ID TEST")
        page.draw_rect(fitz.Rect(40, 60, 90, 190))
        page.draw_circle((140, 80), 10)
        doc.save(source)
    page = PageEvidence(
        page_index=0,
        source_ref="drawing#1",
        width=400,
        height=250,
        dpi=72,
        effective_dpi=72,
        is_scanned=False,
        role="pid",
    )
    detection = DetectionRecord(
        id="d1",
        page_index=0,
        tile_id="t1",
        kind="equipment",
        label="V-001",
        bbox=BBox(x=40, y=60, w=50, h=130),
        confidence="high",
        attributes={"equipment_class": "vessel", "symbol_candidate_id": "c1"},
    )
    legend = LegendPack(
        entries=[LegendEntry(label="Vessel", symbol_class="vessel", kind="equipment")]
    )
    return source, page, detection, legend


def setup_store(tmp_path):
    source, page, detection, legend = inputs(tmp_path)
    run = tmp_path / "runs" / "drawing" / "run-detection"
    run.mkdir(parents=True)
    write_detection_bundle(
        run,
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
        pages=[page],
        detections=[detection],
        legend_pack=legend,
        per_page_status={0: "ok"},
        reviews=[],
        candidates=[
            {"id": "c1", "page_index": 0, "bbox": detection.bbox.model_dump()},
            {"id": "c2", "page_index": 0, "bbox": {"x": 130, "y": 70, "w": 20, "h": 20}},
        ],
    )
    atomic_write_json(run / "workbench.json", {"source_path": str(source)})
    return DetectionStore(run), source, page


@pytest.mark.parametrize(
    "uncertain_legend,guard_stop", [(False, False), (True, False), (False, True)]
)
def test_detection_stops_without_graph(tmp_path, monkeypatch, uncertain_legend, guard_stop):
    from diagex.extractors import symbol_detection as pipeline

    source, page, detection, legend = inputs(tmp_path)
    if uncertain_legend:
        legend.entries[0].attributes["row_status"] = "uncertain"
    cfg = Config(
        runs_dir=tmp_path / "runs", llm=LLMConfig(model="fake", anthropic_api_key="unused")
    )

    class NoCalls:
        def __init__(self, *args, **kwargs):
            self.retries_total = 0

        def reset_retry_counter(self):
            pass

        def messages_create(self, **kwargs):
            raise AssertionError("Unexpected model call")

    monkeypatch.setattr(pipeline, "LLMClient", NoCalls)

    def inspect(**kw):
        if kw["run_dir"]:
            atomic_write_json(
                kw["run_dir"] / "evidence" / "page-0000.json", page.model_dump(mode="json")
            )
        return [page], []

    monkeypatch.setattr(pipeline, "_inspect_pages", inspect)
    monkeypatch.setattr(
        "diagex.extractors.pid_legend.resolve_evidence_legend",
        lambda **kw: SimpleNamespace(resolution=SimpleNamespace(pack=legend, source="test")),
    )

    def perceive(**kw):
        assert len(kw["legend_summary"]) == (0 if uncertain_legend else 1)
        if not uncertain_legend:
            assert "image_b64" in kw["legend_summary"][0]
        return (
            [detection],
            {0: "partial" if guard_stop else "ok"},
            {},
            "Repeated invalid responses" if guard_stop else None,
        )

    monkeypatch.setattr(pipeline, "_run_perception", perceive)

    def forbidden(**kw):
        raise AssertionError("Downstream stage called during detection")

    assert not hasattr(pipeline, "fuse_objects")
    opts = dict(
        diagram=source,
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
    result = pipeline.run_symbol_detection(**opts)
    assert result.workflow_stage == "detection"
    assert not hasattr(result, "graph")
    assert result.observation_count == 1
    assert (result.run_dir / "detection.json").is_file()
    assert not (result.run_dir / "graph.json").exists()
    if guard_stop:
        assert result.quality_status == "partial"
        manifest = json.loads((result.run_dir / "checkpoints/manifest.json").read_text())
        assert manifest["status"] == "paused"
        assert manifest["pause_reason"] == "Repeated invalid responses"


def test_tiny_vector_detail_is_rendered_at_readable_resolution(tmp_path):
    from PIL import Image

    store, _, _ = setup_store(tmp_path)
    workbench = Workbench(Config(runs_dir=tmp_path / "runs"))
    # A small symbol needs a higher PDF render scale than a whole-page preview.
    data = workbench.detection_crop(str(store.run_dir), 0, [128, 68, 24, 24])
    with Image.open(io.BytesIO(data)) as image:
        assert min(image.size) >= 1000
        assert max(image.size) <= 1201


def test_bundle_is_read_only_and_candidates_are_not_detections(tmp_path):
    store, source, page = setup_store(tmp_path)
    before = {
        p.relative_to(store.run_dir): p.read_bytes()
        for p in store.run_dir.rglob("*")
        if p.is_file()
    }
    workbench = Workbench(Config(runs_dir=tmp_path / "runs"))
    for _ in range(2):
        state = workbench.detection_store(str(store.run_dir)).public()
        assert state["observation_count"] == 1
        assert state["candidate_count"] == 2
        assert len(state["symbols"]) == 1
        assert "kind" not in state["candidates"][0]["detection"]
        assert store.download("detection") == before[__import__("pathlib").Path("detection.json")]
        assert json.loads(store.download("legend"))["entries"]
        workbench.detection_page(str(store.run_dir), 0)
    after = {
        p.relative_to(store.run_dir): p.read_bytes()
        for p in store.run_dir.rglob("*")
        if p.is_file()
    }
    assert before == after
    assert not (store.run_dir / "review").exists()


def test_source_attachment_checks_hash_and_confinement(tmp_path):
    store, source, _ = setup_store(tmp_path)
    workbench = Workbench(Config(runs_dir=tmp_path / "runs"))
    (store.run_dir / "workbench.json").unlink()
    assert workbench.recent_runs()[0]["source_available"] is False
    with pytest.raises(WorkbenchError, match="Attach"):
        workbench.detection_page(str(store.run_dir), 0)
    for content, valid in [(source.read_bytes() + b"\n% different source\n", False), (source.read_bytes(), True)]:
        upload = workbench.save_upload(
            filename="source.pdf",
            content_type="application/pdf",
            source=io.BytesIO(content),
            length=len(content),
        )
        if valid:
            assert workbench.open_detection(
                run_dir=str(store.run_dir), upload_id=upload.id
            ).startswith("/detections?")
        else:
            with pytest.raises(WorkbenchError, match="source hash"):
                workbench.open_detection(run_dir=str(store.run_dir), upload_id=upload.id)
    assert workbench.recent_runs()[0]["source_verified"] is True
    with pytest.raises(WorkbenchError):
        workbench.detection_store(str(tmp_path))


def test_new_pipeline_does_not_import_removed_subsystems():
    import subprocess
    import sys

    script = "from diagex.extractors.symbol_detection import run_symbol_detection; from diagex.extractors.pid_legend import resolve_evidence_legend; import sys; assert not any(m.startswith(('diagex.review', 'diagex.dexpi', 'diagex.vision.fusion', 'diagex.vision.topology', 'diagex.vision.reconcile')) for m in sys.modules)"
    subprocess.run([sys.executable, "-c", script], check=True)


def test_taxonomy_preserves_prompt_contract():
    from diagex.detection import taxonomy

    expected = {
        "render_equipment_slash_list": "64de52d3a3849e62b154587cf30d9033b6e28e52728273498c8a3b0590f9342a",
        "render_equipment_subtype_hints": "3b61afa2a064709ce3cb6f202a19a2c9d8c416bb591689ec87e79a8b4891994a",
        "render_equipment_subtype_values": "4f60288b8a4e83cfec7ef1ca3ed29904e448ab5472d9665ed0cb1400d887e2f5",
        "render_equipment_taxonomy_enum": "1c452b4c74b99ac59e83110d3808d93b4aab877f2ba611142e1f061907fec738",
        "render_instrument_class_slash_list": "e4326f60ee87237d8add1d3e3b709b34073e328cd59f34295f330a8aa0abc837",
        "render_instrument_function_enum": "0883e28e42a320a2d827269a97dbc867a10a69355fc6c3fd58beee17a9591275",
        "render_instrument_slash_list": "e9c92d61fb19541190b6af2cc456bd763467aa50b4934b75f0383bb442cb8660",
        "render_legend_equipment_list": "737a9c6873c6ea18e26e7ce8b08403cce47a2f07e34b82951474600204340dd2",
        "render_legend_instrument_list": "aff155642964e68699d256c3122c47af8f5f712886176f6d6e0469e1d760ebee",
        "render_legend_valve_list": "95426eb145e4781f91a9878d14d559885d72ea7dab7d5252ac20ed093425292b",
        "render_valve_slash_list": "57da8e788608e2d4adbd38da6a4d40a5f9d3a0a718e4412cda8f77148497b0b2",
        "render_valve_type_enum": "ef0f114e6176dc6e8c43eb595750d9588f9b55221a4b5ff4182121e01b0b7cf1",
    }
    for name, digest in expected.items():
        assert hashlib.sha256(getattr(taxonomy, name)().encode()).hexdigest() == digest


@pytest.mark.parametrize("rotation", [0, 90, 180, 270])
def test_vector_crop_matches_rotated_page_coordinates(tmp_path, rotation):
    from PIL import Image

    from diagex.vision.evidence import extract_page_evidence
    from diagex.vision.loader import iter_pages, load

    source = tmp_path / "rotated.pdf"
    with fitz.open() as document:
        native = document.new_page(width=200, height=100)
        native.draw_rect(fitz.Rect(30, 20, 50, 40), fill=(0, 0, 0))
        native.set_rotation(rotation)
        document.save(source)
    rendered = next(iter_pages(load(source)))
    with fitz.open(source) as document:
        evidence = extract_page_evidence(page=rendered, source_path=source, pdf_page=document[0])
    run = tmp_path / "runs" / "rotated" / "test"
    run.mkdir(parents=True)
    write_detection_bundle(
        run,
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
        pages=[evidence],
        detections=[],
        legend_pack=LegendPack(),
        per_page_status={0: "ok"},
        candidates=[],
        reviews=[],
    )
    atomic_write_json(run / "source.json", {"source_path": str(source)})
    workbench = Workbench(Config(runs_dir=tmp_path / "runs"))
    box = evidence.paths[0].bbox
    data = workbench.detection_crop(str(run), 0, [box.x, box.y, box.w, box.h])
    image = Image.open(io.BytesIO(data)).convert("L")
    assert min(image.size) >= 1000
    assert image.getpixel((image.width // 2, image.height // 2)) < 10


def test_scan_view_uses_exact_processed_frame(tmp_path):
    from PIL import Image, ImageChops, ImageDraw

    from diagex.extractors.symbol_detection import _inspect_pages
    from diagex.ui.progress import NullReporter
    from diagex.vision.loader import iter_pages, load

    source = tmp_path / "scan.png"
    image = Image.new("RGB", (320, 180), "white")
    draw = ImageDraw.Draw(image)
    for y in range(30, 140, 15):
        draw.line((30, y, 280, y + 8), fill="black", width=2)
    image.save(source)
    config = Config(runs_dir=tmp_path / "runs")
    loaded = load(source, tiling=config.tiling, scan_cfg=config.scan)
    expected = next(iter_pages(loaded)).image.convert("RGB")
    run = config.runs_dir / "scan" / "test"
    run.mkdir(parents=True)
    pages, _ = _inspect_pages(
        source=loaded, diagram=source, store=None, run_dir=run, reporter=NullReporter()
    )
    write_detection_bundle(
        run,
        source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
        pages=pages,
        detections=[],
        legend_pack=LegendPack(),
        per_page_status={0: "ok"},
        candidates=[],
        reviews=[],
    )
    atomic_write_json(run / "source.json", {"source_path": str(source)})
    workbench = Workbench(config)
    actual = Image.open(io.BytesIO(workbench.detection_page(str(run), 0))).convert("RGB")
    assert ImageChops.difference(expected, actual).getbbox() is None
    actual_crop = Image.open(
        io.BytesIO(workbench.detection_crop(str(run), 0, [20, 20, 100, 100]))
    ).convert("RGB")
    assert ImageChops.difference(expected.crop((20, 20, 120, 120)), actual_crop).getbbox() is None
