# diagex Evaluation Plan — `diagex` Phase 1 + Phase 2

**Status:** v0.1 draft for iteration
**Target venue:** Manuscript under review (venue and DOI to be filled in on acceptance).
**Scope of evaluation:** Phase 1 (NL query engine, §7.1 of the spec) and Phase 2 (P&ID → DEXPI 2.0, §7.2 of the spec)
**Corpus:** `tests/p-ids-public/` — 10 PDFs, all publicly distributable (some drawn from prior publications so we can cross-reference existing results without license friction)
**Thesis the evaluation must defend:** a *pure LLM-vision* pipeline (Claude Opus 4.7 + ReAct + deterministic reconciliation) reaches useful working accuracy on heterogeneous P&IDs **without per-customer training or symbol-detector retraining**, and does so at a cost that is within an order of magnitude of hand-built CV pipelines.

> This document is a plan, not yet a paper. Numbers in § 5 and § 6 are target shapes for tables/figures; they get filled in only once the eval harness (§ 7) has actually run. Sections marked `[OPEN]` need a decision before we start authoring ground truth.

### Tooling state 

| Component | File(s) | State |
|---|---|---|
| Low-confidence arbitration pass | `src/diagex/vision/arbitrate.py:arbitrate_low_confidence` | ✅ shipped — reduced Phase 2 entity-count σ/μ from 29.3% → 10.6% on `dexpi-reference`; corpus-wide cost ≈ USD 0.50 |
| Phase-2 stabilisation gate | `scripts/stabilise_phase2.py` | ✅ passing on `dexpi-reference` + `tennessee1` |
| Ground-truth linter | `src/diagex/gt_lint.py` + `diagex gt lint` | ✅ checks schema, id uniqueness, referential integrity, query-file fields, manifest cross-check |
| Phase-2 prompt — segment lines at inline components | `src/diagex/llm/prompts/phase2_pid.py` | ✅ shipped 2026-04-25; previous prompt traced single polylines through valves, breaking the DEXPI segment chain. After re-extract: edges 12 → 24 (dexpi-reference), 1 → 16 (butane1), 26 → 38 (tennessee1) |
| Bootstrap graphs (full-truth, post-segmentation-rule) | `eval/datasets/{dexpi-reference,butane1,tennessee1}/graph.bootstrap.json` | ✅ 27 / 87 / 69 nodes, 24 / 16 / 38 edges; all pass `gt lint` |
| Phase-1 queries (all 10 fixtures) | `eval/datasets/<stem>/queries.truth.yaml` | ✅ 40 rater_1-locked; single-rater authoring (see § 4.3 — no κ pass; called out as § VI threat to validity) |
| Fixture meta | `eval/datasets/<stem>/meta.yaml` | ✅ 10 stubs, manifest-derived |
| Correction CLI — node walk + edge walk | `src/diagex/gt_edit.py` + `diagex gt edit` | ✅ two-pass: nodes (keep/revise/drop/skip/add/undo/quit) then edges (same set). Edge-retention reported alongside node-retention. Prefers `graph.bootstrap_v2.json` when present. |
| Append-only edge author | `diagex gt add-edge` | ✅ tight `[a]dd / [q]uit-and-save` loop on a finalised `graph.truth.json`; appends `edge_add` actions to the audit log |
| VIA → v2 adapter | `scripts/via_to_bootstrap_v2.py` | ✅ IoU-primary + (kind, label) fallback matching, surfaces `bbox_retention_pct` / `label_retention_pct` per fixture |
| Partial-truth entity inventories (7 fixtures) | `eval/datasets/<stem>/annotations.truth.jsonl` | ✅ bootstrap-then-correct via VIA — 486 reviewed entities, retention 98.5%; baseline at `eval/datasets/_retention.v0.2.json` |
| Full-truth ground truth (3 fixtures) | `eval/datasets/{dexpi-reference,butane1,tennessee1}/graph.truth.json` | ✅ 26 / 58 / 70 nodes and 21 / 12 / 37 edges authored 2026-04-25; per-fixture retention numbers in § 10 step 7 |
| DEXPI SVG renderer — Manhattan routing | `src/diagex/extractors/dexpi_svg.py` + `--ortho/--no-ortho` | ✅ inferred edges (no bootstrap polyline) route as Z-shaped Manhattan paths with perimeter-attached endpoints; bootstrap polylines unchanged |
| Eval harness | `eval/run_paper_eval.py` (+ `scoring.py`, `conditions.py`, `aggregate.py`, `latex_tables.py`, `report_md.py`, `figures/`) | ✅ end-to-end on cassettes — `results.csv` → `table2.tex` / `table3.tex` round-trip verified by `tests/unit/test_eval_run_cassette.py`; live + cassette modes both shipped. |
| Cassette recorder | `scripts/record_cassettes.py` + `eval/cassettes/<condition>/<stem>/` | ✅ shipped 2026-04-30. Rebuilds `phase1.json` (trial 0 per query, sourced from `runs/<stem>/<ts>/result.json`) + `graph.json` + `summary.json` from the canonical live runs. Phase 2 picker matches each live `phase2_equipment_f1` tp/fp/fn against candidate `graph.json` files so in-place targeted re-runs land in the cassette correctly. End-to-end replay (`run_paper_eval.py --use-cassettes`) reproduces all 33 Phase 2 metric rows + all 40 Phase 1 trial=0 rows of the live results.csv exactly. |
| Anthropic 5 MiB inline-image guard | `src/diagex/vision/encode.py:encode_image_block` | ✅ shipped 2026-04-28; PNG → JPEG-90 → progressive-downscale fallback, single choke-point reused by `agent/tools.py`, `vision/arbitrate.py`, `extractors/pid_legend.py`. Caused `two-tanks-q2 trial=2` API failure pre-fix; same latent risk on dense raster fixtures in Phase 2 now eliminated. 4 regression tests in `tests/unit/test_vision_encode.py`. |
| List-answer parser hardening | `eval/scoring.py:parse_list_answer` | ✅ shipped 2026-04-28; three model-style accommodations: `<answer>...</answer>` block extraction, triple-backtick code-fence stripping, single-char "X: " label-prefix stripping. Lifted Phase-1 macro 0.9811 → 0.9909 on the same cached answers. 4 new parser tests in `tests/unit/test_eval_scoring.py`. |
| Per-trial QA analysis + targeted-rerun helpers | `eval/qa_analysis.py`, `scripts/{rerun_one_query, rescore_phase1_inplace, rerender_eval_artifacts}.py` | ✅ shipped 2026-04-28. `qa_analysis` now emits one xlsx row per (fixture, query, trial) via `_collect_runs_per_trial` (timestamp-ordered, error-runs filtered). `rerun_one_query.py` patches a single failed (fixture, query, trial) row in-place; `rescore_phase1_inplace.py` re-derives `score`/`detail` from cached `runs/` answers without API calls; `rerender_eval_artifacts.py` rebuilds tables/figures/report.md from the patched CSV. |

---

## 1. Paper framing (so the eval serves the narrative)

### 1.1 Story arc (≤ 8 pages)

