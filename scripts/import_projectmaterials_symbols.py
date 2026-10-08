"""Import the supplied ProjectMaterials 416-entry PDF without OCR or model calls.

This is a one-document extractor for its repeated image-card layout. Printed
labels, including truncations and duplicates, are preserved verbatim.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import re
from collections import Counter
from pathlib import Path

import pymupdf

from diagex.symbol_library import import_project
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.vision.models import BBox

COLLECTION = "projectmaterials-pid-symbols"
NON_SYMBOLS = {
    "Imgi 418 Logo", "Logo", "Logo Light", "Page 27@3X", "Table2", "Table3", "Table4",
    "Filters 1", "S For Lines", "Heat Exchangerss 3", "Instrumentation Symbol...",
}


def bounds(rect: pymupdf.Rect) -> BBox:
    return BBox(x=round(rect.x0), y=round(rect.y0), w=round(rect.width), h=round(rect.height))


def classify(name: str, category: str) -> tuple[str, str, dict[str, str]]:
    """Conservative retrieval hints inferred from printed names, not conformance."""
    name = name.casefold()
    if category == "Lines & Signals" or name.startswith("instrument electrical"):
        return "line", "signal_line" if "signal" in name else "line", {}
    if "valve" in name:
        subtype = next((v for v in ("check", "ball", "butterfly", "gate", "globe", "needle", "pinch", "plug", "diaphragm", "control", "safety") if v in name), "other")
        return "valve", subtype, {"valve_type": subtype}
    for tokens, cls in [
        (("compressor",), "compressor"), (("blower", "fan"), "fan"),
        (("pump",), "pump"), (("strainer", "filter"), "filter"),
        (("motor",), "motor"), (("reactor",), "reactor"),
        (("exchanger", "reboiler", "condenser", "cooler"), "heat_exchanger"),
        (("column", "packed tower", "plate tower", "tray column"), "column"),
        (("tank",), "tank"), (("vessel", "drum"), "vessel"),
    ]:
        if any(token in name for token in tokens):
            return "equipment", cls, {"equipment_class": cls}
    if category == "Instrumentation":
        function = next((f for f in ("transmitter", "controller", "indicator", "recorder", "element") if f in name), "other")
        return "instrument", function, {}
    if category in {"Pumps", "Compressors & Blowers", "Heat Exchangers", "Vessels & Tanks", "Motors & Drivers", "Equipment - General", "Strainers & Filters"}:
        return "equipment", "unclassified_equipment", {}
    return "other", "unclassified", {}


def extract_pdf(path: Path) -> tuple[LegendPack, dict]:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    entries, counts, page_counts = [], Counter(), {}
    with pymupdf.open(path) as doc:
        cover = doc[0].get_text()
        if "416 Symbols in 15 Categories" not in cover or "projectmaterials.com" not in cover:
            raise ValueError("This importer expects the ProjectMaterials 416-symbol reference guide")
        for page in list(doc)[2:]:
            lines = [(pymupdf.Rect(line["bbox"]), "".join(span["text"] for span in line["spans"]))
                     for block in page.get_text("dict")["blocks"] if block["type"] == 0
                     for line in block["lines"]]
            categories = [text for rect, text in lines if rect.x0 > 250 and 20 < rect.y0 < 35]
            if len(categories) != 1:
                raise ValueError(f"Ambiguous category on page {page.number + 1}")
            category = categories[0]
            cells = [item["rect"] for item in page.get_drawings()
                     if item["type"] == "fs" and 90 < item["rect"].width < 100
                     and 90 < item["rect"].height < 100]
            images = page.get_image_info(xrefs=True)
            if len(cells) != len(images):
                raise ValueError(f"Unmatched image on page {page.number + 1}")
            page_counts[str(page.number + 1)] = len(cells)
            used_names, used_images = set(), set()
            for index, cell in enumerate(sorted(cells, key=lambda r: (round(r.y0), r.x0))):
                candidates = [im for im in images if cell.contains(pymupdf.Rect(im["bbox"]))]
                labels = [(j, rect, text) for j, (rect, text) in enumerate(lines)
                          if cell.y1 < rect.y0 < cell.y1 + 20
                          and cell.x0 - 8 < (rect.x0 + rect.x1) / 2 < cell.x1 + 8]
                if len(candidates) != 1 or len(labels) != 1:
                    raise ValueError(f"Ambiguous image/label pairing, page {page.number + 1}, cell {index + 1}")
                image, (line_index, label_rect, name) = candidates[0], labels[0]
                if line_index in used_names or image["number"] in used_images:
                    raise ValueError("An image or label was assigned twice")
                used_names.add(line_index)
                used_images.add(image["number"])
                raw = doc.extract_image(image["xref"])
                # MuPDF's decoded image preserves the embedded bitmap dimensions.
                pix = pymupdf.Pixmap(doc, image["xref"])
                if pix.colorspace and pix.colorspace.n != 3:
                    pix = pymupdf.Pixmap(pymupdf.csRGB, pix)
                png = pix.tobytes("png")
                kind, cls, attributes = classify(name, category)
                attributes.update(
                    reference_collection=COLLECTION, source_document=path.name,
                    source_publisher="ProjectMaterials", source_url="https://projectmaterials.com",
                    source_category=category, source_name=name,
                    source_name_truncated=str(name.endswith("...")).lower(),
                    classification_basis="inferred_from_printed_name_and_category",
                    standard_conformance="not_verified", source_image_format=raw["ext"],
                    source_image_dimensions=f"{image['width']}x{image['height']}",
                    source_image_sha256=hashlib.sha256(raw["image"]).hexdigest(),
                    source_pdf_xref=str(image["xref"]),
                    source_pdf_bbox=json.dumps(list(image["bbox"])),
                    source_bbox_units="PDF points (1/72 inch)",
                    extraction_method="embedded_image_and_native_text",
                )
                if name in NON_SYMBOLS:
                    attributes.update(row_status="reject", reference_exclusion="Logo, page artwork, reference table, or annotated explanation; not an isolated P&ID symbol")
                rect = pymupdf.Rect(image["bbox"])
                entries.append(LegendEntry(
                    label=name, description=f"{name}. Printed category: {category}.",
                    kind=kind, symbol_class=cls, source="document_reference", standard=None,
                    image_b64=base64.b64encode(png).decode(), attributes=attributes,
                    source_page_index=page.number, source_bbox=bounds(rect),
                    source_label_bbox=bounds(label_rect),
                    source_row_id=f"{COLLECTION}:p{page.number + 1}:item{index + 1}",
                ))
                counts[category] += 1
        # The contents page supplies the expected category counts independently.
        toc = doc[1].get_text().splitlines()
        expected = {toc[i - 1]: int(re.fullmatch(r"(\d+) symbols", line).group(1))
                    for i, line in enumerate(toc) if re.fullmatch(r"(\d+) symbols", line)}
        if dict(counts) != expected or len(entries) != 416:
            raise ValueError(f"Contents-page counts do not match extracted cards: {dict(counts)}")
    report = {"source_sha256": digest, "entry_count": len(entries), "categories": dict(counts),
              "pages": page_counts, "excluded_non_symbols": sorted(NON_SYMBOLS),
              "excluded_entry_count": sum(e.attributes.get("row_status") == "reject" for e in entries),
              "truncated_names": sum(e.attributes["source_name_truncated"] == "true" for e in entries)}
    return LegendPack(source_hash=digest, source_ref=f"ProjectMaterials | {path.name}", standard="none",
                      entries=entries, notes="Direct embedded-image/native-text extraction; printed labels preserved. Not an official ISA/IEC/ISO standard."), report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("pdf", type=Path)
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--database", type=Path, default=Path("symbol_database"))
    args = parser.parse_args()
    pack, report = extract_pdf(args.pdf)
    target = args.database / "documents" / COLLECTION
    target.mkdir(parents=True, exist_ok=True)
    (target / "pid-symbols.pdf").write_bytes(args.pdf.read_bytes())
    (target / "legend.json").write_text(pack.model_dump_json(indent=2) + "\n")
    (target / "source.json").write_text(json.dumps({"source_path": "pid-symbols.pdf", "source_sha256": report["source_sha256"]}, indent=2) + "\n")
    (target / "import-report.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps({"import": report, "database": import_project(args.project, args.database)}, indent=2))


if __name__ == "__main__":
    main()
