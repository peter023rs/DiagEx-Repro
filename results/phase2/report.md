# diagex eval report — run `20260428T083413-45a0`

Invocation: `eval/run_paper_eval.py --phase 2 --parallel 1 --out out/diagex-phase2 --only two-tanks --resume-force`

Rows: 56

## Phase 2 (baseline) — per-fixture extraction

- butane1: eq_f1=1.00, inst_f1=1.00, opc_f1=0.80, edge_f1=0.21  [cost=$6.5873, in=402,869, out=42,522, cache_read=1,630,821, steps=37, wall=13m46s]
- butane2: eq_f1=1.00, inst_f1=0.85, opc_f1=n/a, edge_f1=n/a  [cost=$0.6253, in=67,060, out=9,540, cache_read=0, steps=0, wall=2m22s]
- dexpi-reference: eq_f1=0.94, inst_f1=1.00, opc_f1=0.91, edge_f1=0.40  [cost=$2.9875, in=224,577, out=25,452, cache_read=1,525,959, steps=45, wall=8m55s]
- grit-washer1: eq_f1=0.67, inst_f1=0.86, opc_f1=n/a, edge_f1=n/a  [cost=$6.3448, in=376,408, out=46,530, cache_read=1,379,606, steps=43, wall=13m30s]
- open100-1: eq_f1=1.00, inst_f1=0.85, opc_f1=n/a, edge_f1=n/a  [cost=$1.4398, in=93,360, out=14,146, cache_read=0, steps=0, wall=2m56s]
- open100-2: eq_f1=1.00, inst_f1=1.00, opc_f1=n/a, edge_f1=n/a  [cost=$1.0034, in=74,923, out=10,568, cache_read=0, steps=0, wall=2m13s]
- open100-3: eq_f1=1.00, inst_f1=0.79, opc_f1=n/a, edge_f1=n/a  [cost=$2.0956, in=174,374, out=32,110, cache_read=0, steps=0, wall=9m01s]
- open100-4: eq_f1=0.91, inst_f1=0.85, opc_f1=n/a, edge_f1=n/a  [cost=$5.5374, in=419,477, out=47,930, cache_read=678,102, steps=55, wall=22m17s]
- tennessee1: eq_f1=0.90, inst_f1=1.00, opc_f1=0.91, edge_f1=0.25  [cost=$1.1979, in=110,547, out=23,137, cache_read=0, steps=0, wall=3m33s]
- two-tanks: eq_f1=0.78, inst_f1=0.82, opc_f1=n/a, edge_f1=n/a  [cost=$10.3529, in=780,172, out=42,991, cache_read=1,094,349, steps=96, wall=11m21s]

## Run totals

_(condition: baseline)_
  - **Phase 2** — calls=10, cost=$38.1720, in=2,723,767, out=294,926, cache_read=6,308,837, cache_hit=57%, steps=276, tool_calls=622, retries=38, wall=1h30m
  - **Combined** — calls=10, cost=$38.1720, in=2,723,767, out=294,926, cache_read=6,308,837, cache_hit=57%, steps=276, tool_calls=622, retries=38, wall=1h30m

### Tool-call breakdown

- annotate: 486 (78.1%)
- get_tile: 90 (14.5%)
- get_region: 26 (4.2%)
- get_overview: 7 (1.1%)
- list_tiles: 5 (0.8%)
- finish: 4 (0.6%)
- list_annotations: 4 (0.6%)

## Δ vs. previous run (≥ 2.0σ)

(no metrics moved beyond threshold)

Conditions in this run: baseline