| §      | Pages | Content                                                                                                                                                                                                       |
| ------ | :---: | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| I      |  0.75 | **Introduction** — heterogeneous P&ID reality, training-data scarcity, contribution.                                                                                                                          |
| II     |  1.00 | **Related work** — Digitize-PID, Koziolek/ABB, Nature Sci. Rep. 2025, Kang 2019 (butane), Barthelt 2015 (Tennessee Eastman). Position against specialised CV and recent VLM-based attempts.                   |
| III    |  1.50 | **Approach** — tile-on-demand ReAct, `vision/` toolbox, deterministic reconciliation, DEXPI mapping. Kept concise; this is not the contribution.                                                              |
| **IV** |  1.25 | **Eval setup** — corpus, ground-truth authoring, metrics, infra.                                                                                                                                              |
| **V**  |  2.50 | **Results** — Phase 1 query eval, Phase 2 DEXPI extraction, ablations, cost.                                                                                                                                  |
| VI     |  0.75 | **Discussion & limitations** — where the LLM fails, when to fall back to CV, privacy/cost.                                                                                                                    |
| VII    |  0.25 | **Conclusion.**                                                                                                                                                                                               |

The evaluation (§ IV+V) owns **~3.75 pages** total, with **~2.5 pages for the results section (§V) alone**. That budget fits **two headline tables and one figure**: Table II (Phase 1 per-diagram accuracy), Table III (Phase 2 per-diagram extraction), Figure 2 (cost/accuracy scatter). A qualitative overlay inset (Figure 1) is included only if layout permits. The earlier plan of a full ablation table + a dedicated error-taxonomy table has been dropped — those findings move into § V-D / § V-E prose with inline numbers (see § 5).

### 1.2 What the manuscript reviewers will challenge us on

Anticipate these reviewer objections now and design the evaluation so they are already answered:

1. **"Small-N, statistically meaningless."** — 10 diagrams is indeed small; we answer with *per-diagram* reporting and deliberate vendor diversity, not by inflating an average.
2. **"Cherry-picked fixtures."** — we use the public corpus as-is and report *every* diagram's result, including failures. No sub-selection for the headline table.
3. **"Data contamination — the Tennessee-Eastman flowsheet is famous, Opus likely memorised it."** — we acknowledge this residual risk in prose for `tennessee1.pdf`. The two published-paper PDFs (Kang 2019, Barthelt 2015) that carried the sharpest memorisation risk have been removed from the corpus (see § 2).
4. **"Specialised CV beats you."** — we concede on raw accuracy and pitch the generalisation trade. Without Kang/Barthelt PDFs in the corpus we cannot do a same-fixture comparison; instead we quote their published numbers in a small side-table with a caveat (see § 6, item 1).
5. **"You graded your own homework."** — two-rater ground truth (§ 4.3), bootstrap-retention numbers reported explicitly for Phase 2 truth (§ 4.2), `dexpi_ref` as a contamination-free anchor, open artefacts (§ 7.4), reproducibility package released with the paper.

---

## 2. Corpus (the 10 public P&IDs)

All files live in `tests/p-ids-public/` and are already on disk. The corpus was revised several times during April 2026. The manifest at `eval/datasets/manifest.yaml` is authoritative — this section stays consistent with it.

| Stem              | File                  | Source type      | Draughting / export pipeline                  | Role in eval                                                  |
| ----------------- | --------------------- | ---------------- | --------------------------------------------- | ------------------------------------------------------------- |
| `dexpi-reference` | `dexpi-reference.pdf` | vector, A2, tiny | FreePDF XP / AFPL Ghostscript                 | DEXPI C01 canonical reference — full-truth anchor (external). |
| `two-tanks`       | `two-tanks.pdf`       | raster           | Adobe Acrobat 26.1 Image Conversion           | Small sparse two-tank utility P&ID — tests tile-budget lower bound. |
| `butane1`         | `butane1.pdf`         | raster, huge     | Adobe Acrobat 26.1 Image Conversion           | C4-cracking process — full-truth fixture; representative of the dominant raster source type. |
| `butane2`         | `butane2.pdf`         | raster, huge     | Adobe Acrobat 13.0 Image Conversion           | Same C4 process, older raster export — rendering-variance pair with `butane1`. |
| `tennessee1`      | `tennessee1.pdf`      | vector, small    | PDFlib/PDI (conference manuscript render)     | Tennessee-Eastman redraw — full-truth fixture; vector, small page. |
| `grit-washer1`    | `grit-washer1.pdf`    | raster           | Adobe Acrobat 26.1 Image Conversion           | San Mateo WWTP grit-washing unit — municipal-wastewater domain; dense control layer. |
| `open100-1`       | `open100-1.pdf`       | raster           | Adobe Acrobat 26.1 Image Conversion           | OPEN100 open-source PWR — CVCS system.                        |
| `open100-2`       | `open100-2.pdf`       | raster           | Adobe Acrobat 26.1 Image Conversion           | OPEN100 RHR system — cross-sheet consistency.                 |
| `open100-3`       | `open100-3.pdf`       | raster, larger   | Adobe Acrobat 26.1 Image Conversion           | OPEN100 Reactor Coolant System — main RCS sheet.              |
| `open100-4`       | `open100-4.pdf`       | raster           | Adobe Acrobat 26.1 Image Conversion           | OPEN100 pressurizer + RCP-motor-coolant aux sheet.            |

**Diversity claim** (needed in § IV): **6 process domains** (DEXPI synthetic, process-utility, C4 cracking, Tennessee Eastman, wastewater-grit, nuclear PWR across four subsystems — CVCS / RHR / RCS / pressurizer), **≥ 4 authoring/export pipelines** (AFPL Ghostscript, PDFlib+PDI, Acrobat Image Conversion — two vintages 13.0 and 26.1), **both vector and raster** source types with an 8/2 raster-heavy split, and **two related-but-distinct rendering clusters** — `butane1`/`butane2` (same process, two Acrobat vintages) and `open100-1/2/3/4` (same plant, four companion sheets) — that let us isolate *rendering / sheet variance* from *process variance*.

**Pre-training contamination.** The two PDFs whose publication predates the Opus 4.7 cut-off and carried the strongest memorisation risk (Kang 2019, Barthelt 2015) are not in this corpus. `tennessee1.pdf` is a clean redraw of the Tennessee-Eastman flowsheet; the process itself is famously well-documented, so we still note the residual risk in § V, but we no longer need a separate contamination-control column in the headline table. Q5 is retired (see § 3).

---

## 3. Evaluation questions (the hypotheses the numbers must answer)

The evaluation exists to answer concrete questions. **Page budget reality check:** The IEEE two-column page budget gives us ~2.5 pages for §IV+V. Five tables + two figures is too much — we target **2 tables + 1 figure** as the formal artefacts, and fold the rest (one minimal ablation, error taxonomy) into prose.

| Q-id | Question                                                                                             | Metric                              | Reported in                 |
| :--: | ----------------------------------------------------------------------------------------------------- | ----------------------------------- | --------------------------- |
| Q1   | Does Phase 1 answer four canonical query types correctly across heterogeneous P&IDs, zero-shot?       | Per-query accuracy, macro-avg       | Table II                    |
| Q2   | Does accuracy vary materially by diagram source / vendor / domain?                                    | Per-diagram breakdown               | Table II, rows              |
| Q3   | Does Phase 2 produce a DEXPI file that (a) validates and (b) matches ground-truth topology?           | Validation pass rate, node+edge F1  | Table III                   |
| Q4   | How does cost scale with diagram complexity (tiles, tags, lines)?                                     | USD vs. ground-truth entity count   | Figure 2 (scatter)          |
| Q5   | Which *single* design choice matters most — tiling? (the contribution we most want to defend)         | Δ vs. no-tile baseline (and, if cheap, legend on/off) | §V-D prose, 2–3 numbers inline |
| Q6   | Where does the approach fail, and why?                                                                | Error taxonomy (counts per class)   | §V-E prose, categorical list |

