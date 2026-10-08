# Symbol reference database

Open http://127.0.0.1:8765/symbols while DiagEx is running.

- `symbols.sqlite3`: portable SQLite database with `symbols`, `sources`, `occurrences`, and `standards` tables.
- `images/`: original PNG legend crops, addressed by SHA-256.
- `catalog.json`: readable export with names, image paths, sources, page numbers, crop bounds, classifications, and verification status.
- `standards.json`: publisher references, editions, coverage limitations, and eight official IEC index samples.
- `documents/projectmaterials-pid-symbols/`: the supplied `pid-symbols.pdf`, extracted legend pack, source hash, and import report.

## ProjectMaterials reference guide

The supplied 30-page `pid-symbols.pdf` contributes 416 image/name records across 15 categories. Images are extracted from embedded bitmaps at their original dimensions, not re-rendered or traced. Names are taken directly from native PDF text; 58 printed truncations are preserved and flagged. Duplicate names retain separate page/cell identities. Twelve logos, page-artwork images, reference tables, and annotated explanations are retained for provenance but marked `reject` and excluded from detection references.

These are third-party document references, not certified ISA/IEC/ISO definitions or human-verified ground truth. Printed categories and inferred retrieval classes are stored separately. Exact PDF image bounds are recorded in `source_pdf_bbox`, in PDF points; original PNGs are stored in `images/`.

Re-extract this specific document layout with:

```sh
.venv/bin/python scripts/import_projectmaterials_symbols.py symbol_database/documents/projectmaterials-pid-symbols/pid-symbols.pdf
```

The ordinary import command below also refreshes saved packs in `documents/*/legend.json`. Imported general reference guides are available across drawings, below current source legends. Selecting **Project legend only** disables them. They remain available during fresh runs because they are reference material, not previous detection results.

Import or refresh all saved project legend packs and bundled starter packs:

```sh
.venv/bin/python -m diagex.symbol_library --project . --database symbol_database
```

The import covers every `legend.json` and `legend.cache.json` under `runs/`, every pack under `legends/`, and `src/diagex/assets/symbols/*.json`. It makes no model calls. It does not perform fresh extraction of unprocessed PDFs. Identical content is deduplicated; every source occurrence and distinct historical interpretation remains traceable. It does not edit existing run artifacts. Re-importing unchanged files is idempotent.

This is a reference collection, not a verified ground-truth benchmark. `machine_extracted` means the stored machine interpretation; `unverified_starter` means the existing ISO/SAMA starter material. ISA entries without images have been removed, including the bundled text-only fallback. Imports skip them in historical runs and remove any previously imported copies. `uncertain` and `reject` records remain visible but do not guide detection. Customer overrides retain their explicit status. An accepted crop or machine row is not human verification.

The ISO starter standard labels are inherited claims, not proof of conformance to an edition. ISA is registered as a publisher reference with zero imported symbols until source images are available. IEC rows contain exact official index names and IDs only, have no image, and are excluded from detection. ISO 14617 is registered as a source with zero imported symbols. A complete ISA/IEC/ISO graphics collection still requires authoritative source artwork. See [source research](../docs/SYMBOL_REFERENCE_SOURCES.md).

## Detection

Choose **Symbol reference standard** in the workbench, or pass `--symbol-standard isa-5.1|iso-10628|sama|none` to `diagex detect`. IEC metadata is browse-only until actual source graphics are available.

Both web and batch detection read this folder by default. Set `DIAGEX_SYMBOL_DATABASE` to an absolute path to use another location. If the database is absent, existing detection still works with its original legend packs.

Current source legend entries take precedence, including uncertain entries that must not be replaced by an older confident interpretation. Database project references apply only when an imported run's `source.json` records the same full drawing SHA-256. The legend-page hash is never mistaken for a drawing hash. For each source row the latest imported artifact observation is considered, ordered by its original modification time; conflicting historical interpretations remain in the database for inspection. Artifacts without a drawing hash are searchable but cannot supply project references.

Fresh runs and `--no-legend` skip stored project references. Standard starter references are restricted to the selected standard. No references from unrelated drawings are automatically applied. Reference IDs, source paths, and status accompany model context and saved legend entries. Existing content hashing invalidates perception checkpoints when the actual supplied references change. The database is read-only during detection and browsing; rerun the import command to include later saved legends.

Keep the whole folder together when copying it. Source paths in import history refer to the original project and do not need to exist to view saved crops. Source page numbers shown in the browser/export are one-based; crop bounds use the original extraction pixel coordinates.
