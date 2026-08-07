# Reproduction runbook

This document gives the exact commands that produced every published number,
table, and figure in the paper. All commands are run from the repository root
after `pip install -e .` succeeded.

Two reproduction paths are supported. **Cassette mode** replays recorded LLM
responses and is byte-deterministic — use it to verify the published numbers
without an Anthropic API key. **Live mode** calls the real Claude API; results
match the published numbers within ±0.02 macro-F1 (non-determinism is
discussed in §8.1 of `paper/evaluation-plan.md`).

## 0. Prerequisites

- Python 3.11+ (the runtime). The optional `[codegen]` extra (used only to
  regenerate `src/diagex/dexpi/_generated/`) requires Python 3.12+ and is
  **not** needed for reproduction — the generated DEXPI 2.0 model ships
  checked in.
- ~1 GB free disk for cassette-mode reproduction. Live mode requires
  outbound HTTPS to `api.anthropic.com`.
- For Live mode of the GPT-4.1 baseline you also need
  `OPENAI_API_KEY`.

```bash
python3.11 -m venv .venv && source .venv/bin/activate
pip install -e .
pytest tests/unit/        # validates eval harness + DEXPI 2.0 layer
```

## 1. Phase 1 — natural-language queries (Table 2, Fig. 2)

Cassette mode (no API key):

```bash
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
    --phase 1 --conditions baseline \
    --use-cassettes \
    --out /tmp/repro/phase1
diff /tmp/repro/phase1/results.csv results/phase1/results.csv     # expect empty
diff /tmp/repro/phase1/tables/table2.tex results/phase1/tables/table2.tex
```

Live mode:

```bash
export ANTHROPIC_API_KEY=...
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
    --phase 1 --conditions baseline --out /tmp/live/phase1
```

To use OpenRouter instead, select a model that supports both images and tools:

```bash
export DIAGEX_LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY=...
export DIAGEX_MODEL=provider/model-slug
```

DiagEx uses OpenRouter's Anthropic Messages-compatible endpoint so its native
image, tool-use, prompt-caching, and thinking blocks do not require conversion.
`OPENROUTER_MODEL` may be used instead of `DIAGEX_MODEL`; the latter takes
precedence when both are set.

For Kimi Code K3, use a key created in the Kimi Code Console:

```bash
export DIAGEX_LLM_PROVIDER=kimi
export KIMI_API_KEY=...
export KIMI_BASE_URL=https://api.kimi.com/coding/v1
export DIAGEX_MODEL=k3
```

Although this accepts Kimi's commonly published OpenAI-style base URL, DiagEx
normalizes it to the Anthropic-compatible base and calls `/coding/v1/messages`.
This keeps the existing image, tool-use, and thinking-block request format.

## 2. Phase 2 — P&ID → DEXPI 2.0 (Table 3, Fig. 3)

Cassette mode:

```bash
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
    --phase 2 --conditions baseline \
    --use-cassettes \
    --out /tmp/repro/phase2
diff /tmp/repro/phase2/results.csv results/phase2/results.csv
```

Live mode is significantly more expensive (~$5–7 per fixture); we recommend
running it only on a subset first:

```bash
python eval/run_paper_eval.py --phase 2 --conditions baseline \
    --only two-tanks,dexpi-reference --out /tmp/live/phase2-smoke
```

## 3. Ablation — `--no-tile` (Table 4, §VI.B of the paper)

```bash
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
    --phase 2 --conditions ablation-no-tile \
    --use-cassettes \
    --out /tmp/repro/ablation
diff /tmp/repro/ablation/results.csv results/ablation/results.csv
```

## 4. GPT-4.1 single-shot baseline (Table 5)

```bash
export OPENAI_API_KEY=...
python eval/run_paper_eval.py \
    --fixtures eval/datasets/manifest.yaml \
    --phase 1 --conditions gpt41-singleshot \
    --out /tmp/live/gpt41
```

The GPT-4.1 baseline does not have cassettes — it is a comparator that we
re-run from scratch.

## 5. Re-rendering tables and figures from a results CSV

If you only want to regenerate the LaTeX tables and matplotlib figures from
an existing `results.csv`:

```bash
python scripts/rerender_eval_artifacts.py \
    --out results/phase1
python scripts/rerender_eval_artifacts.py \
    --out results/phase2
```

## 6. Verifying the DEXPI 2.0 layer

```bash
pytest tests/unit/test_dexpi_*.py        # ~30 tests, covers JSON, XML, builder
pip-licenses --format=plain | grep -iE 'AGPL'   # expect no output
```

The first command exercises the JSON IO, XML IO, builder fallbacks, refs,
extensions, namespace shims, validation, and the SVG / drawio renderers.
The second confirms no AGPL-licensed packages reached your environment —
diagex shipped under Apache-2.0 once `pydexpi` was replaced by the native
DEXPI 2.0 model under `src/diagex/dexpi/`.

## 7. Optional: regenerating `_generated/` (Python 3.12+)

You should not need to do this; `_generated/` is checked in. But if you want
to verify the derivation chain end-to-end:

```bash
python3.12 -m venv .venv-codegen && source .venv-codegen/bin/activate
pip install -e '.[codegen]'
python -m diagex.dexpi.codegen.regenerate
git diff --stat src/diagex/dexpi/_generated/      # expect zero diff
```

## Mapping numbers to commands

`results/README.md` has the table mapping each paper number to the
`results.csv` row and the script invocation that re-derives it.
