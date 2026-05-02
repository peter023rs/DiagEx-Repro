# diagex eval report — run `20260428T084608-e35c`

Invocation: `eval/run_paper_eval.py --phase 2 --conditions ablation-no-tile --only dexpi-reference,butane1,tennessee1 --parallel 3 --out out/diagex-ablation`

Rows: 21

## Run totals

_(condition: ablation-no-tile)_
  - **Phase 2** — calls=3, cost=$15.3603, in=1,056,387, out=157,069, cache_read=3,064,345, cache_hit=63%, steps=231, tool_calls=405, retries=5, wall=42m18s
  - **Combined** — calls=3, cost=$15.3603, in=1,056,387, out=157,069, cache_read=3,064,345, cache_hit=63%, steps=231, tool_calls=405, retries=5, wall=42m18s

### Tool-call breakdown

- annotate: 302 (74.6%)
- get_region: 87 (21.5%)
- get_overview: 7 (1.7%)
- list_annotations: 3 (0.7%)
- list_tiles: 3 (0.7%)
- finish: 2 (0.5%)
- get_tile: 1 (0.2%)

Conditions in this run: ablation-no-tile
