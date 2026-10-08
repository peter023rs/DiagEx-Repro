from __future__ import annotations

import base64
import hashlib
import io
import json
import os
import sqlite3
from types import SimpleNamespace

from PIL import Image, ImageDraw

from diagex.config import Config, LLMConfig
from diagex.symbol_library import (
    augment_legend,
    browse,
    import_project,
    reference_pack,
    symbol_image,
)
from diagex.vision.legend_context import select_legend_context
from diagex.vision.legend_models import LegendEntry, LegendPack


def entry(**kwargs):
    image = Image.new("RGB", (40, 40), "white")
    ImageDraw.Draw(image).ellipse((5, 5, 35, 35), outline="black", width=2)
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    return LegendEntry(label="Project pump", kind="equipment", symbol_class="pump",
                       source="legend_extracted", image_b64=base64.b64encode(buffer.getvalue()).decode(),
                       source_row_id="row-1", source_page_index=0, crop_quality="accepted", **kwargs)


def save_pack(project, entries, *, run="one", document_hash="drawing-hash", modified=1):
    path = project / "runs" / "drawing" / run / "legend.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(LegendPack(source_hash="legend-page-hash", source_ref="drawing#pages=0",
                               entries=entries).model_dump_json())
    (path.parent / "source.json").write_text(json.dumps({"source_sha256": document_hash}))
    os.utime(path, ns=(modified, modified))
    return path


def test_import_is_idempotent_preserves_sources_images_and_variants(tmp_path):
    original = entry()
    first = save_pack(tmp_path, [original])
    save_pack(tmp_path, [original], run="two", modified=2)
    variant = original.model_copy(update={"description": "Alternate interpretation"})
    save_pack(tmp_path, [variant], run="three", modified=3)
    before = first.read_bytes()
    folder = tmp_path / "database"
    assert import_project(tmp_path, folder) == {"symbols": 2, "images": 2, "sources": 3}
    snapshot = browse(folder)
    import_project(tmp_path, folder)
    assert browse(folder) == snapshot
    assert first.read_bytes() == before
    assert len(list((folder / "images").glob("*.png"))) == 1
    assert symbol_image(folder, snapshot["symbols"][0]["id"]) == original.image_bytes()
    assert symbol_image(folder, "../../etc/passwd") is None
    assert all(r["page"] == 1 and r["status"] == "machine_extracted" for r in snapshot["symbols"])


def test_reference_scope_latest_uncertainty_and_current_legend_precedence(tmp_path):
    folder = tmp_path / "database"
    save_pack(tmp_path, [entry()], modified=1)
    import_project(tmp_path, folder)
    assert not reference_pack(folder, document_hash="other-drawing", standard="none").entries
    assert not reference_pack(folder, document_hash="legend-page-hash", standard="none").entries
    refs = reference_pack(folder, document_hash="drawing-hash", standard="none")
    assert len(refs.entries) == 1
    contexts, images, _ = select_legend_context([e.model_dump() for e in refs.entries], [], [])
    assert images and contexts[0]["attributes"]["reference_symbol_id"]
    current = LegendPack(entries=[entry(attributes={"row_status": "uncertain"})])
    assert augment_legend(current, refs).entries == current.entries
    save_pack(tmp_path, current.entries, run="two", modified=2)
    import_project(tmp_path, folder)
    assert not reference_pack(folder, document_hash="drawing-hash", standard="none").entries
    assert not reference_pack(folder, document_hash="drawing-hash", standard="none", include_project=False).entries


def test_standard_catalog_metadata_is_not_detection_evidence(tmp_path):
    folder = tmp_path / "database"
    folder.mkdir()
    catalog = [{"id": "iec-60617", "title": "Official sample", "preview_url": "https://example.org/index",
                "samples": [{"id": "S00952", "name": "Thermocouple", "page": 32}]}]
    (folder / "standards.json").write_text(json.dumps(catalog))
    import_project(tmp_path, folder)
    data = browse(folder)
    assert data["symbols"][0]["status"] == "catalog_only"
    assert data["symbols"][0]["image_path"] is None
    assert not reference_pack(folder, document_hash="any", standard="none").entries


