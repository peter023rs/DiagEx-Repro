from __future__ import annotations

import hashlib
import http.client
import io
import json
import threading
import time
from http.server import ThreadingHTTPServer
from pathlib import Path
from types import SimpleNamespace

import fitz
import pytest

from diagex.config import Config, LLMConfig
from diagex.vision.models import ReconciledGraph
from diagex.web.server import Workbench, WorkbenchError, make_handler


def _config(tmp_path: Path) -> Config:
    config = Config(
        llm=LLMConfig(
            transport="openrouter",
            model="configured/model",
            vision_model="configured/vision",
            reasoning_model="configured/reasoner",
            openrouter_api_key="environment-secret",
        )
    )
    config.runs_dir = tmp_path / "runs"
    config.pid.engine = "evidence-v2"
    return config


def _pdf_bytes() -> bytes:
    document = fitz.open()
    page = document.new_page(width=160, height=100)
    page.insert_text((15, 20), "P&ID TEST")
    payload = document.tobytes()
    document.close()
    return payload


def test_web_default_and_request_use_glm_in_every_role(tmp_path: Path) -> None:
    from diagex.llm.model_policy import apply_production_profile
    from diagex.web.model_profiles import VISION_MODELS

    original = apply_production_profile(_config(tmp_path))
    workbench = Workbench(original, storage_dir=tmp_path / "web")
    public = workbench.public_config()
    assert public["model_policy"] == "glm"
    assert public["vision_model"] == public["reasoning_model"] == VISION_MODELS["glm"]
    cfg, settings = workbench._config_for_request(
        {
            "model_policy": public["model_policy"],
        }
    )
    assert {
        cfg.llm.model,
        cfg.llm.vision_model,
        cfg.llm.reasoning_model,
        cfg.llm.escalation_model,
    } == {VISION_MODELS["glm"]}
    assert cfg.llm.production_open_weight is False
    assert cfg.llm.transport == "openrouter"
    assert cfg.symbol_perception.workflow == "fixed"
    assert settings["model_policy"] == "glm"
    assert original.llm.production_open_weight is True


@pytest.mark.parametrize("preset", ["glm", "mimo", "kimi", "qwen_vl", "deepseek-flash", "production-open-weight", "evaluation"])
@pytest.mark.parametrize("reasoning", ["", "custom/reinspection"])
def test_explicit_openrouter_models_override_presets(tmp_path, preset, reasoning):
    workbench = Workbench(_config(tmp_path), storage_dir=tmp_path / "web")
    cfg, settings = workbench._config_for_request({
        "model_policy": preset, "provider": "openrouter", "vision_model": "custom/vision",
        "reasoning_model": reasoning,
    })
    assert cfg.llm.vision_model == cfg.llm.model == "custom/vision"
    assert cfg.llm.reasoning_model == cfg.llm.escalation_model == (reasoning or "custom/vision")
    assert cfg.llm.production_open_weight is False
    assert settings["model_policy"] == "evaluation"


def test_web_qwen_is_opt_in_and_custom_does_not_inherit_it(tmp_path: Path) -> None:
    from diagex.llm.model_policy import ESCALATION_MODEL, FAST_MODEL, apply_production_profile

    workbench = Workbench(apply_production_profile(_config(tmp_path)), storage_dir=tmp_path / "web")
    qwen, _ = workbench._config_for_request({"model_policy": "production-open-weight"})
    assert qwen.llm.production_open_weight is True
    assert qwen.llm.vision_model == FAST_MODEL
    assert qwen.llm.escalation_model == ESCALATION_MODEL
    assert qwen.llm.reasoning_model == ESCALATION_MODEL
    custom, _ = workbench._config_for_request(
        {
            "model_policy": "evaluation",
            "vision_model": "custom/vision",
            "reasoning_model": "custom/reasoning",
        }
    )
    assert custom.llm.vision_model == "custom/vision"
    assert custom.llm.reasoning_model == custom.llm.escalation_model == "custom/reasoning"
    assert custom.llm.production_open_weight is False