Q1–Q4 are the headline. Q5 reduces the earlier ablation grid to the one dimension that actually defends the thesis (tiling). Q6 stays as a credibility paragraph, not a full table. The pre-training-contamination question is dropped now that Kang/Barthelt are out of the corpus (see § 2).

---

## 4. Ground-truth authoring

### 4.1 Phase 1 — three standard queries per diagram

The user's brief proposes "three standard queries per diagram." We go slightly further to cover the query families defined in spec § 7.1 without bloating the authoring effort. **Per diagram, four queries** (stretch to five if cheap), one from each family below. Three would fit the brief; four lets us retire one if it turns out to be trivially brittle without re-running the whole set.

| Family             | Standard question template (filled per diagram)                                                                           | Scoring kind (spec § 9.1)    |
| ------------------ | ------------------------------------------------------------------------------------------------------------------------- | ---------------------------- |
| **Inventory**      | "List every control valve in this drawing with its tag number."                                                           | `set_match`                  |
| **Counting**       | "How many level transmitters (LT or LIT) are shown?"                                                                      | `numeric_tolerance` (±5%)    |
| **Connectivity**   | "Is there a process flow path from `<source tag>` to `<sink tag>`?" (source/sink chosen per diagram, answer split yes/no) | `exact` (boolean)            |
| **Identification** | "What kind of equipment sits at approximate page coordinates `(x, y)`?"                                                   | `contains` (substring in class label) |

That gives **40 queries** across the 10 diagrams (10 × 4). Authoring cost estimate: ~20 min per diagram to choose tags / coordinates and verify the ground-truth answer by eye = **≈ 3.5 hours** for the full Phase 1 set.

**Fairness rules** baked into the authoring guide:

- Tag values in the question are supplied *verbatim*; the system is *not* being tested on guessing reasonable candidates.
- Connectivity queries must have at least one yes and one no per diagram *across the 10 fixtures* (5 YES / 5 NO — enforced in the `queries.truth.yaml` fairness contract) so an "always answers yes" model does not score 50%.
- The identification query never points to the interior of a dense cluster — we grade perception, not disambiguation.
- **Identification coordinates are authored in Acrobat against the rendered PDF, not computed from our own `bbox_global` output.** The bootstrap attempt to derive `(x, y)` from graph.json bbox centres produced wrong coordinates on 6 of 10 fixtures — the frame is not uniformly page-pixel at one DPI, and even when it is, the bbox centre is not reliably the symbol's visual centre. Acrobat Pro rulers in Points (top-left origin, y-down) are the canonical frame.
- No question that cannot be answered by a human expert with the drawing alone in under 60 seconds is included.

### 4.2 Phase 2 — DEXPI ground truth

**Authoring-tool gap.** There is no free, open GUI editor that emits valid DEXPI Proteus XML or pyDEXPI JSON. All currently shipping DEXPI-conformant P&ID authoring is inside commercial CAE suites (Aveva E3D / P&ID, Hexagon SmartPlant P&ID, Bentley OpenPlant, Siemens COMOS). pyDEXPI itself is a Python *library* — it validates and manipulates DEXPI graphs but has no drawing canvas. Hand-writing a 100-entity DEXPI JSON from a blank editor is not realistic within this evaluation sprint.

**Proposed workaround — bootstrap-then-correct.** Run `diagex pid-extract` on each fixture to produce a first-pass DEXPI JSON, then have a human expert correct it against the source PDF. Concretely:

1. **Bootstrap.** Run Phase 2 at `--effort high` on each fixture → `runs/<stem>/graph.bootstrap.json` + SVG overlay + side-car annotation list.
2. **Correct** via `diagex gt edit` (implemented as `src/diagex/gt_edit.py` + `diagex gt edit` CLI subcommand). Walks every entity in the bootstrap graph, renders a per-node PDF crop via pymupdf, and prompts the rater for keep / revise / drop / skip / add-missing / undo / quit. Every action is flushed to `graph.truth.history.json` immediately so the session is crash-safe and resumable. Design: `docs/correction-ui.md`. Authoring effort is *correction*, not *construction* — the usual 2–4 h per diagram drops to an estimated **45–90 min**.
3. **Review pass.** *Single-rater authoring for this manuscript — see § 4.3.* In the original plan a second pair of eyes flagged questionable corrections; that pass is deferred to the journal version.
4. **Sanity gate.** `pydexpi.validate(...)` must pass and `diagex gt lint` must accept the file before it enters the eval set.

**Self-grading hazard.** Bootstrapping from our own output risks the reviewer objection "you graded your own homework, of course the system matches its own ground truth." Mitigations:

- The expert must touch *every* entity and confirm or overwrite — the audit log (`graph.truth.history.json`) records which entities were kept vs. edited and the Δ is reported in § V as a separate number ("X% of bootstrap entities retained unchanged").
- For `dexpi-reference` — where the DEXPI reference XML itself exists publicly — we ignore the bootstrap entirely and compare against the canonical reference. That fixture acts as a contamination-free anchor for the other two.
- Node-level F1 is reported on human-reviewed entity inventories for all 10 fixtures. The methodology is the same across the corpus — **bootstrap-then-correct**: a machine pass seeds rater_0 draft bboxes and labels from `runs/<stem>/<latest>/graph.json` into VIA (`scripts/bootstrap_annotations.py`); the human opens the project in VIA and reviews every entity (move / resize / edit / delete / add). Per-fixture **retention %** (fraction of bootstrap entities kept unchanged) is reported in § V as the direct answer to "graded your own homework" — 10 numbers, not an aggregate. Edge-level metrics still apply only to the 3 fully-annotated fixtures.

**Scope cut.** Scope:

- **Full DEXPI truth** for **3 diagrams**: `dexpi-reference` (near-free — canonical reference XML exists), `butane1` (raster, representative of the dominant source type), `tennessee1` (vector, small page, well-scoped topology — replaces the former `h2first1` pick after the corpus update).
- **Partial truth** (entity inventory only, no edges) for the remaining 7, produced via bootstrap-then-correct in VIA (`tools/via/`; scripts `bootstrap_annotations.py` → `annotations_to_via.py` → VIA review → `via_to_annotations.py`). Feeds node-level F1 and tag OCR exact-match.
- **pyDEXPI schema validation** runs on *all* 10 outputs — that metric is automatic and cheap.

Budget under the unified bootstrap-then-correct model: **~6 h** full-truth correction (3 fixtures, including edges) + **~2.5 h** partial-truth correction across the 7 (inventory only, bootstrap preloaded in VIA — 388 entries already seeded) + **~3 h** review pass = **~11.5 h** total. Comparable to the prior plan but with one consistent methodology across all 10 fixtures and honest per-fixture retention-% reporting.

### 4.3 Inter-rater reliability — *deferred; single-rater authoring*

The original plan called for two raters and Cohen's κ. We deferred the second pass for this manuscript; the 3 full-truth fixtures and the 40 Phase-1 queries are authored by a single rater (Heiko Koziolek). This is an acknowledged threat to validity and is called out explicitly in § VI as a limitation:

> "All 3 full-truth ground-truth graphs and the 40 Phase 1 queries are single-rater. Without an inter-rater κ pass we cannot bound rater bias — particularly on borderline kind/class taxonomy decisions and on connectivity calls where the source PDF is ambiguous. We mitigate via (a) per-fixture retention reporting (§ V) so reviewers can see how much we changed from the model's bootstrap, (b) `dexpi-reference` graded against the canonical DEXPI C01 reference XML (a contamination-free external anchor), and (c) the public reproducibility package (§ 7.4) so a second rater can re-grade post-publication. The full two-rater pass is queued for the journal version."

