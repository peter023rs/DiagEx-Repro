# diagex — reproducibility package

This repository is the public reproducibility package for the manuscript

> **DiagEx: Zero-Shot P&ID-to-DEXPI Digitization with a Vision-Language Agent**
> Heiko Koziolek, Thilo Braun, Tabea Bordis
> ABB Corporate Research Center, Mannheim, Germany
> *Manuscript under review — venue and DOI to be added on acceptance.*

It contains:

- The diagex Python package (`code/diagex/`) that performs the extraction.
- The evaluation harness (`code/eval/`) used to produce every number in the
  paper.
- Ground-truth corpora (`data/ground_truth/`) for the 10 public P&IDs the paper
  evaluates against.
- The 10 source PDFs (`data/pdfs/`).
- Final results CSVs, tables, and figures (`results/`) for Phase 1, Phase 2,
  the no-tile ablation, and the GPT-4.1 baseline.
- Replay cassettes (`cassettes/`) so reviewers can re-derive results without
  an Anthropic API key.
- The unreviewed manuscript PDF (`paper/manuscript.pdf`) and the design-time
  evaluation plan (`paper/evaluation-plan.md`).

Per-run agent transcripts, tile crops, intermediate DEXPI JSON, and full
debug reports live in the **separate Zenodo supplementary archive** linked
from `.zenodo.json` (cross-DOI). They are not in this repository because
they are large (~150–250 MB) and not needed to verify any number.

## Quick start (no API key required)

```bash
git clone <REPLACE_WITH_REPO_URL> diagex-repro && cd diagex-repro
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .

# Run the unit suite (validates eval logic + DEXPI 2.0 round-trip).
pytest tests/unit/

# Re-derive Phase 1 results from cassettes.
python code/eval/run_paper_eval.py \
    --fixtures data/ground_truth/manifest.yaml \
    --phase 1 --conditions baseline --use-cassettes \
    --out /tmp/repro
diff /tmp/repro/results.csv results/phase1/results.csv
```

If the diff is empty, your environment reproduces the published Phase 1
numbers byte-for-byte. See `docs/REPRODUCE.md` for the equivalent commands
for Phase 2, the ablation, and the GPT-4.1 baseline.

## Live mode

To re-run the agent against the real PDFs (Anthropic API key required):

```bash
export ANTHROPIC_API_KEY=...
python code/eval/run_paper_eval.py --conditions baseline --phase 1 --out /tmp/live
```

Live results are non-deterministic; expect ±0.02 macro-F1 around the
published numbers per the evaluation plan §8.1.

## Layout

```
code/        diagex source, eval harness, scripts
data/        PDFs + ground-truth corpora
results/     Final CSVs, tables, figures, reports
cassettes/   Replay artefacts for offline re-derivation
tests/unit/  Unit tests (eval harness + DEXPI 2.0 layer)
docs/        Reproduction runbook, data card, architecture sketch
paper/       The manuscript PDF
```

A full file-by-file map lives in `docs/REPRODUCE.md` (which paper number
maps to which CSV row to which command).

## Licensing

- diagex source: Apache-2.0 (see `LICENSE`).
- DEXPI 2.0 specification sources, vendored under
  `code/diagex/dexpi/codegen/vendored/`: CC-BY 4.0 (DEXPI Initiative; see
  `NOTICE` and `code/diagex/dexpi/codegen/vendored/PROVENANCE.md`).
- All other third-party code: their original licenses, listed in `NOTICE`.

## Citing

See `CITATION.cff` (GitHub renders it as a "Cite this repository" widget).

## Limitations

- Reproduction needs Python 3.11+ on Linux/macOS. The `[codegen]` extra
  (which requires Python 3.12+ and `dexpi.specificator==1.0.0`) is **not**
  required to reproduce results — the DEXPI 2.0 model is checked in under
  `code/diagex/dexpi/_generated/`.
- The 10-fixture corpus is the public subset; private customer P&IDs that
  appear in some paper figures are not redistributable and are not in this
  archive.
- Live-mode reproduction depends on Anthropic API availability and current
  pricing of `claude-opus-4-7`. Cassette mode is fully offline.