def test_isa_requires_images_and_removes_legacy_records(tmp_path):
    from diagex.extractors.pid_legend import load_builtin_pack

    folder = tmp_path / "database"
    pictured = entry(standard="isa-5.1").model_copy(update={"source": "built_in"})
    text_only = pictured.model_copy(update={"label": "Text-only ISA", "image_b64": None})
    iso = text_only.model_copy(update={"label": "ISO starter", "standard": "iso-10628"})
    save_pack(tmp_path, [pictured, text_only, iso])
    import_project(tmp_path, folder)
    assert {r["name"] for r in browse(folder)["symbols"]} == {pictured.label, iso.label}

    # Simulate an older database that already stored a text-only ISA definition.
    with sqlite3.connect(folder / "symbols.sqlite3") as db:
        db.execute("""INSERT INTO symbols
            SELECT 'legacy-isa', 'Legacy ISA', description, kind, symbol_class, standard,
                   status, scope, 'legacy-row', NULL, entry_json
            FROM symbols WHERE standard='isa-5.1'""")
        db.execute("""INSERT INTO occurrences
            SELECT 'legacy-isa', source_id, 99 FROM occurrences LIMIT 1""")
    assert import_project(tmp_path, folder) == {"symbols": 2, "images": 1, "sources": 1}
    snapshot = browse(folder)
    import_project(tmp_path, folder)
    assert browse(folder) == snapshot
    refs = reference_pack(folder, document_hash="", standard="isa-5.1")
    assert len(refs.entries) == 1 and refs.entries[0].image_b64 == pictured.image_b64
    assert not load_builtin_pack("isa-5.1").entries


def test_detection_receives_references_and_records_changed_content(tmp_path, monkeypatch):
    from diagex.extractors import symbol_detection as pipeline
    from tests.unit.test_detection import inputs

    source, page, detection, _ = inputs(tmp_path)
    digest = hashlib.sha256(source.read_bytes()).hexdigest()
    folder = tmp_path / "database"
    save_pack(tmp_path, [entry()], document_hash=digest)
    import_project(tmp_path, folder)
    cfg = Config(runs_dir=tmp_path / "results", symbol_database_dir=folder,
                 llm=LLMConfig(model="fake", anthropic_api_key="unused"))

    class NoCalls:
        def __init__(self, *args, **kwargs):
            self.retries_total = 0

        def reset_retry_counter(self):
            pass

    monkeypatch.setattr(pipeline, "LLMClient", NoCalls)
    monkeypatch.setattr(pipeline, "_inspect_pages", lambda **kw: ([page], []))
    monkeypatch.setattr("diagex.extractors.pid_legend.resolve_evidence_legend", lambda **kw:
                        SimpleNamespace(resolution=SimpleNamespace(pack=LegendPack(), source="test")))
    contexts = []

    def perceive(**kw):
        contexts.append(kw["legend_summary"])
        return [detection], {0: "ok"}, {}, None

    monkeypatch.setattr(pipeline, "_run_perception", perceive)
    options = dict(diagram=source, symbol_standard="none", legend_path=None, legend_pages=None,
                   legend_region=None, no_legend=False, legend_key=None, effort="medium",
                   config=cfg, persist=True, console=None)
    first = pipeline.run_symbol_detection(**options)
    first_manifest = json.loads((first.run_dir / "checkpoints/manifest.json").read_text())
    assert contexts[-1][0]["attributes"]["reference_status"] == "machine_extracted"
    assert json.loads((first.run_dir / "legend.json").read_text())["entries"][0]["source"] == "reference_database"
    save_pack(tmp_path, [entry(description="Updated definition")], run="new", document_hash=digest, modified=2)
    import_project(tmp_path, folder)
    second = pipeline.run_symbol_detection(**options)
    second_manifest = json.loads((second.run_dir / "checkpoints/manifest.json").read_text())
    assert contexts[-1][0]["description"] == "Updated definition"
    assert first_manifest["stage_versions"]["legend_content"] != second_manifest["stage_versions"]["legend_content"]
    pipeline.run_symbol_detection(**options, fresh=True)
    assert contexts[-1] == []
