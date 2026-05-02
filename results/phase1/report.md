# diagex eval report — run `20260427T174115-5a9b`

Invocation: `eval/run_paper_eval.py --phase 1 --conditions baseline --n-replicates 3 --parallel 4 --out out/diagex-phase1/ --emit tables,figures,artifacts`

Rows: 120

## Phase 1 (baseline) — per-fixture overall

- butane1: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$1.3525, in=175,150, out=10,939, cache_read=149,288, wall=6m32s]
- butane2: overall=0.92 (inv=1.00, cnt=1.00, conn=0.67, ident=1.00)  [n=12, cost=$2.2773, in=316,049, out=18,387, cache_read=284,062, wall=9m55s]
- dexpi-reference: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$0.5655, in=61,532, out=4,677, cache_read=71,107, wall=2m57s]
- grit-washer1: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$1.0424, in=136,957, out=9,591, cache_read=150,030, wall=5m28s]
- open100-1: overall=0.99 (inv=0.97, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$1.4218, in=168,401, out=13,502, cache_read=289,577, wall=7m13s]
- open100-2: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$0.8096, in=110,364, out=5,216, cache_read=95,154, wall=3m45s]
- open100-3: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$1.3656, in=162,167, out=12,677, cache_read=241,228, wall=6m30s]
- open100-4: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$2.1601, in=267,489, out=19,538, cache_read=307,723, wall=9m00s]
- tennessee1: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$0.6221, in=77,668, out=5,528, cache_read=84,674, wall=3m20s]
- two-tanks: overall=1.00 (inv=1.00, cnt=1.00, conn=1.00, ident=1.00)  [n=12, cost=$2.7515, in=274,547, out=27,397, cache_read=892,237, wall=12m07s]

**macro**: overall=0.99  cost_total=$14.3683, cost_median=$0.0731, in=1,750,324, out=127,452, cache_read=2,565,080, wall_total=1h06m, latency_median=23.2s

## Run totals

_(condition: baseline)_
  - **Phase 1** — calls=120, cost=$14.3683, in=1,750,324, out=127,452, cache_read=2,565,080, cache_hit=57%, steps=474, tool_calls=440, wall=1h06m
  - **Combined** — calls=120, cost=$14.3683, in=1,750,324, out=127,452, cache_read=2,565,080, cache_hit=57%, steps=474, tool_calls=440, wall=1h06m

### Tool-call breakdown

- get_region: 302 (68.6%)
- get_overview: 121 (27.5%)
- get_tile: 9 (2.0%)
- finish: 5 (1.1%)
- list_tiles: 3 (0.7%)

## Δ vs. previous run (≥ 2.0σ)

(no metrics moved beyond threshold)

Conditions in this run: baseline
