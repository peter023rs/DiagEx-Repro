"""Machine bundles. Reading and exporting never writes to a run."""

from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path

from diagex.extractors.evidence_checkpoint import atomic_write_json
from diagex.vision.legend_models import LegendPack
from diagex.vision.perception import DetectionRecord


def write_detection_bundle(
    run_dir, *, source_hash, pages, detections, legend_pack, per_page_status, candidates, reviews
):
    atomic_write_json(
        run_dir / "detection.json",
        {
            "version": 1,
            "source_sha256": source_hash,
            "pages": [
                {"page_index": p.page_index, "width": p.width, "height": p.height, "role": p.role}
                for p in pages
            ],
            "detections": [d.model_dump(mode="json") for d in detections],
            "legend_pack": legend_pack.model_dump(mode="json"),
            "per_page_status": per_page_status,
            "candidates": candidates,
            "reviews": reviews,
        },
    )


class DetectionStore:
    def __init__(self, run_dir: Path):
        self.run_dir = run_dir
        self.raw = (run_dir / "detection.json").read_bytes()
        self.bundle = json.loads(self.raw)
        if self.bundle.get("version") != 1:
            raise ValueError("Unsupported detection bundle version")
        pages = self.bundle.get("pages", [])
        indices = set()
        for page in pages:
            index = page["page_index"]
            if not isinstance(index, int) or index < 0 or index in indices:
                raise ValueError("Invalid detection page index")
            indices.add(index)
            if page["width"] <= 0 or page["height"] <= 0:
                raise ValueError("Invalid detection page dimensions")
        for detection in self.bundle.get("detections", []):
            DetectionRecord.model_validate(detection)
            if detection["page_index"] not in indices:
                raise ValueError("Detection references an unknown page")
        LegendPack.model_validate(self.bundle["legend_pack"])

    def _metadata(self, path: Path) -> dict:
        if not path.resolve().is_relative_to(self.run_dir.resolve()):
            raise ValueError("Artifact is outside its run directory")
        if not path.exists():
            return {}
        value = json.loads(path.read_text())
        if not isinstance(value, dict):
            raise ValueError("Invalid run metadata")
        return value

    def public(self):
        bundle = deepcopy(self.bundle)
        diagnostics = bundle.get("reviews", [])
        symbols = [
            {
                "id": "detection-" + str(i),
                "detection": d,
                "origin": "detected",
                "status": d.get("confidence", "unknown"),
                "reason": "",
            }
            for i, d in enumerate(bundle.get("detections", []))
        ]
        candidates = []
        for i, candidate in enumerate(bundle.get("candidates", [])):
            decisions = [
                r
                for r in diagnostics
                if r.get("candidate_id") == candidate["id"]
                and r.get("page_index") == candidate["page_index"]
            ]
            candidates.append(
                {
                    "id": f"candidate-{i}",
                    "detection": candidate,
                    "origin": "native_candidate",
                    "status": decisions[-1].get("status", "uncertain")
                    if decisions
                    else "uncertain",
                    "reason": "; ".join(str(r.get("reason", "")) for r in decisions),
                    "diagnostics": decisions,
                }
            )
        for i, diagnostic in enumerate(diagnostics):
            candidates.append(
                {
                    "id": f"diagnostic-{i}",
                    "detection": {
                        **(diagnostic.get("object") or {}),
                        "page_index": diagnostic.get("page_index"),
                        "tile_id": diagnostic.get("tile_id"),
                        "bbox": diagnostic.get("bbox"),
                        "id": diagnostic.get("candidate_id", f"diagnostic-{i}"),
                    },
                    "origin": "diagnostic",
                    "status": diagnostic.get("status", "uncertain"),
                    "reason": diagnostic.get("reason", ""),
                    "diagnostics": [diagnostic],
                }
            )
        text_rows = []
        for page in bundle["pages"]:
            index = page["page_index"]
            evidence = self._metadata(self.run_dir / "evidence" / f"page-{index + 1:04d}.json")
            for i, span in enumerate(evidence.get("text_spans", [])):
                text_rows.append(
                    {
                        "id": f"text-{index}-{i}",
                        "origin": "native_text",
                        "status": "complete",
                        "detection": {**span, "page_index": index, "label": span.get("text", "")},
                        "reason": "",
                    }
                )
        result = self._metadata(self.run_dir / "result.json")
        status = "paused" if result.get("stop_reason") else result.get("quality_status")
        if status in {None, "needs_review", "ok"}:
            status = (
                "partial"
                if any(v != "ok" for v in bundle.get("per_page_status", {}).values())
                else "complete"
            )
        return {
            **bundle,
            "symbols": symbols,
            "texts": text_rows,
            "candidates": candidates,
            "legends": [
                {
                    "id": f"legend-{i}",
                    "entry": e,
                    "status": e.get("attributes", {}).get("row_status", "complete"),
                }
                for i, e in enumerate(bundle["legend_pack"]["entries"])
            ],
            "status": status,
            "stop_reason": result.get("stop_reason"),
            "observation_count": len(symbols),
            "candidate_count": len(bundle.get("candidates", [])),
            "diagnostic_count": len(diagnostics),
        }

    def download(self, kind: str) -> bytes:
        if kind == "detection":
            return self.raw
        if kind == "legend":
            return json.dumps(self.bundle["legend_pack"], ensure_ascii=False, indent=2).encode()
        raise ValueError("Download kind must be detection or legend")
