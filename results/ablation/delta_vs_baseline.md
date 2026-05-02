# §V-D minimal ablation — `--no-tile` vs `baseline`

Run: `20260428T084608-e35c` (3 fixtures, parallel=3, ~38 min wall clock).

Baseline reference: latest per-fixture run from `out/diagex-phase2/results*.csv`
(`20260427T144955-1dbc` for butane1 + dexpi-reference; `20260427T110420-2fa0` for tennessee1).

## Per-fixture deltas (ablation − baseline)

| fixture | equip F1 | instr F1 | OPC F1 | tag-OCR EM | edge F1 | DEXPI | cost USD | wall s |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| dexpi-reference | 0.941 → 0.889 (−0.052) | 1.000 → 0.857 (−0.143) | 0.909 → 0.909 (+0.000) | 0.667 → 0.611 (−0.056) | 0.400 → 0.303 (−0.097) | ✓ → ✓ | 2.99 → 4.09 (+1.10) | 535 → 852 (+317) |
| butane1 | 1.000 → 0.556 (−0.444) | 1.000 → 0.372 (−0.628) | 0.800 → 0.923 (+0.123) | 0.759 → 0.296 (−0.463) | 0.211 → 0.000 (−0.211) | ✓ → ✓ | 6.59 → 7.42 (+0.84) | 827 → 1252 (+425) |
| tennessee1 | 0.900 → 0.829 (−0.071) | 1.000 → 1.000 (+0.000) | 0.909 → 0.909 (+0.000) | 0.886 → 0.900 (+0.014) | 0.246 → 0.696 (+0.450) | ✓ → ✓ | 1.78 → 3.85 (+2.07) | 246 → 434 (+189) |

## Means across 3 fixtures

| metric | baseline | ablation | Δ |
|---|---:|---:|---:|
| equipment F1 | 0.947 | 0.758 | **−0.189** |
| instrument F1 | 1.000 | 0.743 | **−0.257** |
| OPC F1 | 0.873 | 0.914 | +0.041 |
| tag OCR EM | 0.771 | 0.602 | **−0.169** |
| edge F1 | 0.285 | 0.333 | +0.048 |
| DEXPI validates | 1.000 | 1.000 | 0.000 |
| cost USD / fixture | 3.79 | 5.12 | **+1.33** (+35%) |
| wall-clock s / fixture | 536 | 846 | +310 |

## §V-D draft (3 sentences)

> Replacing tile-on-demand with a single page-overview image — same Opus 4.7,
> page rendered at ≤2000 px long-side and fed at the model's 3.75 MP cap —
> drops mean equipment F1 by 0.19, mean instrument F1 by 0.26, and mean tag-OCR
> EM by 0.17 across the three fully-annotated fixtures, while raising mean
> cost by USD 1.33/fixture (+35%) and wall-clock by ~5 min/fixture as the
> agent compensates with more `get_region` calls and annotation steps. The
> hit is dominated by the dense raster fixture (`butane1`: equipment F1
> 1.00 → 0.56, instrument F1 1.00 → 0.37, tag OCR 0.76 → 0.30); on the small
> vector fixture (`tennessee1`) the agent recovers and even improves edge F1
> (0.25 → 0.70) while keeping tag legibility (0.89 → 0.90). DEXPI validation passes
> on all six runs (3 fixtures × 2 conditions).

## Interpretation notes

- **The model isn't the bottleneck — visual resolution is.** Per-kind F1 takes the largest hit (equipment −0.19, instrument −0.26); `tag_ocr_em` falls less (0.77 → 0.60, −0.17) because the metric measures OCR fidelity *given the entity is identified* and the agent recovers most tags via `get_region` zoom-ins even with the page fed as a single image. Where the no-tile mode falls apart is identification itself: it cannot reliably localize and classify symbols against the downscaled overview.
- **Cost goes *up* without tiling.** Counter to the naive intuition that "no tiles = fewer images = cheaper", the agent compensates by issuing many more `get_region` zoom-ins and annotation steps (butane1 ablation: 139 steps, 4 retries). Tiling pays for itself.
- **`butane1` is the canonical worst case** — dense raster, large page; the no-tile downscale destroys it. `tennessee1` is small enough that one page-overview is closer to baseline.
- **`--no-legend` was not run.** Plan §5.4 makes it conditional on baseline showing legend-driven failures; the baseline numbers don't surface that signature, so the optional second ablation is not load-bearing for the §V-D claim.
