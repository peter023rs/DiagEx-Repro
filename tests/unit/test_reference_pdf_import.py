from __future__ import annotations

import io
import json
from pathlib import Path

import pytest
from PIL import Image

from diagex.symbol_library import augment_legend, browse, import_project, reference_pack
from diagex.vision.legend_context import select_legend_context
from diagex.vision.legend_models import LegendEntry, LegendPack

PDF = Path(__file__).resolve().parents[2] / "symbol_database/documents/projectmaterials-pid-symbols/pid-symbols.pdf"
pytestmark = pytest.mark.skipif(
    not PDF.is_file(), reason="The user-supplied reference PDF is outside the package distribution"
)


def test_reference_guide_pairs_all_cards_and_retains_source_names():
    from scripts.import_projectmaterials_symbols import extract_pdf

    pack, report = extract_pdf(PDF)
    assert len(pack.entries) == report["entry_count"] == 416
    assert len(report["categories"]) == 15
    assert report["truncated_names"] == 58
    assert report["excluded_entry_count"] == 12
    assert len({e.source_row_id for e in pack.entries}) == 416
    first = pack.entries[0]
    assert first.label == "Blind No" and first.source_page_index == 2
    valve = next(e for e in pack.entries if e.label == "Ball Valve")
    assert valve.source_page_index == 4 and valve.kind == "valve"
    assert valve.standard is None and valve.source == "document_reference"
    assert len([e for e in pack.entries if e.label == "Axial Compressor"]) == 2
    for entry in pack.entries:
        with Image.open(io.BytesIO(entry.image_bytes())) as image:
            assert f"{image.width}x{image.height}" == entry.attributes["source_image_dimensions"]
        assert entry.attributes["source_bbox_units"] == "PDF points (1/72 inch)"


def test_document_references_are_global_but_do_not_override_drawing_legends(tmp_path):
    from scripts.import_projectmaterials_symbols import COLLECTION, extract_pdf

    pack, _ = extract_pdf(PDF)
    folder = tmp_path / "database"
    target = folder / "documents" / COLLECTION
    target.mkdir(parents=True)
    (target / "legend.json").write_text(pack.model_dump_json())
    (target / "source.json").write_text(json.dumps({"source_sha256": pack.source_hash}))
    assert import_project(tmp_path, folder)["symbols"] == 416
    before = browse(folder)
    assert import_project(tmp_path, folder)["symbols"] == 416
    assert browse(folder) == before
    refs = reference_pack(folder, document_hash="unrelated-drawing", standard="isa-5.1", include_project=False)
    assert len(refs.entries) == 404
    assert not any(e.attributes.get("reference_exclusion") for e in refs.entries)
    assert not reference_pack(folder, document_hash="unrelated-drawing", standard="none").entries
    current = LegendEntry(label="Ball Valve", symbol_class="other", kind="valve",
                          source="legend_extracted", attributes={"row_status": "uncertain"})
    merged = augment_legend(LegendPack(entries=[current]), refs)
    assert [e for e in merged.entries if e.label == "Ball Valve"] == [current]
    valve = next(e for e in refs.entries if e.label == "Ball Valve")
    context, images, _ = select_legend_context([valve.model_dump()], [], ["ball valve"])
    assert images and context[0]["attributes"]["reference_status"] == "document_reference"
    assert context[0]["attributes"]["source_document"] == "pid-symbols.pdf"