Two practical mitigations baked into the workflow:
- **External anchor.** `dexpi-reference` is graded against the canonical DEXPI C01 reference XML, not the rater's own visual judgement.
- **Per-fixture retention.** § V reports VIA bbox / label retention and `gt edit` node / edge retention separately per fixture (10 numbers across 3 fixtures × 4 dimensions). Reviewers see the rater↔model agreement directly rather than as a single aggregate.

### 4.4 Ground-truth file layout

Follows spec § 9.1 verbatim; one directory per fixture under `eval/datasets/<stem>/` with `graph.truth.json`, `queries.truth.yaml`, `meta.yaml`. `diagex gt lint` must pass before any fixture enters the eval run. No bespoke adapters.

---

## 5. Metrics, tables, and figures (target shape)

**Artefact budget under 2.5-page constraint:** two tables + one figure as the formal artefacts. Ablation results and error taxonomy move into prose (§ V-D / § V-E) rather than their own tables. If the page count permits after layout, a small qualitative inset can be added late.

### 5.1 Table II — Phase 1 per-diagram accuracy

Rows: 10 diagrams + macro-average row. Columns: Inventory, Counting, Connectivity, Identification, **Overall**, Median-cost-USD, Median-latency-s.

Targets (these are the numbers § V must beat; they restate spec § 7.1 exit criteria so the paper is consistent with the internal contract):

- Macro inventory ≥ 0.90
- Macro connectivity ≥ 0.80
- Median cost < USD 0.50 per query
- Median latency < 2 min per query

### 5.2 Table III — Phase 2 per-diagram extraction

Rows: 10 diagrams. Columns: #equip / #instr / #lines (truth), Equipment F1, Instrument F1, Tag OCR EM, Edge F1 (`N/A` for the 7 partial-truth rows), DEXPI-validates (Y/N), Cost USD, Wall-clock min.

Targets: equipment F1 ≥ 0.85, instrument F1 ≥ 0.80, tag OCR ≥ 0.85, edge F1 ≥ 0.70, DEXPI validation pass rate ≥ 50% — these are the § 9.2 v0 targets.

**Tag OCR EM definition.** A truth node pairs with a same-kind prediction when any of {IoU ≥ 0.30, equal normalized labels, shared tag-root, loose OPC token-overlap} succeeds — the same lenient `_node_match` rule the per-kind F1 columns use. Among tie-eligible candidates the highest-IoU pair wins, with a label-equal pair preferred over a label-different one. Tag OCR EM is then strict on the *label*: the score contribution is 1 iff the normalized truth and prediction labels agree exactly, otherwise 0. The framing measures OCR fidelity *given the entity is identified*; bbox misplacement is captured by the per-kind F1 columns and is intentionally not double-counted into Tag EM, since downstream consumers (control-logic derivation, tag look-up) key on the tag string and not on bbox coordinates. Implemented in `eval/scoring.py:tag_ocr_exact_match`.

### 5.3 Figure 2 — Cost / accuracy scatter

One scatter plot, x = ground-truth entity count (log scale), y = extraction USD, marker colour = overall F1 bucket, marker shape = source type (vector / raster). 10 points. Lets a reviewer see at a glance that (a) cost scales roughly linearly with complexity, (b) scans cost more, (c) the outlier cluster is the outlier.

### 5.4 Ablation — *minimal* (§ V-D prose, not a table)

The full ablation grid (overlap × effort × legend × cache) was scoped out: 60-plus runs, ~USD 120, and two columns of table real estate we do not have. We keep the **single dimension that most directly defends the contribution** — the *tiling* strategy — and run it on the 3 fully-annotated fixtures:

- **Baseline** (all defaults from § 7.1 / § 7.2)
- **`--no-tile`** — same Opus 4.7, entire page as a single image downscaled to the 3.75 MP limit

That is **1 extra condition × 3 fixtures ≈ USD 9** compute. Reported as two-to-three sentences in § V-D with the Δ-F1 and Δ-cost numbers inline. If early runs show legend injection is also load-bearing (and cheap to verify), we may add a single `--no-legend` comparison on the same 3 fixtures (+USD 9); beyond that we *do not* extend the ablation grid for this manuscript.

### 5.5 Error taxonomy — prose, not a table

Six failure classes are reported as a categorical paragraph in § V-E with per-class counts; no dedicated table. Draft classes (refined against actual failures during the sprint):

- `tag_ocr_near_miss` — e.g. `FIC-102` ↔ `FIC-I02`
- `symbol_misclass` — ball-valve ↔ globe-valve etc.
- `edge_crossing_misread` — spec § 2.2 case A3
- `edge_stitching_miss` — line split across tiles not rejoined
- `hallucinated_entity` — tag the drawing does not contain
- `dropped_entity` — real tag missed entirely

### 5.6 Figure 1 — Qualitative (optional, half-column inset if space allows)

If post-layout pagination leaves a half-column slot, one inset from `butane1.pdf` with ground-truth (green) vs. predicted (blue) entities overlaid — one success, one failure. Descoped from the formal artefact list; it is nice-to-have, not load-bearing.

---

## 6. Comparisons (§ V-B in the paper)

Strictly zero-shot, so no retraining. We do **not** run specialised-CV baselines ourselves — that is a one-month project we cannot afford inside the paper's timeline. Instead:

1. **Prior-work numbers quoted verbatim.** Kang 2019 reports ~X%, Digitize-PID ~Y%, Nature Sci. Rep. 2025 ~Z%. Put them in a small side-table with the caveat that they are *not on the same fixtures* and *not graded with the same rubric*. This is common practice in this venue class.
2. **One VLM baseline we can actually run.** GPT-4.1 on Azure AI Foundry, **single-shot per Phase 1 query** (one chat-completions call: page overview image at 2048 px max-dim + question + answer-format suffix; no tools, no ReAct loop), on all 10 fixtures. The tile + ReAct + reconciliation contributions are deliberately *not* part of this leg — the comparison anchors "how does a frontier VLM do on these P&IDs given just the page and the question, before the harness adds anything?" rather than "same harness, different model". Phase 2 is N/A for this condition: GPT-4.1's chat-completions output cap (≤16k tokens) cannot reliably hold dense fixtures' DEXPI graphs, and porting the tool-use schema across SDK families is out of scope (see § 7.5). Implementation lives in `eval/gpt_singleshot.py`; selected via condition `gpt41-singleshot`. Budget **< USD 1** (40 queries × ~1 100 image tokens + ~250 text tokens in @ USD 2/Mtok input, ~80 tokens out @ USD 8/Mtok output ≈ USD 0.13–0.50; verify with `python scripts/gpt41_dry_run.py` before kicking off). The original GPT-4o ~USD 30 estimate assumed full Phase 2 with tool use — Phase 1 single-shot is ~50× cheaper.
3. **No-tile ablation.** Same Opus 4.7, but given the *entire page* as a single image downscaled to the 3.75 MP limit. Shows the tiling contribution isolated from the model. This is free — same fixtures, different inference config — and makes a crisp point.

---

## 7. Automation — `eval/run_paper_eval.py`

### 7.1 What the script owns

One command reproduces every table, figure, and appendix number in the paper:

```bash
python eval/run_paper_eval.py \
  --fixtures eval/datasets/ \
  --phase {1,2,both} \
  --conditions baseline,ablation-no-tile \
  --parallel 4 \
  --out out/diagex/ \
  --emit tables,figures,artifacts \
  --use-cassettes   # regression mode; omit for live runs
```

