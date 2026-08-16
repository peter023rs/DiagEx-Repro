# diagex — reproducibility package

This repository is the public reproducibility package for the manuscript

> **DiagEx: Zero-Shot P&ID-to-DEXPI Digitization with a Vision-Language Agent**
> Heiko Koziolek, Thilo Braun, Tabea Bordis
> ABB Corporate Research Center, Mannheim, Germany
> *Manuscript under review — venue and DOI to be added on acceptance.*

It contains:

- The diagex Python package (`src/diagex/`) that performs the extraction.
- The evaluation harness (`eval/`) used to produce every number in the
  paper.
- Ground-truth corpora (`eval/datasets/`) for the 10 public P&IDs the paper
  evaluates against.
- The 10 source PDFs (`tests/p-ids-public/`).
- Final results CSVs, tables, and figures (`results/`) for Phase 1, Phase 2,
  the no-tile ablation, and the GPT-4.1 baseline.
- Replay cassettes (`eval/cassettes/`) so reviewers can re-derive results without
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
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
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
python eval/run_paper_eval.py --conditions baseline --phase 1 --out /tmp/live
```

OpenRouter is supported through its Anthropic Messages-compatible endpoint:

```bash
export DIAGEX_LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=...
export DIAGEX_MODEL=provider/model-slug
# auto follows --effort; enabled/disabled force all model calls
export DIAGEX_REASONING=auto

diagex extract-pid path/to/drawing.pdf --effort medium
```

Choose a model that supports both image input and tool calling. `OPENROUTER_MODEL`
is accepted as an alias for `DIAGEX_MODEL`. Optional attribution settings are
`OPENROUTER_HTTP_REFERER` and `OPENROUTER_APP_TITLE`.

`DIAGEX_REASONING` accepts `auto`, `enabled`, or `disabled` (`on`/`off` and
`true`/`false` are aliases). `auto` retains the existing effort-based behavior;
the other values globally force reasoning or non-reasoning for page extraction,
legend work, edge cleanup, and arbitration.

Kimi Code K3 is also supported with the Kimi Code Console key:

```bash
export DIAGEX_LLM_PROVIDER=kimi
export KIMI_API_KEY=...
export KIMI_BASE_URL=https://api.kimi.com/coding/v1
export DIAGEX_MODEL=k3

diagex extract-pid path/to/drawing.pdf --effort medium
```

DiagEx accepts Kimi's OpenAI-style `/coding/v1` setting above, but uses Kimi's
Anthropic-compatible `/coding/v1/messages` endpoint internally so image and tool
blocks do not need conversion. `KIMI_MODEL` is accepted as a model-name alias.

New run directories include the sanitized model name after the timestamp, for
example `runs/2401/2026-08-16T10-30-00_qwen-qwen3.7-flash_r-ab12/`.

Live results are non-deterministic; expect ±0.02 macro-F1 around the
published numbers per the evaluation plan §8.1.

## Human review workbench

Review an extraction beside its original PDF in a local browser:

```bash
diagex review runs/<drawing>/<run-id> \
  --pdf path/to/drawing.pdf \
  --rater "Reviewer name"
```

The left pane preserves the source page and the right pane shows editable,
source-aligned entities and connections. Every action is autosaved under the
run's `review/` directory, so Ctrl+C is safe and the same command resumes the
session. Final export remains disabled until every page, entity, connection,
and extraction conflict has an explicit disposition. Completion writes
`graph.reviewed.json`, `pid.reviewed.dexpi.json`,
`pid.reviewed.dexpi.xml`, and `review.report.json` without changing the
original `graph.json`.

## Layout

```
src/diagex/         diagex Python package (the extractor)
eval/               evaluation harness, ground-truth corpora, replay cassettes
  ├─ *.py           harness modules
  ├─ datasets/      ground-truth corpora (manifest + per-fixture truth)
  └─ cassettes/     offline replay artefacts (no API key needed)
scripts/            operational scripts (rendering, rescoring, build)
tests/
  ├─ unit/          eval-harness + DEXPI 2.0 layer unit tests
  ├─ fixtures/      shared test fixtures (DEXPI 2.0 reference XML)
  └─ p-ids-public/  the 10 public source PDFs
results/            final CSVs, tables, figures, reports
docs/               reproduction runbook, data card, architecture sketch
paper/              the manuscript PDF + evaluation plan
data/               supporting illustration assets (e.g. two_tanks_hires.png)
```

A full file-by-file map lives in `docs/REPRODUCE.md` (which paper number
maps to which CSV row to which command).

## Licensing

- diagex source: Apache-2.0 (see `LICENSE`).
- DEXPI 2.0 specification sources, vendored under
  `src/diagex/dexpi/codegen/vendored/`: CC-BY 4.0 (DEXPI Initiative; see
  `NOTICE` and `src/diagex/dexpi/codegen/vendored/PROVENANCE.md`).
- All other third-party code: their original licenses, listed in `NOTICE`.

## Citing

See `CITATION.cff` (GitHub renders it as a "Cite this repository" widget).

## Limitations

- Reproduction needs Python 3.11+ on Linux/macOS. The `[codegen]` extra
  (which requires Python 3.12+ and `dexpi.specificator==1.0.0`) is **not**
  required to reproduce results — the DEXPI 2.0 model is checked in under
  `src/diagex/dexpi/_generated/`.
- The 10-fixture corpus is the public subset; private customer P&IDs that
  appear in some paper figures are not redistributable and are not in this
  archive.
- Live-mode reproduction depends on Anthropic API availability and current
  pricing of `claude-opus-4-7`. Cassette mode is fully offline.
