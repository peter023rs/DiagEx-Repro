"""Browser smoke test with a synthetic P&ID; never contacts an extraction model.

Requires Node, playwright (via NODE_PATH if necessary), and CHROME_PATH.
Run from the repository root: .venv/bin/python tests/browser/run_detection_smoke.py
"""

import argparse
import hashlib
import subprocess
import tempfile
import threading
from http.server import ThreadingHTTPServer
from pathlib import Path

import fitz

from diagex.config import Config, LLMConfig
from diagex.detection.artifacts import write_detection_bundle
from diagex.detection.result import DetectionResult
from diagex.extractors.evidence_checkpoint import atomic_write_json
from diagex.vision.evidence import PageEvidence
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.vision.models import BBox
from diagex.vision.perception import DetectionRecord
from diagex.web.server import Workbench, make_handler


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, default=Path("output/detection-smoke"))
    args = parser.parse_args()
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        source = root / "synthetic.pdf"
        with fitz.open() as document:
            p = document.new_page(width=600, height=423.8)
            p.draw_circle((325, 205), 5)
            p.insert_text((330, 205), "Legend symbol")
            p.insert_text((80, 100), "PT: Pressure transmitter")
            p = document.new_page(width=600, height=423.8)
            p.draw_rect(fitz.Rect(300, 180, 335, 260))
            p.draw_circle((453.5, 293.5), 3.5)
            p.draw_line((420, 293.5), (450, 293.5))
            p.draw_line((457, 293.5), (490, 293.5))
            document.save(source)
        pages = [
            PageEvidence(
                page_index=i,
                source_ref="synthetic",
                width=6000,
                height=4238,
                dpi=720,
                effective_dpi=720,
                is_scanned=False,
                role="legend" if i == 0 else "pid",
            )
            for i in range(2)
        ]
        detections = [
            DetectionRecord(
                id=did,
                page_index=1,
                tile_id="t1",
                kind=kind,
                label=label,
                bbox=BBox(**bbox),
                confidence="high",
                attributes=attributes,
            )
            for did, kind, label, bbox, attributes in [
                (
                    "d1",
                    "equipment",
                    "V-001",
                    {"x": 3000, "y": 1800, "w": 350, "h": 800},
                    {"equipment_class": "vessel"},
                ),
                (
                    "d2",
                    "instrument",
                    "PT-002",
                    {"x": 4500, "y": 2900, "w": 70, "h": 70},
                    {"instrument_function": "transmitter"},
                ),
            ]
        ]
        pack = LegendPack(
            entries=[
                LegendEntry(
                    label="Drawing glyph",
                    symbol_class="instrument",
                    kind="instrument",
                    source="legend_extracted",
                    source_page_index=0,
                    source_bbox=BBox(x=3200, y=2000, w=100, h=100),
                ),
                LegendEntry(
                    label="PT",
                    symbol_class="abbreviation",
                    source="legend_extracted",
                    source_page_index=0,
                    source_bbox=BBox(x=800, y=900, w=150, h=100),
                    crop_quality="omitted_abbreviation",
                ),
                LegendEntry(
                    label="Library reference",
                    symbol_class="valve",
                    kind="equipment",
                    source="built_in",
                ),
            ]
        )
        run = root / "runs" / "drawing" / "run-ui-test"
        run.mkdir(parents=True)
        write_detection_bundle(
            run,
            source_hash=hashlib.sha256(source.read_bytes()).hexdigest(),
            pages=pages,
            detections=detections,
            legend_pack=pack,
            per_page_status={0: "ok", 1: "ok"},
            reviews=[{
                "page_index": 1, "tile_id": "t1", "status": "uncertain",
                "bbox": {"x": 2000, "y": 1200, "w": 90, "h": 60},
                "object": {"kind": "raster_symbol", "confidence": "high", "attributes": {
                    "broad_category": "arrow", "requires_legend_interpretation": True,
                    "geometry_basis": "vlm_broad_raster_observation",
                }},
                "reason": "Broad raster observation; detailed legend interpretation required",
                "legend_interpretation": {"symbol_id": "symbol-0", "decision": "non_node",
                    "reason": "Flow arrow; retain as direction evidence", "legend_entry_ids": []},
            }],
            candidates=[
                {"id": "c3", "page_index": 1, "bbox": {"x": 1000, "y": 1200, "w": 70, "h": 70}}
            ],
        )
        atomic_write_json(run / "workbench.json", {"source_path": str(source)})
        captured = []
        def runner(**kwargs):
            captured.append(kwargs)
            return DetectionResult(diagram_stem="drawing", run_id="test", model="fake", effort="medium", run_dir=run, observation_count=2, candidate_count=1, legend_entry_count=3)

        config = Config(
            runs_dir=root / "runs",
            llm=LLMConfig(transport="openrouter", model="test/model", openrouter_api_key="test"),
        )
        config.pid.engine = "evidence-v2"
        workbench = Workbench(config, runner=runner)
        path = "/"
        server = ThreadingHTTPServer(("127.0.0.1", 0), make_handler(workbench))
        threading.Thread(target=server.serve_forever, daemon=True).start()
        output = args.out
        output.mkdir(parents=True, exist_ok=True)
        before = (run / "detection.json").read_bytes()
        try:
            subprocess.run(
                [
                    "node",
                    str(Path(__file__).with_name("detection_smoke.cjs")),
                    f"http://127.0.0.1:{server.server_port}{path}",
                    str((output / "chinese-detection-results.png").resolve()),
                    str(source.resolve()),
                ],
                check=True,
                timeout=120,
            )
            assert len(captured) == 1
            assert captured[0]["config"].llm.vision_model == "test/vision"
            assert captured[0]["config"].llm.escalation_model == "test/reinspection"
            assert captured[0]["config"].llm.openrouter_provider_order == ["xiaomi"]
            assert captured[0]["config"].llm.openrouter_provider_ignore == ["deepinfra"]
            assert captured[0]["config"].llm.openrouter_allow_fallbacks is False
            assert (run / "detection.json").read_bytes() == before
            assert not (run / "review").exists()
        finally:
            server.shutdown()
            server.server_close()
            workbench.close()


if __name__ == "__main__":
    main()