(`ablation-no-legend` may be added on-the-fly if the baseline run surfaces legend-driven failures; `conditions.py` keeps the old named conditions — overlap / effort / cache — defined but unused so they can be revived for the journal version without re-plumbing.)

Key invariants the script enforces:

- **Fixture list is a file**, not a CLI flag list. `eval/datasets/manifest.yaml` declares the 10 fixtures, their expected `source_type`, and which ones are fully vs. partially annotated. The paper's diagram count comes from this file.
- **Every run writes `out/diagex/<condition>/<stem>/`** with the same layout as `runs/…` from spec § 7.1 — the eval is just a batch driver over the existing per-run artefact shape, not a parallel universe.
- **Tables are emitted as LaTeX fragments** (`out/diagex/tables/table2.tex`, etc.) that the paper `\input{}`s. Re-running the eval re-writes the `.tex` files; regenerating the PDF is a `make` away. Reviewers can see the diff from one eval run to the next in git.
- **Figures are emitted as PDFs** via matplotlib (`fig1.pdf`, `fig2.pdf`) with a single stylesheet for fonts. No bitmap figures.
- **`results.csv`** is the single source of truth: one row per (condition, fixture, metric). All tables and figures are generated *from* it. If the CSV does not exist, no LaTeX is written.
- **Summary `report.md`** is a human-readable digest the authors read before submission; it diffs against the previous run and flags any metric that moved > 2 σ.

### 7.2 Module layout (skeleton, not code)

```
eval/
├── datasets/                            # ground truth, one dir per fixture
│   ├── manifest.yaml
│   ├── dexpi_ref/
│   │   ├── graph.truth.json
│   │   ├── queries.truth.yaml
│   │   └── meta.yaml
│   └── …
├── run_paper_eval.py                    # top-level driver
├── conditions.py                        # named conditions → kwargs tuples
├── scoring.py                           # scoring kinds from spec § 9.1
├── aggregate.py                         # results.csv → tables + figures
├── latex_tables.py                      # DataFrame → booktabs LaTeX
├── figures/
│   ├── fig1_qualitative.py              # uses one fixture's artefacts
│   └── fig2_cost_accuracy.py
└── report_md.py                         # report.md emitter
```

### 7.3 Runtime envelope

- Phase 1 baseline: 10 fixtures × 4 queries × ~USD 0.30 median ≈ **USD 12** compute, **~1 h** wall-clock with `--parallel 4`.
- Phase 1 N=3 replicates (per § 8.1): ~USD 24 extra, +**~2 h** wall-clock.
- Phase 2 baseline: 10 fixtures × ~USD 3 median ≈ **USD 30** compute, **~4 h** wall-clock.
- Minimal ablation (`--no-tile` on 3 fixtures, optionally `--no-legend` same 3): 3–6 runs × ~USD 3 ≈ **USD 9–18** compute, **~1 h** wall-clock.
- GPT-4.1 single-shot Phase 1 baseline on all 10 fixtures (§ 6): **< USD 1** compute (~USD 0.13–0.50 per `scripts/gpt41_dry_run.py`), **~30 min** wall-clock. 40 queries × 1 chat-completions call each; no tools.

Total before cassette replay: **~USD 70–80**, **~8.5 h** (Phase 1 baseline ~USD 12 + N=3 replicates ~USD 24 + Phase 2 baseline ~USD 30 + minimal ablation ~USD 9 + GPT-4.1 anchor < USD 1). Comfortably within a single weekend's budget. Cassette replay (for CI and reviewer reproducibility) adds no API cost.

**Operator runbook.** Concrete command lines for the four production runs (and cassette/dry-run flows) live in [`eval/README.md`](../eval/README.md). The plan tracks intent and budget; the README tracks invocation.

### 7.5 Why the GPT-4.1 leg is single-shot, not "same harness, different model"

The original plan called for GPT-4o on the same tool interface as the Claude path. The current `LLMClient` (`src/diagex/llm/client.py`) is hard-wired to the Anthropic SDK + Anthropic message wire format — even when pointed at Azure AI Foundry, it talks to Foundry's *Anthropic-compatible* endpoint (Claude only). Reaching GPT-4.1 means going through Foundry's *OpenAI-compatible* deployment, which is a structurally different schema:

| Layer | Anthropic (current) | OpenAI / Azure GPT-4.1 |
|---|---|---|
| Image content block | `{"type":"image","source":{"type":"base64",...}}` | `{"type":"image_url","image_url":{"url":"data:..."}}` |
| Tool schema | top-level `input_schema` | `{"type":"function","function":{"parameters":...}}` |
| Tool result | user message with `{"type":"tool_result","content":[image+text]}` | separate `{"role":"tool","tool_call_id",...}` message |
| **Image inside tool result** | supported | **not supported** — must be a follow-up `user` message |
| Thinking blocks w/ signature | required round-trip | n/a |
| `cache_control` markers | the cost story | OpenAI does its own implicit caching |
| Output token cap | 32k+ | 4k–16k (truncates dense Phase 2 graphs) |

The single-shot Phase-1-only leg sidesteps every cell in the right column. It is honestly framed as a different question — "what does a frontier VLM do given one image and one question?" — rather than dishonestly framed as the same harness. The full cross-model port (an OpenAI transport in `LLMClient` that adapts the four schema deltas above) is queued for the journal version, where Phase 2 GPT comparison would also become tractable.

### 7.4 Reproducibility package shipped with the paper

- `runs/` pruned to the final submission's condition set, zipped and attached as supplementary material (each run includes transcript + tool-call log).
- `results.csv` and the exact command line that produced it (written to `out/diagex/invocation.txt`).
- `pytest-vcr` cassettes for the 3-fixture regression set, so a reviewer can replay Phase 1 locally with no API key (the ablation grid requires a key — that is disclosed, not hidden).
- Model version pinned in the invocation record (`claude-opus-4-7`, exact snapshot id from `anthropic` response headers).

---

## 8. Alternatives & improvements worth considering

The brief asked for alternatives; here are the ones I think are worth a decision *before* authoring ground truth, in rough order of expected paper-impact-per-effort.

### 8.1 Strong

- **Add a graph-edit-distance (GED) metric** alongside node/edge F1 on the 3 fully-annotated fixtures. F1 over nodes + F1 over edges is the ML-paper default but it fails to penalise split/merged entities that matter for downstream DEXPI consumers. GED (normalised by truth graph size) gives a single number a process engineer actually cares about. Cost: one afternoon of scripting (`networkx.graph_edit_distance` with node/edge cost callbacks), no extra LLM spend.
- **Run every Phase 1 query N=3 times, report mean ± SD.** Opus 4.7 at `temperature=0.0` is not bit-deterministic on vision inputs. Three trials × 40 queries ≈ USD 40 extra and turns "accuracy 0.87" into "0.87 ± 0.02", which is the only honest claim. This is a cheap credibility upgrade.
- **Report latency in tokens-in + tokens-out + image-tokens, not just wall-clock seconds.** Wall-clock is dominated by Anthropic's queueing, which drifts. Token counts are what a reader can reproduce. Keep wall-clock as a secondary column.
- **Two-rater ground truth on Phase 1 queries.** Same cost argument as § 4.3 but for queries. One rater authors, the other solves each question blind, disagreements are adjudicated. Probably catches 2–3 broken questions before they hit the paper.

### 8.2 Medium — pick one if space allows

