"""Portable SQLite symbol references with original PNGs and source provenance.

Import explicitly with ``python -m diagex.symbol_library --project .``.
Detection and the web browser only read the resulting database.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import io
import json
import sqlite3
from contextlib import closing
from pathlib import Path

from PIL import Image

from diagex.vision.legend_models import LegendEntry, LegendPack

SCHEMA = """
PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS sources (
 id TEXT PRIMARY KEY, path TEXT NOT NULL, sha256 TEXT NOT NULL,
 document_sha256 TEXT NOT NULL, source_ref TEXT NOT NULL,
 modified_ns INTEGER NOT NULL, legend_hash TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS symbols (
 id TEXT PRIMARY KEY, name TEXT NOT NULL, description TEXT NOT NULL,
 kind TEXT NOT NULL, symbol_class TEXT NOT NULL, standard TEXT NOT NULL,
 status TEXT NOT NULL, scope TEXT NOT NULL, row_key TEXT NOT NULL,
 image_path TEXT, entry_json TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS occurrences (
 symbol_id TEXT NOT NULL REFERENCES symbols(id),
 source_id TEXT NOT NULL REFERENCES sources(id), entry_index INTEGER NOT NULL,
 PRIMARY KEY (source_id, entry_index)
);
CREATE INDEX IF NOT EXISTS symbols_scope ON symbols(scope);
CREATE TABLE IF NOT EXISTS standards (
 id TEXT PRIMARY KEY, metadata_json TEXT NOT NULL
);
PRAGMA user_version=1;
"""


def _json(value) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def _hash(value: str | bytes) -> str:
    return hashlib.sha256(value.encode() if isinstance(value, str) else value).hexdigest()


def _connect(folder: Path, *, write=False) -> sqlite3.Connection:
    path = folder / "symbols.sqlite3"
    connection = sqlite3.connect(path if write else f"{path.resolve().as_uri()}?mode=ro", uri=not write)
    connection.row_factory = sqlite3.Row
    return connection


def import_pack(connection, folder: Path, path: Path, project: Path) -> None:
    """Keep every observation; deduplicate identical content, never by name alone."""
    raw = path.read_bytes()
    pack = LegendPack.model_validate_json(raw)
    relative = path.relative_to(project).as_posix()
    document_hash = ""
    source_file = path.parent / "source.json"
    if source_file.is_file():
        document_hash = json.loads(source_file.read_text()).get("source_sha256", "")
    source_id = _hash(relative + _hash(raw))
    connection.execute(
        "INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?)",
        (source_id, relative, _hash(raw), document_hash, pack.source_ref,
         path.stat().st_mtime_ns, pack.source_hash),
    )
    for index, entry in enumerate(pack.entries):
        # Imported fallback entries in a saved run are references, not new legend evidence.
        if entry.source == "reference_database":
            continue
        standard = entry.standard or (pack.standard if entry.source == "built_in" else "")
        # Historical runs still contain the removed text-only ISA starter pack.
        if standard == "isa-5.1" and not entry.image_b64:
            continue
        payload = entry.model_dump(mode="json")
        encoded = payload.pop("image_b64")
        image_path = None
        if encoded:
            image_bytes = base64.b64decode(encoded, validate=True)
            with Image.open(io.BytesIO(image_bytes)) as im:
                if im.format != "PNG":
                    raise ValueError(f"Expected PNG in {relative}, entry {index}")
                im.verify()
            image_path = f"images/{_hash(image_bytes)}.png"
            target = folder / image_path
            if not target.exists():
                target.write_bytes(image_bytes)
        scope = (f"standard:{entry.standard or pack.standard}" if entry.source == "built_in"
                 else f"legend:{pack.source_hash or source_id}")
        if entry.source == "document_reference":
            scope = f"document:{pack.source_hash or source_id}"
        row_key = entry.source_row_id or _hash(_json([
            entry.label, entry.source_page_index,
            entry.source_bbox.model_dump() if entry.source_bbox else None,
        ]))
        status = ("unverified_starter" if entry.source == "built_in" else "machine_extracted")
        if entry.source == "document_reference":
            status = "document_reference"
        if entry.source == "customer_override":
            status = "customer_override"
        if entry.attributes.get("row_status") in {"uncertain", "reject"}:
            status = entry.attributes["row_status"]
        symbol_id = _hash(_json([scope, payload, image_path]))
        connection.execute(
            "INSERT OR IGNORE INTO symbols VALUES (?,?,?,?,?,?,?,?,?,?,?)",
            (symbol_id, entry.label, entry.description or "", entry.kind,
             entry.symbol_class, entry.standard or "", status, scope, row_key,
             image_path, _json(payload)),
        )
        connection.execute("INSERT OR IGNORE INTO occurrences VALUES (?,?,?)",
                           (symbol_id, source_id, index))


def import_project(project: Path, folder: Path) -> dict:
    project, folder = project.resolve(), folder.resolve()
    folder.mkdir(parents=True, exist_ok=True)
    (folder / "images").mkdir(exist_ok=True)
    packs = set((project / "src/diagex/assets/symbols").glob("*.json"))
    packs.update((folder / "documents").glob("*/legend.json"))
    for root in (project / "runs", project / "legends"):
        if root.exists():
            for path in root.rglob("*.json"):
                if root.name == "legends" or path.name in {"legend.json", "legend.cache.json"}:
                    packs.add(path)
    with closing(_connect(folder, write=True)) as db, db:
        db.executescript(SCHEMA)
        for path in sorted(packs):
            import_pack(db, folder, path, project)
        catalog = folder / "standards.json"
        if catalog.is_file():
            for standard in json.loads(catalog.read_text()):
                db.execute("INSERT OR REPLACE INTO standards VALUES (?,?)",
                           (standard["id"], _json(standard)))
                for sample in standard.get("samples", []):
                    source_id = _hash(standard["preview_url"])
                    db.execute("INSERT OR IGNORE INTO sources VALUES (?,?,?,?,?,?,?)",
                               (source_id, standard["preview_url"], "", "", standard["title"], 0, ""))
                    symbol_id = _hash(_json([standard["id"], sample]))
                    entry = {"source_page_index": sample["page"] - 1,
                             "attributes": {"standard_symbol_id": sample["id"],
                                            "image_status": "image_unavailable"}}
                    db.execute("INSERT OR IGNORE INTO symbols VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                               (symbol_id, sample["name"], sample["id"], "other", "",
                                standard["id"], "catalog_only", f"catalog:{standard['id']}",
                                sample["id"], None, _json(entry)))
                    db.execute("INSERT OR IGNORE INTO occurrences VALUES (?,?,?)",
                               (symbol_id, source_id, int(sample["id"][1:])))
        # Apply the image requirement to databases created before this policy too.
        imageless_isa = """SELECT id FROM symbols
            WHERE (standard='isa-5.1' OR scope='standard:isa-5.1')
              AND (image_path IS NULL OR image_path='')"""
        db.execute(f"DELETE FROM occurrences WHERE symbol_id IN ({imageless_isa})")
        db.execute(f"DELETE FROM symbols WHERE id IN ({imageless_isa})")
        db.execute("""DELETE FROM sources WHERE source_ref='built-in:isa-5.1'
                      AND NOT EXISTS (SELECT 1 FROM occurrences WHERE source_id=sources.id)""")
    result = browse(folder)
    # A readable export sits beside the portable SQLite database and original crops.
    (folder / "catalog.json").write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    return result["summary"]


def browse(folder: Path | None) -> dict:
    if folder is None or not (folder / "symbols.sqlite3").is_file():
        return {"symbols": [], "standards": [], "summary": {"symbols": 0, "images": 0, "sources": 0}}
    with closing(_connect(folder)) as db:
        rows = [dict(row) for row in db.execute("SELECT * FROM symbols ORDER BY name, id")]
        sources = {}
        for row in db.execute("""SELECT o.symbol_id, s.* FROM occurrences o
                                  JOIN sources s ON s.id=o.source_id ORDER BY s.path"""):
            item = dict(row)
            sources.setdefault(item.pop("symbol_id"), []).append(item)
        for row in rows:
            entry = json.loads(row.pop("entry_json"))
            row["page"] = (entry.get("source_page_index") + 1
                           if entry.get("source_page_index") is not None else None)
            row["bbox"] = entry.get("source_bbox")
            row["crop_quality"] = entry.get("crop_quality")
            row["attributes"] = entry.get("attributes", {})
            row["sources"] = sources.get(row["id"], [])
        return {
            "symbols": rows,
            "standards": [json.loads(r[0]) for r in db.execute("SELECT metadata_json FROM standards ORDER BY id")],
            "summary": {"symbols": len(rows), "images": sum(bool(r["image_path"]) for r in rows),
                        "sources": db.execute("SELECT COUNT(*) FROM sources").fetchone()[0]},
        }


def symbol_image(folder: Path | None, symbol_id: str) -> bytes | None:
    if folder is None or not (folder / "symbols.sqlite3").is_file():
        return None
    with closing(_connect(folder)) as db:
        row = db.execute("SELECT image_path FROM symbols WHERE id=?", (symbol_id,)).fetchone()
    if not row or not row[0]:
        return None
    path = (folder / row[0]).resolve()
    if path.parent != (folder / "images").resolve():
        raise ValueError("Invalid symbol image path")
    return path.read_bytes()


def reference_pack(folder: Path | None, *, document_hash: str, standard: str,
                   include_project=True) -> LegendPack:
    """Latest observation per source row; no cross-drawing project assumptions."""
    result = LegendPack(standard=standard, source_ref="reference-database")
    if folder is None or not (folder / "symbols.sqlite3").is_file():
        return result
    with closing(_connect(folder)) as db:
        # A pack hash is a hash of legend page bytes, NOT the complete source PDF.
        # Only source.json's document hash establishes same-drawing applicability.
        rows = db.execute("""
            SELECT * FROM (
              SELECT y.*, s.path, s.source_ref, s.document_sha256,
                ROW_NUMBER() OVER (PARTITION BY y.scope,y.row_key
                  ORDER BY s.modified_ns DESC,s.path DESC,y.id) AS revision
              FROM symbols y JOIN occurrences o ON o.symbol_id=y.id
              JOIN sources s ON s.id=o.source_id
              WHERE y.scope=? OR (? AND y.scope LIKE 'document:%')
                              OR (? AND s.document_sha256=? AND s.document_sha256!=''
                                  AND y.scope LIKE 'legend:%')
            ) WHERE revision=1 ORDER BY scope,row_key
        """, (f"standard:{standard}", standard != "none", include_project, document_hash)).fetchall()
    for row in rows:
        if row["status"] in {"uncertain", "reject"}:
            continue
        entry = json.loads(row["entry_json"])
        if str(entry.get("crop_quality") or "").startswith("rejected"):
            continue
        if row["image_path"]:
            entry["image_b64"] = base64.b64encode(symbol_image(folder, row["id"])).decode()
        entry["source"] = "reference_database"
        entry["attributes"].update(
            reference_symbol_id=row["id"], reference_status=row["status"],
            reference_source=row["path"], reference_source_ref=row["source_ref"],
            reference_scope=row["scope"],
        )
        result.entries.append(LegendEntry.model_validate(entry))
    return result


def augment_legend(pack: LegendPack, references: LegendPack) -> LegendPack:
    """Live source rows (even uncertain ones) block stale database fallbacks."""
    current = [e for e in pack.entries if e.source != "built_in"]
    labels = {e.label.strip().casefold() for e in current}
    row_ids = {e.source_row_id for e in current if e.source_row_id}
    additions = [e for e in references.entries
                 if e.label.strip().casefold() not in labels
                 and (not e.source_row_id or e.source_row_id not in row_ids)]
    project_labels = {e.label.strip().casefold() for e in additions
                      if e.attributes.get("reference_scope", "").startswith("legend:")}
    additions = [e for e in additions
                 if not e.attributes.get("reference_scope", "").startswith("standard:")
                 or e.label.strip().casefold() not in project_labels]
    reference_labels = {e.label.strip().casefold() for e in additions}
    builtins = [e for e in pack.entries if e.source == "built_in"
                and e.label.strip().casefold() not in reference_labels]
    return pack.model_copy(update={"entries": [*current, *additions, *builtins]})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project", type=Path, default=Path("."))
    parser.add_argument("--database", type=Path, default=Path("symbol_database"))
    args = parser.parse_args()
    print(json.dumps(import_project(args.project, args.database), indent=2))


if __name__ == "__main__":
    main()
