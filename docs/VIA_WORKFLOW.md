# VIA — ground-truth authoring workflow (informational)

This document is **informational only**. The annotations shipped under
`eval/datasets/` are post-correction final truth — reviewers do not need
to run VIA, render bootstraps, or re-author anything to reproduce results.

It exists to document how the partial-truth `annotations.truth.jsonl` files
in `eval/datasets/<stem>/` were produced, in case a re-grader wants to
audit the rater↔model agreement evidence (`graph.truth.history.json`) or
extend the corpus with a new fixture.

The full toolchain (VIA editor binaries, rendered authoring-DPI PNGs,
bootstrap-seeding scripts, project-conversion scripts) is **not** in this
archive — it is in the source repo (`tools/via/`, `scripts/render_pages.py`,
`scripts/bootstrap_annotations.py`, `scripts/annotations_to_via.py`,
`scripts/via_to_annotations.py`, `scripts/via_to_bootstrap_v2.py`) but is
not part of the reproducibility surface for the paper.

## The flow that produced the shipped truth

1. **Render** authoring-DPI PNGs from each PDF.
2. **Bootstrap** an `annotations.truth.jsonl` from a clean Phase-2 run on
   that fixture, seeding draft bboxes.
3. **Correct** in VIA — the human rater reviews every drafted region
   (move / resize / delete / add / edit). Every kept entity is therefore
   human-verified; the corresponding `graph.truth.history.json` records
   each individual edit (this is the "we did not grade our own homework"
   evidence cited in §4.3 of `paper/evaluation-plan.md`).
4. **Round-trip** the corrected VIA project back to JSONL. This emits both
   `annotations.truth.jsonl` (authoritative) and a regenerated
   `graph.truth.json` for fixtures with full-graph annotation level.
5. **Measure retention** with `scripts/measure_retention.py`, which
   produces `eval/datasets/_retention.v0.2.json`. The paper's
   retention numbers come from this file.

## Two DPIs

The pipeline renders pages at one DPI for inference, and a higher DPI for
human authoring. The mapping lives in `tools/via/images/dpis.json`
(scale = `authoring_dpi / pipeline_dpi`) so coordinates round-trip cleanly
between the agent's frame and the rater's frame.

## What is in this archive

- `data/two_tanks_hires.png` — the only authoring-DPI PNG kept here, used in
  the manuscript (§10 step 12 of `paper/evaluation-plan.md` describes the
  authoring-DPI illustration in detail).
- `eval/datasets/<stem>/graph.truth.history.json` — append-only audit
  log per fixture.

If you need any other VIA artefact, it is in the source repository.