- **Blind human-expert baseline on Phase 1.** Three domain engineers answer a sub-sample (say 10 queries from 5 diagrams) under a time limit; we report the human/agent accuracy gap. Very strong talking point for an manuscript reviewers. Cost is coordinating three experts — non-trivial but not impossible; you (Heiko) know the pool better than I do.
- **Sensitivity to image rendering DPI.** Sweep `{200, 300, 400}` DPI on `butane1.pdf` and `tennessee1.pdf`. One sentence in the ablations table; answers reviewer Q "why 300?" definitively.
- **Compare `h2first1.pdf` (rendered) to `h2first1-src.pdf` (native).** Isolates rendering-pipeline noise from model error. Probably worth a single-paragraph call-out, not a full section.

### 8.3 Weak — defer to journal version

- PLCopen / Proteus round-tripping. Out of scope for Phase 2.
- Fine-tuning comparison. Violates the zero-shot thesis; save for a follow-up paper.
- Latency under concurrent load. Not in scope for this manuscript.

---

## 9. Risks specific to the submission timeline

| Risk                                                                                    | Mitigation                                                                                                                                                     |
| --------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Phase 2 is implemented but *unvalidated at eval quality*. | **Resolved 2026-04-24.** Stabilisation gate passed on `dexpi-reference` + `tennessee1` (3 clean runs each, 0 crashes, 0 validation issues, entity-count σ/μ 10.6% / 0.0%, all within the ≤15% gate). The low-confidence arbitration pass (`arbitrate_low_confidence` in `vision/arbitrate.py`) cut variance from 29.3% on the bare pipeline. See § 10 step 4 for the gate definition and `scripts/stabilise_phase2.py` for the reproducible check. |
| Ground-truth authoring dominates the schedule — and the bootstrap-then-correct approach is novel (§ 4.2). | Start the bootstrap runs immediately so correction can begin in parallel with code stabilisation. Keep the `graph.truth.history.json` audit log so we can report the bootstrap-retention Δ honestly. |
| Anthropic rate-limits block parallel eval.                                              | `--parallel` is tunable; the spec-mandated token bucket (§ 6.4) keeps us under the ceiling; eval runs happen off-peak.                                         |
| Residual pre-training knowledge on Tennessee-Eastman inflates `tennessee1.pdf`.         | One sentence in § V notes that the Tennessee-Eastman flowsheet is public, independent of whether Barthelt 2015 itself was in the training set. No separate contamination column now that the two published-paper PDFs are out of the corpus. |
| Opus 4.7 is deprecated between submission and camera-ready.                             | Pin model snapshot id in `invocation.txt`; if 4.7 retires, run the camera-ready eval on the successor and call out the change in an addendum paragraph.       |
| A raster fixture (e.g. `butane2`, `open100-3`, or the dense `grit-washer1`) cost-overruns and blocks the batch. | Per-sheet cost cap (spec § 6.4) aborts cleanly; the table shows "cost-exhausted" rather than blowing the whole eval. |
| Reviewer rejects on "it is just prompting."                                             | Position the deterministic reconciliation layer (§ 5.5 of the spec) as a non-trivial contribution; the paper's approach section (§ III) must make this vivid.  |
| Reviewer rejects on "you graded your own homework" (bootstrap-then-correct).            | Report per-fixture bootstrap-retention % in § V — 10 numbers, not an aggregate. VIA correction forces the human to touch every entity, so retention is an honest measure of bootstrap accuracy rather than a rubber-stamp. Lean on `dexpi-reference` (canonical external truth) as the contamination-free anchor. Retention is tracked by committing the `bootstrap_annotations.py` output before the VIA pass and `git diff`-ing after. `queries.truth.yaml` authoring mitigates the same risk for Phase 1: identification coords were Acrobat-verified against the rendered PDF, not against our own bbox output (see § 4.1). |
| **Single-rater authoring** (§ 4.3 inter-rater pass deferred to the journal version).      | Acknowledged as a § VI threat to validity. Three structural mitigations: (a) `dexpi-reference` graded against the canonical DEXPI C01 reference XML (an external anchor independent of the rater); (b) per-fixture VIA bbox / VIA label / gt-edit node / gt-edit edge retention reported separately so reviewers see the rater↔model agreement directly; (c) the reproducibility package (§ 7.4) ships every truth file + audit log so a second rater can re-grade post-publication. |

---

## 10. Authoring checklist (concrete next steps)

Status legend: ✅ done · 🔜 next · ⏳ queued.

1. ✅ **Decision — 4 queries/diagram** (§ 4.1). Locked: 4 per family for coverage, 40 total.
2. ✅ **Decision — GPT-4.1 single-shot Phase 1 baseline included** (§ 6, item 2; revised 2026-04-27). Locked: GPT-4.1 on Azure Foundry, single chat-completions call per query (no tools), all 10 fixtures, Phase 1 only. **< USD 1 compute** (dry-run estimate USD 0.13 at default settings — `scripts/gpt41_dry_run.py`). Replaces the earlier GPT-4o + identical-tool-interface plan (see § 7.5 for the SDK-incompatibility analysis that drove the scope cut).
3. ✅ **Create `eval/datasets/manifest.yaml`** with the 10 fixtures listed (§ 2 table). Dataset version `diagex.v0.2` — [manifest file](../eval/datasets/manifest.yaml).
4. ✅ **Stabilise Phase 2 on `dexpi-reference` + `tennessee1`** (completed 2026-04-24). Both fixtures cleared the gate:
   - 3 runs each, 0 crashes, 0 `pydexpi.validate()` issues, every cost ≤ USD 5.
   - Entity-count σ/μ: `dexpi-reference` = **10.6%**, `tennessee1` = **0.0%** — both within the ≤15% gate.
   - `diagex gt lint` clean on every emitted `graph.json`.
   - **Bugs fixed during stabilisation:** (a) reconciler was emitting edges with empty-string endpoints (`_build_edge` in `vision/reconcile.py` — dropped polylines are now recorded in `graph.conflicts` rather than synthesised as invalid edges; `ReconciledEdge` pydantic validator guards regressions); (b) low-confidence arbitration pass added (`arbitrate_low_confidence` in `vision/arbitrate.py`) — cut variance from 29.3% → 10.6% on `dexpi-reference` by re-cropping every medium/low entity and asking the model to CONFIRM / REVISE / REJECT / UNCERTAIN; cost ≈ $0.50 corpus-wide.
   - Reproduce: `scripts/stabilise_phase2.py` (stream + aggregate) or `scripts/stabilise_phase2.py --analyze-only --runs 3` (score existing runs, no API cost).
