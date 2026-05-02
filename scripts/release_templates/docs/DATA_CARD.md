# Data card — diagex evaluation corpus

This card documents the 10 public P&IDs the manuscript evaluates against.
The authoritative manifest lives at `eval/datasets/manifest.yaml`
(filename retained from the source repo for compatibility with code that
reads it; the corpus is not venue-specific)
and pins per-fixture metadata (page size, source pipeline, annotation level,
domain tag, notable flags). This document is the human-readable companion.

## Corpus version

`dataset_version: diagex.v0.2` — same string emitted in every results CSV
row in `results/phase{1,2}/results.csv`. If you regenerate the corpus from
`scripts/measure_retention.py` you should see retention numbers
matching `eval/datasets/_retention.v0.2.json`.

## Provenance

All 10 PDFs are sourced from publicly redistributable material. Per-PDF
provenance lives next to each fixture in `eval/datasets/<stem>/meta.yaml`
under the `provenance` key (URL, license, author, year). The manifest's
`source_type` field distinguishes vector PDFs (clean text) from raster PDFs
(scanned or rasterised exports).

| stem                | source_type | domain               | annotation_level |
|---------------------|-------------|----------------------|------------------|
| dexpi-reference     | vector      | dexpi-synthetic      | full             |
| two-tanks           | raster      | process-utility      | partial          |
| butane1             | raster      | c4-cracking          | full             |
| butane2             | raster      | c4-cracking          | partial          |
| open100-1..4        | raster      | open-process-100     | partial          |
| grit-washer1        | raster      | water-treatment      | partial          |
| tennessee1          | raster      | tennessee-eastman    | partial          |

## Ground-truth artefacts (per fixture)

Every fixture under `eval/datasets/<stem>/` ships:

- `graph.truth.json` — DEXPI-2.0-aligned ground graph (equipment, valves,
  instruments, segments, OPCs, piping network systems). Authoritative for
  Phase 2.
- `annotations.truth.jsonl` — bounding-box-level ground truth per visual
  symbol. Used by partial-truth Phase 2 scoring.
- `queries.truth.yaml` — the 4 NL queries per fixture (Phase 1) plus their
  expected answers and grader configs (`set_match`, `numeric_tolerance`,
  etc.).
- `meta.yaml` — provenance, source pipeline, annotation level, source type,
  domain tag, contamination notes (whether the PDF appears in any public
  dataset that may have leaked into LLM training data).
- `graph.truth.history.json` — append-only audit log of every
  rater↔model-arbitrated edit since bootstrap. Cited as agreement evidence
  in §4.3 of `paper/evaluation-plan.md`; do not rewrite by hand.
- `graph.truth.svg` — visual rendering of `graph.truth.json` for quick eyeball
  checks.

## Annotation level

The `annotation_level` field on each fixture is one of:

- **`full`** — every load-bearing visual symbol in the diagram is annotated;
  Phase 2 graph metrics use the full graph truth.
- **`partial`** — only a subset of visual symbols is annotated (typically
  enough to anchor the equipment + 1-hop piping). Phase 2 metrics on these
  fixtures use the annotations-only fallback in `eval/scoring.py`.

This split is the reason `eval/scoring.py` switches between graph-level F1
and annotations-only F1 on a per-fixture basis.

## Contamination posture

The DEXPI reference P&ID (`dexpi-reference`) is the public DEXPI 2.0
canonical sample and may appear, in some form, in LLM training corpora — its
score should not be averaged into headline numbers without acknowledging
this. The `notable_flags` field flags this with `canonical_reference_exists`.
Other fixtures are either novel re-illustrations (open-process-100 series,
grit-washer1) or come from less-indexed sources (tennessee1, butane1/2);
contamination risk is harder to quantify but is discussed in §2 of
`paper/evaluation-plan.md`.

## License

Per-PDF: see each fixture's `meta.yaml`. Most are public-domain or CC-BY;
the corpus is redistributable as a whole under those original terms.

The ground-truth annotations themselves (graph, jsonl, yaml) are released
under **Apache-2.0** alongside diagex.