def _wait_for_job(workbench: Workbench, job_id: str) -> object:
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        job = workbench.job(job_id)
        if job.status in {"succeeded", "failed"}:
            return job
        time.sleep(0.01)
    raise AssertionError("background extraction did not finish")


def test_config_is_redacted_and_upload_is_safely_named(tmp_path: Path) -> None:
    workbench = Workbench(_config(tmp_path), storage_dir=tmp_path / "web")

    public = workbench.public_config()
    assert public["configured_keys"]["openrouter"] is True
    assert "environment-secret" not in json.dumps(public)

    payload = _pdf_bytes()
    upload = workbench.save_upload(
        filename="../../unsafe drawing.pdf",
        content_type="application/pdf",
        source=io.BytesIO(payload),
        length=len(payload),
    )

    assert upload.filename == "unsafe_drawing.pdf"
    assert upload.path.parent == (tmp_path / "web" / "uploads" / upload.id)
    assert upload.path.name == "unsafe_drawing.pdf"
    assert upload.path.read_bytes() == payload


def test_fresh_extraction_uses_memory_key_and_persists_only_redacted_settings(
    tmp_path: Path,
) -> None:
    captured: dict[str, object] = {}
    run_dir = tmp_path / "runs" / "drawing" / "run-1"

    def fake_runner(**kwargs: object) -> object:
        captured.update(kwargs)
        run_dir.mkdir(parents=True)
        graph = ReconciledGraph(source_path="drawing.pdf")
        (run_dir / "graph.json").write_text(graph.model_dump_json(), encoding="utf-8")
        return SimpleNamespace(
            diagram_stem="drawing",
            run_id="r-test",
            engine="evidence-v2",
            model="vision=test/vision; reasoning=test/reasoner",
            effort="high",
            quality_status="partial",
            run_dir=run_dir,
            observation_count=5,
            candidate_count=2,
            dexpi_stats={"equipment_count": 2, "instrument_count": 3},
            dexpi_issues=["review"],
            validation_issues=[],
            legend_source="cache_hit",
            legend_entry_count=10,
            cost_summary={"total_tokens": 1234, "wall_clock_s": 2.5, "retries": 1},
        )

    workbench = Workbench(_config(tmp_path), storage_dir=tmp_path / "web", runner=fake_runner)
    payload = _pdf_bytes()
    upload = workbench.save_upload(
        filename="drawing.pdf",
        content_type="application/pdf",
        source=io.BytesIO(payload),
        length=len(payload),
    )
    job = workbench.start_extraction(
        {
            "upload_id": upload.id,
            "provider": "openrouter",
            "api_key": "one-run-secret",
            "base_url": "https://openrouter.ai/api",
            "vision_model": "test/vision",
            "reasoning_model": "test/reasoner",
            "reasoning_mode": "enabled",
            "effort": "high",
            "engine": "evidence-v2",
            "fresh": True,
        }
    )
    finished = _wait_for_job(workbench, job.id)

    assert finished.status == "succeeded"
    assert captured["fresh"] is True
    request_config = captured["config"]
    assert request_config.llm.openrouter_api_key == "one-run-secret"
    public_job = finished.public()
    assert "one-run-secret" not in json.dumps(public_job)
    manifest = json.loads((run_dir / "workbench.json").read_text(encoding="utf-8"))
    assert manifest["settings"]["fresh"] is True
    assert "one-run-secret" not in json.dumps(manifest)


@pytest.mark.parametrize(
    "payload",
    [
        {"engine": "legacy"},
        {"stop_after": "graph"},
        {"reviewed_run": "run"},
        {"draft": True},
        {"raster_proposals": {}},
    ],
)
def test_graph_and_experimental_payloads_are_rejected(tmp_path, payload):
    workbench = Workbench(_config(tmp_path))
    with pytest.raises(WorkbenchError, match="Only"):
        workbench.start_extraction(payload)