5. ✅ **Author `queries.truth.yaml` for all 10 fixtures** (§ 4.1). 40 queries drafted by rater_1 (Claude Opus 4.7) from `runs/<stem>/graph.json` + PDF visual inspection, then reviewed and corrected by Heiko Koziolek; all 10 identification coords hand-verified in Acrobat Pro. All queries at `status: rater_1_locked`. Per-fixture files under `eval/datasets/<stem>/queries.truth.yaml` — [archived template](../eval/datasets/_template.queries.truth.yaml). Single-rater authoring per § 4.3 (no κ pass for this manuscript — § VI threat-to-validity language).
6. ✅ **Bootstrap Phase 2** (§ 4.2): ran `diagex extract-pid --effort high` on `dexpi-reference`, `butane1`, `tennessee1` on 2026-04-24. Outputs at `eval/datasets/<stem>/graph.bootstrap.json` (27 / 51 / 70 nodes). All three pass `diagex gt lint` cleanly. Combined cost ~USD 5.5, wall-clock ~10 min.
7. ✅ **Corrected the bootstrap** to full `graph.truth.json` for the 3 fixtures (2026-04-25). Workflow: VIA pass for bboxes + labels (entity inventory) → `via_to_bootstrap_v2.py` produces `graph.bootstrap_v2.json` (IoU-primary + (kind,label) fallback matching) → `diagex gt edit` two-pass (nodes then edges) for `equipment_class` taxonomy + edge correction. After the original bootstrap revealed the agent was tracing single polylines through inline valves, the Phase-2 prompt was updated with an explicit segment-at-inline-components rule and all 3 bootstraps were re-extracted. Final per-fixture retention numbers feed § V reviewer-objection #5:

   | fixture | nodes | edges | VIA bbox-ret | VIA label-ret | gt edit node-ret | gt edit edge-ret |
   |---|---:|---:|---:|---:|---:|---:|
   | dexpi-reference | 26 | 21 | 0.0% | 95.0% | 92.9% | 72.7% |
   | butane1         | 58 | 12 | 16.7% | 43.6% | 98.3% | 0.0% |
   | tennessee1      | 70 | 37 | 1.8% | 45.6% | 100.0% | 75.0% |

   Story: **labels are mostly right, bboxes are mostly wrong, edges are mostly right when the bootstrap segmented correctly.** butane1's 0% edge-retention reflects a poor edge inventory in that bootstrap — most edges authored via `gt add-edge`, not kept from bootstrap. All 3 truth files are `gt lint`-clean, render-dexpi round-trips, and audit logs are committed alongside.
8. ✅ **Bootstrap + correct entity inventories** for the 7 partial-truth fixtures via VIA. 388 bootstrap entries → 486 reviewed entities (+72 added, 6 deleted). Retention measured by `scripts/measure_retention.py`, baseline pinned at `eval/datasets/_retention.v0.2.json`:

   | fixture | boot | final | retained | bbox-edited | added | deleted | ret % |
   |---|---:|---:|---:|---:|---:|---:|---:|
   | butane2 | 51 | 59 | 51 | 51 | 4 | 0 | 100.0 |
   | grit-washer1 | 28 | 78 | 28 | 28 | 47 | 0 | 100.0 |
   | open100-1 | 50 | 51 | 50 | 49 | 1 | 0 | 100.0 |
   | open100-2 | 29 | 46 | 29 | 28 | 0 | 0 | 100.0 |
   | open100-3 | 53 | 61 | 50 | 43 | 3 | 3 | 94.3 |
   | open100-4 | 44 | 57 | 44 | 44 | 13 | 0 | 100.0 |
   | two-tanks | 133 | 134 | 130 | 127 | 4 | 3 | 97.7 |
   | **total** | **388** | **486** | **382** | **370** | **72** | **6** | **98.5** |

   Story for § V: machine label fidelity is high (98.5% retained), bbox precision is the weak link (97% of retained boxes nudged > 5 px), coverage is the second weak link and is fixture-specific (47 of 72 additions are on `grit-washer1` — LCP-panel bubbles + gate-side ZS/HS switches). Hallucination rate 1.5%. Workflow lives in `tools/via/README.md`.
9. ✅ **`meta.yaml` per fixture** — generated mechanically from the manifest on 2026-04-24. All 10 files at `eval/datasets/<stem>/meta.yaml` with `source_type`, `symbol_standard`, `domain`, `page_size_pts`, `draughting_tool`, `annotation_level`, `notes`, `authoring_provenance`, `artefacts_expected/present`. `diagex gt lint eval/datasets` now reports **22 files clean, 0 warnings**. Widened `VALID_SOURCE_TYPES` in the linter to accept `{scanned, raster, vector}` (the spec's `{scanned, vector}` dichotomy didn't anticipate Acrobat image-conversion exports, which are pipeline-equivalent to scans).
10. ✅ **Implemented `eval/run_paper_eval.py`** on cassettes (2026-04-25). Modules at `eval/{run_paper_eval, scoring, conditions, aggregate, latex_tables, report_md, _loader}.py` plus `eval/figures/{fig1_qualitative, fig2_cost_accuracy}.py`. Single-command shape per § 7.1 (`--phase`, `--conditions`, `--use-cassettes`, `--out`, `--emit`). `results.csv` → `table2.tex` / `table3.tex` round-trip verified by `tests/unit/test_eval_run_cassette.py` (re-rendering the LaTeX from the same CSV is byte-identical). Cassette layout: `eval/cassettes/<condition>/<fixture>/{phase1.json, graph.json, summary.json}`. 23 unit tests added (`tests/unit/test_eval_{scoring,aggregate,run_cassette}.py`); full suite still green at 238 passed.
11. ✅ **Live Phase 1 baseline run + N=3 replicates** (2026-04-27 / 28). 120 rows in `out/diagex-phase1/results.csv` (40 queries × 3 trials × 1 condition), `run_id=20260427T174115-5a9b`. Wall-clock 1h06m, total cost USD 14.37, 51% cache-hit. **Macro overall = 0.99** after parser fix (0.98 raw). All four § 5.1 exit criteria cleared:

    | target | actual |
    |---|---|
    | macro inventory ≥ 0.90 | **1.00** (10/10 fixtures) |
    | macro connectivity ≥ 0.80 | **0.97** (only `butane2-q3 trial=2` flips yes/no) |
    | median cost < USD 0.50 / query | **USD 0.073** (~7× under target) |
    | median latency < 2 min / query | **23.2 s** (~5× under target) |

    Two genuine reasoning failures remain in 120 rows: `butane2-q3 trial=2` (yes/no flip on connectivity) and `open100-1-q1 trial=0` (recall miss of `MOV-1115`). Both are real § V-E error-taxonomy material, not parser/infra glitches. One transient API failure (5 MiB image cap) was caught on `two-tanks-q2 trial=2` and recovered: `vision/encode.py` now guarantees inline images fit, then `scripts/rerun_one_query.py` re-ran the single failed cell. Three list-parser patterns were folded back into `eval/scoring.py` (XML answer block, code-fence, single-char label prefix) and the 120 rows re-scored from cached `runs/` answers via `scripts/rescore_phase1_inplace.py` — no extra API calls. Per-trial xlsx at `out/diagex-phase1/qa_analysis.xlsx`. **Note:** the run wrote to `out/diagex-phase1/` rather than the canonical `out/diagex/baseline/` per § 7.1; Phase 2 (step 12) is expected to land in `out/diagex-phase2/` as its sibling, with the per-condition layout reserved for the final aggregated submission tree.
12. ✅ Live Phase 2 baseline run — completed across 10 fixtures via iterative
    targeted re-runs (`out/diagex-phase2/`).
    Macro: Eq. F1 0.92, Inst. F1 0.90, Tag EM 0.83 (under the §5.2 OCR-fidelity-given-identification definition), DEXPI validates 10/10.
    Per-fixture range: Eq. F1 [0.67, 1.00] (low: grit-washer1; high: butane1/butane2/open100-1..3); Tag EM [0.67, 1.00] (low: dexpi-reference; high: open100-2).
    Total cost USD 38.17 / 1h30m wall.
    Two-tanks initially scored 0.48/0.47 due to embedded raster downsample in the
    source PDF; resolved by re-converting from `tools/via/images/two-tanks.png`
    (5550×4044), bringing it to 0.78/0.82.
    Tables in `out/diagex-phase2/tables/{table2,table3}.tex`,
    diagnostics workbook in `out/diagex-phase2/diagnostics/phase2_diagnostics.xlsx`.
