"""Upload-to-results regression with the real detector and a limited provider."""

import io
import json
import time
from types import SimpleNamespace

import anthropic
import fitz
import httpx
import pytest
from PIL import Image, ImageDraw

from diagex.config import Config, LLMConfig
from diagex.llm.client import LLMClient
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.web.server import Workbench
from tests.unit.test_legend_context import definition


@pytest.mark.parametrize("source_type", ["png", "pdf", "multipage_pdf", "legend_pdf"])
def test_scan_upload_completes_with_four_image_provider(tmp_path, monkeypatch, source_type):
    pack = LegendPack(entries=[
        LegendEntry.model_validate(definition("round_symbol", i)) for i in range(11)
    ])
    if source_type != "legend_pdf":
        monkeypatch.setattr(
            "diagex.extractors.pid_legend.resolve_evidence_legend",
            lambda **kw: SimpleNamespace(resolution=SimpleNamespace(pack=pack, source="test")),
        )
    monkeypatch.setattr("diagex.extractors.symbol_detection.reference_pack", lambda *a, **kw: LegendPack())
    counts = []
    legend_rows_seen = []

    class Stream:
        def __init__(self, tool_name, tool_input):
            self.tool_name, self.tool_input = tool_name, tool_input

        def __enter__(self):
            return self

        def __exit__(self, *args):
            pass

        def __iter__(self):
            return iter(())

        def get_final_message(self):
            return SimpleNamespace(content=[{
                "type": "tool_use", "name": self.tool_name, "input": self.tool_input,
            }], usage=SimpleNamespace(input_tokens=100, output_tokens=20))

    def stream(**kwargs):
        count = sum(b.get("type") == "image" for m in kwargs["messages"] for b in m["content"])
        counts.append(count)
        if count > 4:
            message = f"DeepInfra: Too many images in request: {count} > 4"
            raise anthropic.BadRequestError(message, response=httpx.Response(
                400, request=httpx.Request("POST", "https://openrouter.ai/api/v1/messages"),
            ), body={"error": {"message": message}})
        tool_name = kwargs["tools"][0]["name"]
        if tool_name == "submit_legend_rows":
            rows = [json.loads(b["text"]) for b in kwargs["messages"][0]["content"] if b["type"] == "text"]
            legend_rows_seen.extend(row["row_id"] for row in rows)
            return Stream(tool_name, {"rows": [{"row_id": row["row_id"], "decision": "accept",
                "kind": "instrument", "symbol_class": "unclassified_instrument",
                "candidate_shapes": ["round_symbol"]} for row in rows]})
        assert tool_name == "submit_pid_objects"
        return Stream(tool_name, {"objects": [{"kind": "instrument", "label": "PT-1",
            "bbox": {"x": 0.4, "y": 0.4, "w": 0.1, "h": 0.1}, "confidence": "high"}]})

    monkeypatch.setattr(LLMClient, "_build_client", staticmethod(
        lambda config: SimpleNamespace(messages=SimpleNamespace(stream=stream))
    ))
    config = Config(runs_dir=tmp_path / "runs", llm=LLMConfig(
        transport="openrouter", model="xiaomi/mimo-v2.6-pro", openrouter_api_key="test",
    ))
    workbench = Workbench(config, storage_dir=tmp_path / "web")
    image = Image.new("RGB", (600, 400), "white")
    ImageDraw.Draw(image).ellipse((240, 160, 300, 200), outline="black", width=3)
    payload = io.BytesIO()
    image.save(payload, format="PNG")
    drawing = payload.getvalue()
    if source_type != "png":
        with fitz.open() as document:
            if source_type == "legend_pdf":
                legend = document.new_page(width=600, height=800)
                legend.insert_text((20, 20), "Symbol legend")
                for i in range(12):
                    y = 50 + i * 55
                    legend.draw_rect(fitz.Rect(100, y, 130, y + 30))
                    legend.insert_text((150, y + 20), f"Instrument reference {i}")
            if source_type == "multipage_pdf":
                cover = document.new_page(width=600, height=400)
                cover.insert_text((20, 20), "Cover sheet")
            scan = document.new_page(width=600, height=400)
            scan.insert_image(scan.rect, stream=drawing)
            drawing = document.tobytes()
    filename, mime = ("scan.png", "image/png") if source_type == "png" else ("scan.pdf", "application/pdf")
    upload = workbench.save_upload(filename=filename, content_type=mime,
                                   source=io.BytesIO(drawing), length=len(drawing))
    job = workbench.start_extraction({"upload_id": upload.id, "model_policy": "evaluation",
                                      "provider": "openrouter", "vision_model": config.llm.model,
                                      "reasoning_mode": "disabled", "fresh": True})
    deadline = time.monotonic() + 10
    while job.status not in {"succeeded", "failed", "paused"} and time.monotonic() < deadline:
        time.sleep(0.01)
    try:
        assert job.status == "succeeded", job.error or job.result
        assert job.result["stats"]["observation_count"] > 0
        assert counts and max(counts) <= 4
        if source_type == "legend_pdf":
            assert len(legend_rows_seen) == len(set(legend_rows_seen)) == 12
    finally:
        workbench.close()
