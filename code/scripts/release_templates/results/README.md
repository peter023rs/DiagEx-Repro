# Results — paper-number provenance map

Every number in the paper traces back to a row (or roll-up) of one of the
four `results.csv` files in this directory. This document is the map.

## File layout

```
results/
├── phase1/
│   ├── results.csv            # canonical Phase 1 row set
│   ├── tables/table2.tex      # the paper's Table 2 (Phase 1 macro-F1 etc.)
│   ├── figures/fig2*.pdf      # the paper's Figure 2 (cost vs. accuracy)
│   ├── report.md
│   ├── invocation.txt
│   └── qa_analysis.xlsx
├── phase2/
│   ├── results.csv
│   ├── tables/{table2,table3}.tex
│   ├── figures/{fig2,fig3*}.pdf
│   ├── diagnostics/{phase2_diagnostics,truth_cleanup}.xlsx
│   ├── rater_action_rates.json
│   ├── report.md
│   └── invocation.txt
├── ablation/
│   ├── results.csv
│   ├── tables/, figures/, report.md, delta_vs_baseline.md
│   └── invocation.txt
├── gpt41/
│   ├── results.csv
│   ├── tables/, figures/, report.md
│   └── invocation.txt
└── README.md            # this file
```

## Number → CSV row → command

| Paper element                                  | Source file                      | Row filter                                         | Re-derive with                                                                                               |
|------------------------------------------------|----------------------------------|----------------------------------------------------|--------------------------------------------------------------------------------------------------------------|
| Table 2 (Phase 1 macro-F1, cost, latency)      | `phase1/results.csv`             | `condition=baseline, phase=1, metric_kind=phase1_query` aggregated by query family | `python code/scripts/rerender_eval_artifacts.py --out results/phase1`                                         |
| Figure 2 (Phase 1 cost vs. accuracy)           | `phase1/results.csv`             | same as Table 2                                     | same as Table 2                                                                                              |
| Table 3 (Phase 2 per-fixture P/R/F1)           | `phase2/results.csv`             | `condition=baseline, phase=2, metric_kind in {phase2_equipment_f1, phase2_segment_f1, ...}` | `python code/scripts/rerender_eval_artifacts.py --out results/phase2`                                         |
| Figure 3 (Phase 2 per-fixture heterogeneity)   | `phase2/results.csv`             | same as Table 3                                     | same as Table 3                                                                                              |
| Table 4 (no-tile ablation Δ vs. baseline)      | `ablation/results.csv` + `phase2/results.csv` | join on `(fixture, metric_kind)`        | `python code/scripts/rerender_eval_artifacts.py --out results/ablation` and read `delta_vs_baseline.md`     |
| Table 5 (GPT-4.1 single-shot baseline Phase 1) | `gpt41/results.csv`              | `condition=gpt41-singleshot, phase=1`              | `python code/scripts/rerender_eval_artifacts.py --out results/gpt41`                                         |
| §V retention numbers                           | `data/ground_truth/_retention.v0.2.json` | per-fixture                            | `python code/scripts/measure_retention.py`                                                                    |
| §VI rater↔model agreement evidence             | `data/ground_truth/<stem>/graph.truth.history.json` (per fixture) + `phase2/rater_action_rates.json` | per fixture | `python code/eval/rater_action_rates.py --out results/phase2`                                                 |

## Why the snapshot CSVs are stripped

The source repo carries a few mid-stabilisation snapshots
(`results.before-targeted.csv`, `results.before-rerun.csv`, etc.). These are
not in the archive — they are internal scratch from the truth-correction
loop. The canonical `results.csv` in each subdirectory is what every paper
number traces back to.

## Why per-run transcripts are not here

Per-run agent transcripts, tile crops, intermediate DEXPI 2.0 JSON, debug
HTML, and the like are large (~150–250 MB total) and not needed to verify
any paper number. They are in the **separate Zenodo supplementary
deposition** linked from `.zenodo.json` (`related_identifiers` →
`isSupplementedBy`). Pull that archive if you want to inspect what the agent
saw tile-by-tile or replay a single fixture's run end-to-end.