def test_http_upload_job_view_and_download(tmp_path):
    from urllib.parse import urlencode

    from diagex.detection.artifacts import write_detection_bundle
    from diagex.detection.result import DetectionResult
    from diagex.vision.evidence import PageEvidence
    from diagex.vision.legend_models import LegendPack

    source = Path("tests/p-ids-public/two-tanks.pdf").read_bytes()
    run = tmp_path / "runs" / "two-tanks" / "test-run"
    captured = []

    def runner(**kwargs):
        captured.append(kwargs)
        run.mkdir(parents=True)
        page = PageEvidence(
            page_index=0,
            source_ref="two-tanks",
            width=160,
            height=100,
            dpi=72,
            effective_dpi=72,
            is_scanned=False,
            role="pid",
        )
        write_detection_bundle(
            run,
            source_hash=hashlib.sha256(source).hexdigest(),
            pages=[page],
            detections=[],
            legend_pack=LegendPack(),
            per_page_status={0: "ok"},
            candidates=[],
            reviews=[],
        )
        return DetectionResult(diagram_stem="two-tanks", model="fake", effort="medium", run_dir=run)

    workbench = Workbench(_config(tmp_path), runner=runner)
    server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(workbench))
    threading.Thread(target=server.serve_forever, daemon=True).start()
    conn = http.client.HTTPConnection("127.0.0.1", server.server_port, timeout=10)

    def request(method, path, body=None):
        conn.request(
            method,
            path,
            body if isinstance(body, bytes) else json.dumps(body) if body is not None else None,
            {"Content-Type": "application/json"},
        )
        response = conn.getresponse()
        return response.status, response.read()

    try:
        status, body = request("GET", "/")
        assert status == 200 and b'id="startButton"' in body and b'id="reviewButton"' not in body
        status, body = request("POST", "/api/uploads?filename=two-tanks.pdf", source)
        assert status == 201
        upload_id = json.loads(body)["upload"]["id"]
        status, body = request(
            "POST", "/api/extractions", {"upload_id": upload_id, "vision_model": "fake", "symbol_standard": "iso-10628"}
        )
        assert status == 202
        job = _wait_for_job(workbench, json.loads(body)["job"]["id"])
        assert job.status == "succeeded", job.error
        assert captured[0]["config"].pid.engine == "evidence-v2"
        assert captured[0]["symbol_standard"] == "iso-10628"
        assert "reviewed_inputs" not in captured[0]
        before = (run / "detection.json").read_bytes()
        query = urlencode({"run_dir": str(run)})
        for path in (
            "/detections?",
            "/api/detections?",
            "/api/detection-download?kind=detection&",
            "/api/detection-download?kind=legend&",
            "/api/detection-page?",
        ):
            status, body = request("GET", path + query)
            assert status == 200, body
            if "kind=detection" in path:
                assert body == before
        for path in ("/api/reviews", "/api/detection-review/actions"):
            assert request("POST", path, {})[0] == 404
        assert (
            request("POST", "/api/extractions", {"upload_id": upload_id, "stop_after": "graph"})[0]
            == 400
        )
        assert request("GET", "/api/detection-download?kind=../../.env&" + query)[0] == 400
        assert request("GET", "/api/detection-crop?box=-1,0,10,10&" + query)[0] == 400
        assert (run / "detection.json").read_bytes() == before
        assert not (run / "review").exists()
        assert len(captured) == 1
    finally:
        conn.close()
        server.shutdown()
        server.server_close()
        workbench.close()


@pytest.mark.parametrize(
    "filename,data", [("bad.pdf", b"not PDF"), ("bad.png", b"not PNG"), ("empty.pdf", b"")]
)
def test_invalid_upload_does_not_start_a_job_or_leave_a_file(tmp_path, filename, data):
    workbench = Workbench(_config(tmp_path))
    with pytest.raises(WorkbenchError):
        workbench.save_upload(
            filename=filename,
            content_type="application/octet-stream",
            source=io.BytesIO(data),
            length=len(data),
        )
    assert not workbench.jobs
    assert list(workbench.uploads_dir.iterdir()) == []