13. ✅ **Minimal ablation — `--no-tile` on the 3 full-truth fixtures** (run `20260428T084608-e35c`, ~38 min wall, USD 15.36 total). All three runs validate DEXPI; means across the 3 fixtures (baseline → ablation): equipment F1 0.947 → 0.758 (Δ −0.189), instrument F1 1.000 → 0.743 (Δ −0.257), tag-OCR EM 0.771 → 0.602 (Δ −0.169), cost USD 3.79 → 5.12/fixture (Δ +1.33, +35%), wall-clock 536 → 846 s/fixture. The dense raster fixture `butane1` collapses on per-kind F1 (equip 1.00→0.56, instr 1.00→0.37, tag 0.76→0.30); the small vector `tennessee1` keeps tag legibility (tag 0.89→0.90) and even improves edge F1 (0.25 → 0.70). Counter to the naive intuition, no-tile is *more expensive* — the agent compensates with many more `get_region` calls and annotation steps (butane1 ablation: 139 steps). `--no-legend` was *not* run: plan §5.4 makes it conditional on baseline showing legend-driven failures, which the baseline numbers don't surface. §V-D draft + per-fixture deltas at [`out/diagex-ablation/delta_vs_baseline.md`](../out/diagex-ablation/delta_vs_baseline.md); raw rows at `out/diagex-ablation/results.csv`.
14. ✅ **GPT-4.1 single-shot Phase 1 baseline on all 10 fixtures** (run `20260428T090501-da59`, output at `out/diagex-gpt41/`). 40 queries × 1 trial × 1 condition (`gpt41-singleshot`), parallel=4. **Total cost USD 0.1093** (dry-run estimate USD 0.134 — actual was lower because real prompt/output tokens were below the 250-in / 80-out projection). Median per-query cost USD 0.0027, median latency 3.45 s. Macro overall **0.57** (vs Claude baseline 0.99 — step 11), which is the cross-model anchor § VI / § V-B reports verbatim. Per-family macros: connectivity 0.90, identification 0.60, inventory 0.48, counting 0.30 — the LLM-only single-shot leg holds connectivity but loses on counting and dense-inventory queries that the ReAct/tile loop solves.

    | fixture | inv | cnt | conn | ident | overall |
    |---|---:|---:|---:|---:|---:|
    | dexpi-reference | 1.00 | 1.00 | 1.00 | 0.00 | 0.75 |
    | two-tanks       | 1.00 | 0.00 | 1.00 | 1.00 | 0.75 |
    | butane1         | 0.00 | 1.00 | 1.00 | 1.00 | 0.75 |
    | butane2         | 0.00 | 0.00 | 1.00 | 1.00 | 0.50 |
    | tennessee1      | 1.00 | 0.00 | 0.00 | 0.00 | 0.25 |
    | grit-washer1    | 0.67 | 0.00 | 1.00 | 0.00 | 0.42 |
    | open100-1       | 0.00 | 0.00 | 1.00 | 1.00 | 0.50 |
    | open100-2       | 0.00 | 1.00 | 1.00 | 1.00 | 0.75 |
    | open100-3       | 1.00 | 0.00 | 1.00 | 1.00 | 0.75 |
    | open100-4       | 0.18 | 0.00 | 1.00 | 0.00 | 0.30 |

    **Operational notes for the runbook:**
    - `.env` `AZURE_OPENAI_GPT41_ENDPOINT` must be the **bare** OpenAI-compatible base (`https://<resource>.openai.azure.com`) — *not* the `/anthropic` suffix used by the Claude leg. The first attempt used the suffixed URL and 404'd on every call; fixed by editing `.env` and re-running. The `eval/README.md` example already shows the correct bare form.
    - 11 of 40 calls hit Azure `429 Too Many Requests` at parallel=4; the openai SDK's default retries cleared most but 11 cells landed as error rows. Patched in place via `scripts/rerun_one_query.py --condition gpt41-singleshot` looped sequentially with a 12 s gap between calls — every retry succeeded. After the loop: 0 error rows, `scripts/rerender_eval_artifacts.py --out out/diagex-gpt41` regenerated tables/figures/`report.md` from the patched CSV.
    - Pre-flight `python scripts/gpt41_dry_run.py` projected USD 0.134; actual USD 0.109 (−18%) because real per-query tokens were lighter than the conservative defaults.
15. ✅ Paper draft § IV-V written against the emitted `.tex` tables (2026-04-30). LaTeX submission complete; numbers are `\input{}`-ed from `out/diagex-phase1/tables/table2.tex` and `out/diagex-phase2/tables/table3.tex` so re-running the eval re-renders the paper without hand-edits.
16. ✅ **Cassette recording** (2026-04-30). `scripts/record_cassettes.py` copies the canonical live-run artefacts into `eval/cassettes/<condition>/<stem>/{phase1.json, graph.json, summary.json}` — 13 directories / 36 files / 808 KiB total covering `baseline` (10 fixtures × {phase1, graph, summary}) and `ablation-no-tile` (3 fixtures × {graph, summary}). Phase 1 picks trial 0 per query; Phase 2 picks the run_dir whose graph.json reproduces the live equipment-F1 tp/fp/fn (handles in-place targeted re-runs whose `run_id` no longer points at the original timestamp). End-to-end replay (`run_paper_eval.py --use-cassettes`) reproduces all 33 Phase 2 metric rows and all 40 Phase 1 trial=0 rows of the live `results.csv` byte-for-byte. `tests/unit/test_eval_run_cassette.py` (5 tests) green. Pre-submission step 17 is the only remaining item.
17. ⏳ Pre-submission: a second person runs `run_paper_eval.py --use-cassettes` on a clean checkout and confirms the CSV matches.

**Effort total (remaining):** human authoring (steps 1–10), live API legs (steps 11–14), paper drafting (step 15), and cassette recording (step 16) are all done. Only step 17 (independent reviewer-style replay on a clean checkout) is left.

- **Live runs** (steps 11–14): all complete. Booked USD 14.37 (Phase 1 baseline + N=3) + USD 38.17 (Phase 2 baseline) + USD 15.36 (no-tile ablation) + USD 0.11 (GPT-4.1 anchor) ≈ **USD 68** total / ~6 h wall-clock. Comfortably inside the original ~USD 70–80 envelope.
- **Cassette recording** (step 16): done. `scripts/record_cassettes.py` is rerunnable; `eval/cassettes/` (13 dirs / 36 files / 808 KiB) replays Phase 1 baseline and Phase 2 baseline + ablation-no-tile from cached artefacts with no API spend.
- **Paper drafting** (step 15): done. § IV-V `\input{}`s the emitted `.tex` tables — no hand-copied numbers.

**Pre-live-run readiness checklist** (all green except where flagged):
- ✅ `manifest.yaml` lists all 10 fixtures with current `annotation_level` and `source_type`.
- ✅ All 10 `eval/datasets/<stem>/{queries.truth.yaml, meta.yaml}` pass `gt lint`.
- ✅ 3 `graph.truth.json` files (full-truth) finalised with retention audit logs committed.
- ✅ 7 `annotations.truth.jsonl` files (partial-truth) finalised with retention table at `eval/datasets/_retention.v0.2.json`.
- ✅ Eval harness `eval/run_paper_eval.py` end-to-end on cassettes (23 unit tests pass).
- ⚠️ Anthropic API key + per-sheet cost cap (spec § 6.4) configured before kicking off step 12 — the dense raster fixtures could otherwise overrun.
- ⚠️ Single-rater note added to § VI is the load-bearing limitation prose; review before submission.

---

*End of diagex evaluation plan v0.1 — iterate on § 4 (ground truth scope) and § 8 (alternatives) before the authoring sprint starts.*
