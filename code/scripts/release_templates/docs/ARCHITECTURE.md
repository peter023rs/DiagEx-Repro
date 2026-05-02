# diagex pipeline — short architecture sketch

This sketch is intentionally short; §III of the manuscript is the
authoritative description. The aim here is to orient a reader who wants to
trace a single number back to its code path.

## Pipeline shape

```
PDF ──▶ pymupdf rasteriser ──▶ overview tile + grid tiles
                                       │
                                       ▼
                          Claude Opus 4.7 (vision + tool use)
                                ┌──────┴───────┐
                                │              │
                          get_overview     get_tile / annotate / lookup_symbol
                                │              │
                                └──────┬───────┘
                                       ▼
                            ReconciledGraph (Python)
                                       │
                  ┌────────────────────┴─────────────────────┐
                  ▼                                          ▼
        DEXPI 2.0 builder                          Phase-1 NL answer
        (extractors/dexpi_builder.py)              (extractors/query.py)
                  │
                  ▼
        diagex.dexpi.json_io ──▶ pid.pydexpi.json
        diagex.dexpi.xml_io  ──▶ pid.dexpi.xml
        extractors/dexpi_svg ──▶ pid.svg
        extractors/dexpi_drawio ──▶ pid.drawio
```

Two design rules are load-bearing:

1. **The agent does not see all tiles at once.** It calls `get_overview`
   first, then asks for specific tiles or regions on demand. That keeps
   image-token cost bounded and is essential to the cost claim in the paper.
2. **Reconciliation is deterministic, non-LLM Python.** The LLM does
   perception (annotate calls); plain Python does dedup, line-stitching, tag
   arbitration. LLM-based ambiguity arbitration (`vision/arbitrate.py`) is a
   bounded secondary pass, not the primary graph builder.

## Where the DEXPI 2.0 layer lives

`code/diagex/dexpi/` is the diagex-native DEXPI 2.0 model. It replaces the
formerly-used pyDEXPI package (AGPL-3.0) and is responsible for the project
shipping under Apache-2.0. Subpackages:

- `_generated/` — pydantic v2 classes derived from the DEXPI 2.0 spec.
  Checked-in so reviewers do not need the codegen extra. CI guards this
  tree against drift.
- `codegen/vendored/` — the upstream DEXPI 2.0 spec sources (CC-BY 4.0,
  attributed in `NOTICE` and `vendored/PROVENANCE.md`).
- `codegen/{regenerate,pydantic_emit}.py` — the derivation pipeline. Opt-in
  Python 3.12+ extra.
- `json_io.py`, `xml_io.py` — DEXPI 2.0 wire formats.
- `extensions.py` — diagex-internal additions (control intent, custom-attr
  hints) that ride on top of the pure DEXPI types.
- `validate.py` — semantic checks beyond the schema.

## Where the eval harness lives

`code/eval/` orchestrates the paper:

- `run_paper_eval.py` — driver. Reads the manifest, dispatches per-fixture
  jobs to the extractor, scores them, and writes `results.csv`.
- `conditions.py` — the four condition recipes (baseline, ablation-no-tile,
  gpt41-singleshot, plus a no-op cassette condition).
- `scoring.py` — graph-level and annotations-only metrics.
- `aggregate.py` + `latex_tables.py` + `figures/` — per-fixture roll-up,
  paper tables, paper figures.
- `report_md.py` — human-readable per-run report.
- `_loader.py` — the canonical fixture loader. Used by both the harness and
  the regression tests, so the on-disk format is single-sourced.

## Why no classical CV

The paper's thesis is that pure LLM vision plus deterministic reconciliation
can replace specialised CV pipelines (YOLO, Hough, per-customer trained
detectors). Adding OpenCV or a trained symbol model would invalidate that
thesis. If you find yourself wanting to add one, the right move is to file
that as a follow-up paper, not to mix it into this codebase.

For more detail, see §III–IV of the manuscript.
