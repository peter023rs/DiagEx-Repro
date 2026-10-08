# DiagEx symbol detection and UI fork: AI implementation handoff

## 1. Goal and agreed scope

Fork DiagEx-Repro into a smaller application that detects symbols in P&IDs and lets the user inspect the results in the existing workbench UI.

The user wants the existing UI design and all applicable viewing functions. The user explicitly confirmed **viewing only**: remove manual symbol editing as well as human review, approval, rejection, sign-off, and graph-building workflows.

Target journey:

**Configure models -> upload drawing -> detect legends and symbols -> view source-aligned results -> reopen or download results.**

Reuse and simplify the existing implementation. Preserve its visual design, English/Chinese language support, and useful interactions. This is a scope reduction, not a frontend rewrite or a new detector research project.

This document is the implementation specification. It was originally written before application changes; the implementation status below records the completed fork work.

### Implementation status (2026-09-29)

The detection-only vertical slice, dependency extraction, viewer parity, runtime pruning, and setup documentation are implemented in this workspace. The baseline descriptions later in this document describe the original architecture, not the current module locations.

- `src/diagex/extractors/symbol_detection.py` runs the retained evidence-v2 legend/perception pipeline and stops before graph processing. Completed compatible evidence can be reused in a new run; fresh runs bypass the applicable caches.
- `src/diagex/detection/` owns the version-1 bundle writer, immutable reader, detection result contract, and independent symbol taxonomy. Saved observations, candidates, diagnostics, and native text remain distinct. Reading and downloading do not create review decisions or call a model.
- The workbench exposes detection-only jobs, read-only results, allowlisted JSON downloads, verified source attachment, source pages, and detail crops. Removed graph/review payloads and mutation endpoints are rejected by the server.
- The existing English/Chinese UI retains configuration, uploads, progress, recent runs, filters, selection, zoom/pan, comparison/background modes, panels, and downloads. PDF rotation and saved scan frames preserve overlay coordinates.
- Hand-maintained graph/review/export runtime and unused research/training scripts are removed. Generated/vendored files, attribution, historical research data, and pre-existing local `workflows/` work are preserved and excluded from distributions. The retained local `runs/` module is included in the package; the root-only runs ignore rule no longer hides its source.
- The public CLI contains `detect`, `web`, and `version`. Installation, provider configuration, artifacts, reuse, and limitations are documented in `README.md`.

Validation completed:

- `python -m pytest tests/unit -o addopts='' -q`: **242 passed**, with five upstream PyMuPDF SWIG deprecation warnings.
- `ruff check .`, JavaScript syntax checks, and `git diff --check`: passed.
- Deterministic HTTP integration uploads the public `two-tanks.pdf` fixture. Pipeline tests replay model responses and verify completed-run reuse, fresh execution, guards, and stopping before graph processing.
- Browser smoke covers upload -> job -> results, both languages, filters, crops, comparison/background controls, panels, downloads, and desktop/narrow widths. It verifies no review/graph requests, unchanged detection bytes, and no review directory. Desktop screenshots were visually inspected; evidence is in ignored `output/detection-smoke/`.
- An sdist and a wheel built from that sdist succeeded. The wheel includes the three reference symbol libraries and retained run helpers and excludes retired subsystems. Runtime imports, CLI help, and the full browser smoke passed from the installed wheel in a separate temporary environment outside the checkout.
- Clean-install testing identified an undeclared direct `httpx` dependency and an incompatible unbounded SDK upgrade. The package now declares `httpx` and bounds Anthropic to the tested SDK minor version.

Remaining validation: no live provider smoke or detection-accuracy claim is made because no provider credentials were configured. Browser and pipeline checks use deterministic model substitutes. The pre-existing `graphify-out/` map describes the old architecture and should be regenerated before using it for current dependency analysis. No commit or publication was performed.

### Missing-symbol response-contract fix (2026-09-30)

Inspection of the saved 2401 drawing found a compressor candidate withheld because the model's `compressor_type: screw` field was rejected by the strict candidate-response schema. A filter candidate had the same failure with `filter_type`. The new runs had reused these cached outcomes; their raw detections were identical to the older saved detections.

The perception contract now explicitly supports equipment subtype fields from the retained taxonomy and preserves them in detection attributes. Candidate identity, geometry, and unknown fields remain constrained. A separate response-contract revision lets an explicitly started resume job retry older crops with candidate-validation failures while reusing successful crops. New checkpoints record that revision, so persistent failures are not automatically retried on every resume. Existing published bundles remain unchanged.

The exact saved compressor response now passes through parsing and native-coordinate projection with the original box `(2265, 2061, 270, 67)`. Five regression cases cover subtype retention and selective cache retry. The full suite passes with **247 tests**; lint and whitespace checks pass. This is a saved-response replay, not a new live provider run. Producing an updated result still requires starting a detection job with resume enabled.

### Baseline and evidence

Model-selection follow-up (2026-09-30): provider/model inputs remain editable under every preset. Editing switches to custom settings; explicit model IDs override server preset defaults. The browser loads image/tool-capable suggestions from OpenRouter's public model catalog without credentials and supports manual IDs when offline. Reinspection can use a separate model or default to the vision model. The full suite passed with 253 tests; the browser smoke verifies catalog filtering, failure recovery, both languages, responsive layout, and delivery of the chosen model IDs to the job runner.

- Repository: `peter023rs/DiagEx-Repro`.
- Inspected on 2026-09-28; HEAD: `f458f4cfc9c17194e8a6d8de4901184bc45821ba`.
- Findings below were checked against local source after using the existing graph for navigation. Function names are more durable references than line numbers.
- The working directory contains additional local work, including `src/diagex/workflows/` and `tests/unit/test_run_module_seams.py`. `src/diagex/runs/` also exists locally but is not in this HEAD's tracked file list. Do not assume these modules are available in a fresh clone, or overwrite/delete them in this workspace. Check the actual fork baseline first.
- This handoff does not assert that a live model run or the existing test suite passed. Implementation must establish its own baseline.

## 2. Required user-facing functions

### A. Workbench and configuration

Keep the existing application shell, branding treatment, typography, colors, cards, spacing, buttons, responsive layout, connection indicator, notifications, and English/Chinese switch.

Keep these working functions:

- Provider selection, API endpoint configuration, API key input and show/hide control, and environment-key fallback. Preserve the provider support already implemented in the source.
- Vision-model selection and relevant model profiles. Keep model suggestions configurable rather than treating today's model IDs as permanent requirements.
- Reasoning mode and effort where they affect symbol detection or legend extraction. Keep the model setting used for bounded symbol reinspection if the retained pipeline uses it; remove controls used exclusively by relationship or cross-sheet reasoning.
- File chooser, drag/drop upload, PDF/PNG/JPEG/TIFF acceptance, upload progress, file details, replace-file action, and useful validation messages. Preserve current loader capabilities; multi-page PDF support exists, whereas the image loader currently yields one image page, so multi-frame TIFF support is not implied.
- Resume compatible artifacts versus start a fresh run. Explain cache reuse using detection terminology.
- One primary **Detect symbols** action, including the legend stage. Force the evidence-v2 detection workflow on the server too.
- Job state, elapsed time, activity indicator, incremental log, auto-scroll, copy log, error details, and recovery instructions.
- Completed/partial detection summary with model, symbol-observation count, candidate/uncertainty count where available, legend count, token/cost information where recorded, and run location. Count fields must distinguish observations from unique physical symbols.
- Recent runs, search by drawing/run/model, refresh, source-file reattachment with source-hash verification, and reopening saved detection results without model calls.

Adapt labels such as “Start extraction” and “Review legends & symbols” to **Detect symbols** and **View results**. Remove reviewer-name inputs. Remove legacy-engine selection, graph-start/build actions, graph-specific metrics, and connection-only process/rules inputs after checking that no retained detection call consumes them.

### B. Read-only results workbench

Reuse the existing detection viewer and port applicable presentation features from the graph review viewer. Keep:

- Source drawing, page selection/navigation, visible page number and read-only page role.
- Symbol bounding boxes aligned with the actual detection coordinate frame; click a box to select its result.
- Result list and inspector that stay synchronized with selection, page changes, and search.
- Zoom in/out, zoom percentage, pan, fit page, focus selected symbol, and optional automatic focus on selection.
- Clear selection highlighting and high-resolution source detail crops, especially for small vector symbols.
- Legend browser with thumbnails, labels, classes, descriptions, source information, and filters for drawing symbols, text definitions, and reference-library entries.
- Symbol search by tag, class, ID, or diagnostic reason; page and type filters; machine-confidence/uncertainty filters. Default to showing results, not a pending approval queue.
- Read-only inspector fields: label/printed tag, kind/class, confidence, bounding box, page/tile, attributes, source text references, candidate provenance, and diagnostic reasons where available.
- The existing comparison presentation: source beside source-plus-detections, side-by-side/stacked layouts, full/dimmed/hidden background modes, and collapsible list/inspector panels. These are adaptations from `review/static/`, not features already supplied by the detection viewer alone.
- Read-only symbol inventory and evidence/candidate list using available detection/native evidence. Omit graph-only columns such as connection counts. Do not invent node assignments when only text candidates exist.
- Reload, return to the workbench, English/Chinese labels, accessible names, keyboard-operable controls, empty-result messages, and partial/error states.
- Download the machine detection bundle and legend data directly. This is a small adaptation to the existing UI, with no completion or approval gate.

Remove all editing and review controls: add/move/resize/delete symbols, change classes/tags/legend entries, confirm/reject/bulk decisions, undo edits, reviewer identity, page-coverage checkbox, approve/waive page, review queue, review-completion progress, “Finish & export,” “Build graph,” and “Build draft.”

Viewing and downloading results must not create a `review/` directory, modify detection content, or call a model. Uploading and starting a detection job remain normal workbench actions.

### C. Detection behavior

Keep the existing evidence-v2 legend and raw-symbol detection behavior:

- Multi-page PDF loading, image loading, render sizing, scan preprocessing, and rotation/coordinate handling.
- Native PDF text and vector-path extraction and deterministic page-role classification.
- Project legend discovery, extraction, source-row thumbnails, abbreviation tables, built-in symbol library, and compatible legend caching.
- Native physical-symbol candidates with stable identities and source geometry.
- Deterministic overlapping crop coverage and model image encoding.
- Vision-language classification into equipment, instruments, and off-page connectors (`opc`), with subtype/tag/attribute fields already supported by the source taxonomy.
- Candidate-bound geometry, strict response validation, non-symbol/uncertain outcomes, bounded repair/reinspection, timeout/failure guards, and preservation of completed work.
- Checkpoints, source/config/model/version compatibility checks, diagnostics, model usage accounting, and resumability.

Keep the ordinary raster/image detection path. Optional externally supplied raster proposals, broad-raster experiments, and detector training/evaluation are outside the first fork scope. Disable/remove those opt-in routes deliberately instead of treating their unconfirmed proposals as normal detections.

## 3. How detection currently works

### Entry point and stopping boundary

`src/diagex/web/server.py` owns `Workbench.start_extraction()` and `_run_extraction()`. The workbench invokes `run_pid_extract()` in `extractors/pid.py`, which routes evidence-v2 requests to `run_pid_evidence_extract()` in `extractors/pid_evidence.py`.

The usable existing boundary is:

```python
engine = "evidence-v2"
stop_after = "detection"
```

In `run_pid_evidence_extract()`, the detection return occurs **before** `fuse_objects()`. It writes `detection.json`, `legend.json`, `result.json`, cost/reuse information, and checkpoints. Its result object currently carries an empty `ReconciledGraph` and stores the detection count in a field named `dexpi_stats`. Those are compatibility leftovers to remove from the fork's result contract.

Merely setting this flag is a good first working slice, but is not the finished smaller fork: imports, UI routes, result types, and downstream modules still need separation.

### Detection stages to preserve

1. **Load and inspect.** `vision/loader.py` (`load`, `iter_pages`) and `vision/evidence.py` (`extract_page_evidence`, `classify_page`) provide rendered pages, native text, paths, and page roles. `_inspect_pages()` coordinates this for evidence-v2.
2. **Resolve the legend.** `extractors/pid_legend.py:resolve_evidence_legend()` uses the inspected legend-page roles, delegates extraction to `resolve_legend()`, and merges native abbreviation tables. With no detected legend page, it can use the built-in pack. Preserve the distinction between no project legend and a failed/incomplete project legend. The latter can stop perception or make results partial.
3. **Select usable legend context.** Uncertain/rejected machine legend rows remain visible in output but are excluded from interpretation rules. `vision/legend_context.py` selects relevant examples and definitions for perception.
4. **Propose native symbols and cover the page.** `vision/symbol_candidates.py:symbol_candidates()` uses `vector_geometry.py` to form physical glyph candidates. `vision/tiling.py` provides `AspectAwareStrategy`, `tile`, and `ownership_core`; `vision/views.py:ViewProvider` tracks view geometry and projection.
5. **Classify each crop.** `_run_perception()` calls `vision/perception.py:perceive_tile()`. This is structured vision-language inference with native evidence and legend context, not simply a trained object-detector weight file. Preserve the candidate identity/geometry constraints and `DetectionRecord` representation.
6. **Validate and recover.** Native candidates receive symbol, non-symbol, or uncertain outcomes. Free-form proposals are handled separately. The current `SymbolPerceptionConfig` defines a 6,000-token first pass, a 16,000-token reasoning allowance, request/time limits, and bounded failure handling. Reuse the configuration and tests rather than duplicating constants in the UI.
7. **Persist and display.** Save immutable machine observations, page status, candidates, diagnostics, legend content, and provenance. Stop before object fusion, contextual composite resolution, line topology, relationship solving, and graph/DEXPI export.

### Important interpretation rules

- `detection.json` contains pre-fusion observations. Overlapping crops may produce repeated observations. The first fork preserves this behavior and labels counts honestly; it does not add a new deduplication algorithm.
- Native candidates, uncertain/rejected proposals, and validated model detections are different categories. Display them separately. Never promote candidates automatically just because human review was removed.
- A machine `non_symbol` outcome is detector logic, not a human rejection workflow. Keep it.
- `perception.review.json`, the bundle's `reviews` field, and `candidate_reviews` contain machine diagnostics as well as data formerly shown to reviewers. Preserve that evidence; names alone are not a reason to delete it.
- Removing review does not guarantee detection accuracy. Completion means processing finished, not that an engineer verified the output.

## 4. Code to retain, adapt, and remove

### Retain and adapt these entry points

- `src/diagex/web/server.py`: uploads, request configuration/redaction, jobs/logs, run discovery, source linking, page/crop rendering, local server. Replace review-specific result access with a read-only detection reader.
- `src/diagex/web/static/index.html`, `app.js`, `styles.css`: existing dashboard design and interactions; prune graph/review controls and handlers.
- `src/diagex/web/static/detection.html`, `detection.js`, `detection.css`, `detection-i18n.js`: primary basis for the read-only results viewer.
- `src/diagex/review/static/index.html`, `app.js`, `styles.css`: source for comparison/layout/background, inventory, and panel controls. Port useful presentation behavior before removing this directory; do not retain the review state machine.
- `src/diagex/web/model_profiles.py`, `config.py`, `llm/`, and `ui/progress.py`: keep configuration, transports, relevant prompts, metering, and progress required by the retained path.
- `src/diagex/extractors/pid_evidence.py`: extract the detection stages into a focused entry point. Remove downstream imports from that entry point.
- `src/diagex/extractors/pid_legend.py`, `legend_rows.py`, `vision/legend_models.py`, `legend_tables.py`, `legend_context.py`, and `src/diagex/assets/symbols/`: retain the applicable legend pipeline and packaged library.
- `src/diagex/vision/loader.py`, `preprocess.py`, `encode.py`, `evidence.py`, `models.py`, `tiling.py`, `views.py`, `symbol_candidates.py`, `vector_geometry.py`, `perception.py`: retain detection and rendering dependencies. Confirm transitive imports before pruning neighboring modules.
- `src/diagex/extractors/evidence_checkpoint.py`: current checkpoint/atomic-write implementation. If the chosen baseline has migrated it into `runs/`, use that baseline's authoritative implementation instead of creating a duplicate.
- `src/diagex/cli.py`: keep `diagex web` working; provide a detection-only CLI action by adapting the current extraction command. Document the final command after implementation.

### Required dependency extractions before deletion

1. **Bundle writer.** `write_detection_bundle()` lives in `review/detection.py` and is imported by the detection pipeline. Move it into the retained detection/artifact layer unchanged initially.
2. **Read-only data access.** `Workbench.detection_store()`, `detection_page()`, and `detection_crop()` depend on `DetectionReviewStore`. Replace that dependency with a validated immutable bundle reader. Keep run-directory confinement, source-hash checks, crop bounds checks, and vector re-rendering.
3. **Taxonomy.** `vision/legend_models.py` imports `dexpi_schema.py`, which imports classes from `dexpi.model`. Separate the symbol keys, descriptions, and prompt taxonomy needed by detection from the DEXPI class/export mappings before removing DEXPI. Preserve existing class names and validation behavior.
4. **Legend agent dependencies.** `pid_legend.py` imports `ReactRuntime`, `RunConfig`, and `AgentState`. Retain the agent pieces actually needed by the legend path until those imports and uses are isolated. The old P&ID graph agent being out of scope does not make the entire `agent/` directory immediately disposable.
5. **Result contract.** Replace the graph-bearing `PidExtractionResult` with a detection result that exposes run identity, counts, statuses, model, costs, and artifact paths directly. Update server summaries and CLI output together.
6. **Mixed tests and UI code.** Detection bundle, coordinate, crop, and source-hash tests currently sit beside review tests. Move retained assertions before removing review-specific tests and browser scripts.

### Remove after these extractions pass validation

- Human review servers/stores, revisioned decisions, review actions, approval gates, reviewer metadata, reviewed-graph snapshots, and graph-build-from-review routes.
- Legacy P&ID graph extraction, object fusion/assembly, contextual post-fusion correction, pipe/signal topology, connection acceptance, relationship/page-graph solving, cross-sheet reconciliation, and graph export.
- DEXPI builders, XML/JSON model exporters and validation/codegen machinery, SVG/draw.io graph exporters, once detection taxonomy/imports are independent.
- Query/other extraction commands outside the symbol-detection product, and graph/DEXPI-specific debug report generation.
- Paper reproduction, evaluation/training scripts, publication results, and their dependencies when they are not used by retained tests/runtime. Keep a small licensed fixture set for detector and UI validation.

This is a dependency-based removal list, not a command to delete whole directories at the start. Preserve `LICENSE`, applicable `NOTICE` entries, and retained fixture provenance. Never manually edit auto-generated files or `CHANGELOG.md`.

## 5. Target API and artifacts

### Existing endpoints to keep or simplify

- `GET /api/health`, `GET /api/config`.
- `POST /api/uploads`.
- `POST /api/extractions`, restricted to detection. Reject graph/legacy/reviewed-build payloads instead of accepting hidden capabilities.
- `GET /api/jobs`, `GET /api/jobs/{id}`, and `GET /api/runs`.

### Proposed viewer endpoints

The following names are proposed, not existing APIs:

- `GET /detections?run_dir=...`: viewer page.
- `GET /api/detections?run_dir=...`: immutable results plus display metadata.
- `GET /api/detection-download?run_dir=...&kind=detection|legend`: allowlisted JSON downloads.

Retain/adapt existing `GET /api/detection-page` and `GET /api/detection-crop`. Remove `POST /api/reviews` and `POST /api/detection-review/actions`, plus the old graph review server. Redirecting an old detection-view URL to the new viewer is acceptable; restoring review mutations is not.

### Data contract

Preserve the version-1 detection bundle first:

```text
version, source_sha256
pages[]: page_index, width, height, role
detections[]: id, page_index, tile_id, kind, label,
              bbox {x,y,w,h}, confidence, raw_text,
              attributes, source_text_ids
legend_pack, per_page_status, candidates, reviews
```

`DetectionRecord.bbox` is page-space geometry; model response boxes may be normalized within a crop and must pass through the existing projection logic. Stored page dimensions define overlay coordinates, not preview-image dimensions or PDF point units. Preserve rotation/preprocessing transforms when displaying image and PDF inputs.

Initially retain legacy machine-diagnostic field names for compatibility. A later rename to `diagnostics` requires an explicit schema version and reader migration.

Keep detection/legend bundles, native evidence needed by the viewer, detection checkpoints, diagnostics/stop reasons, source-link metadata, result metadata, and cost/reuse information. No graph or reviewed artifact is a prerequisite to open or download a result.

Use machine execution states such as complete, partial, paused, and error consistently. Replace the current successful detection `quality_status="needs_review"` presentation with a machine-results label; retain uncertainty and incomplete coverage explicitly. An empty fully processed drawing is different from a failed or unprocessed drawing.

Existing detection runs should open without modification. Old graph-only runs can be shown as unsupported by this fork rather than triggering graph reconstruction. Browsing historical data must not replay paid model calls. Preserve matching-run resume and fresh-run separation without overwriting the original results.

## 6. Implementation sequence

1. **Record the baseline.** Inspect current status and project instructions, choose the fork baseline, inventory local-only modules, and start the original workbench. Capture reference views of the dashboard and both existing viewer layouts. Use public fixtures and saved/mock results to record the current detection path. Done when the starting behavior and retained UI are reproducible.
2. **Make one detection-only vertical slice.** Route the primary workbench action through evidence-v2 with `stop_after="detection"`. Expose its bundle in a read-only viewer and enable direct JSON download. Done when upload -> job -> source-aligned results works without review or graph generation.
3. **Extract dependencies.** Move the bundle writer/reader and rendering access out of review; isolate taxonomy, required legend agent code, checkpoint helpers, and detection result types. Done when the retained detection/viewing path imports without review or graph-export dependencies.
4. **Finish UI parity.** Preserve the dashboard and detection viewer styles; port comparison, background, layout, inventory, and panel controls. Remove all review/edit handlers, stale translations, reviewer forms, and unused graph inputs. Done when every retained visible control works in both languages and results are read-only.
5. **Prune the fork.** Remove unused pipelines, commands, assets, dependencies, and tests only after checking imports and packaging. Keep source attribution and fixture provenance. Done when a clean install starts the workbench and does not require removed subsystems.
6. **Validate and document.** Run focused tests, a browser workflow, and a real detection smoke run when credentials are available. Update the fork README with installation, launch, inputs, outputs, and limitations. Report exactly which checks ran and which remain unverified.

Use the existing Python/local HTTP server and plain HTML/CSS/JavaScript architecture. Do not add a frontend framework, database, worker service, authentication system, or orchestration layer for this scope. Keep localhost binding and current credential redaction behavior.

## 7. Acceptance checks

### End-to-end behavior

- A user uploads `tests/p-ids-public/two-tanks.pdf`, selects configuration, starts detection, sees progress, and opens results with the original page and aligned symbol boxes.
- A rotated vector PDF, a raster image/scanned PDF, and a multi-page PDF retain correct page/box/crop alignment. Use existing fixtures where applicable and a small derived test fixture where missing.
- Legend entries and their source crops are visible; no-legend fallback and failed/partial legend handling remain distinct.
- Selection, search, filters, page navigation, pan/zoom/fit/focus, comparison modes, panel visibility, language switch, and downloads work.
- Refresh/reopen/download makes no model calls and writes no review decisions. Starting a new job is the only model-triggering workbench action.
- Reopening a run with the wrong source is rejected; missing source attachment has a useful recovery path.
- Interrupted detection retains completed crops, shows an honest partial/paused state, and resumes compatible work. A fresh run bypasses applicable machine caches.
- Model contract failure, timeout, authentication error, missing library, invalid upload, empty detections, and uncertain candidates produce useful states rather than blank UI or false success.
- Browser network inspection shows no review mutation or graph-build requests. Removed endpoints reject calls even when invoked directly.
- Browsing/downloading leaves the detection bundle byte-for-byte unchanged, and no `review/` directory is created.

### Tests to reuse and adapt

Start with `tests/unit/test_symbol_perception.py`, `test_symbol_response_contract.py`, `test_runtime_guards.py`, `test_legend_context.py`, `test_legend_tables.py`, `test_native_legend_rows.py`, `test_pid_legend_thumbnails.py`, `test_tile_id_resolution.py`, `test_vision_encode.py`, `test_progress.py`, and the relevant checkpoint/reuse tests.

In `tests/unit/test_detection_review.py`, retain the detection-stops-before-fusion assertion from `test_detection_stops_before_fusion_and_reviewed_build_keeps_instances`, and the source/page/crop assertions from `test_detection_http_api_and_vector_detail` and `test_tiny_vector_detail_is_rendered_at_readable_resolution`. Split them from obsolete review assertions.

Adapt `tests/unit/test_web_server.py` for upload, redacted configuration, jobs, run discovery, and source attachment without review handoff. Replace the review smoke path in `tests/browser/run_detection_review_smoke.py` and `detection_review_smoke.cjs` with the retained browser journey.

Use mocked/replayed model responses for deterministic tests. Assert that detection does not call fusion/topology/graph/export functions. Run a live smoke separately if credentials are available; do not claim accuracy from a mocked run. Visually inspect desktop and narrow layouts for clipped controls, horizontal overflow, blurry detail crops, misplaced overlays, and missing translations.

Completion requires working retained behavior, removal of obsolete server capabilities and imports, an installable package, passing applicable lint/tests, and a short report of validation and remaining limitations. Hiding buttons alone is insufficient.

## 8. Prompt to give the implementation AI

> Implement the fork described in `docs/SYMBOL_DETECTION_UI_FORK_HANDOFF.md`. Keep DiagEx-Repro's evidence-v2 legend/symbol detection, workbench design, and all applicable viewing functions. The results viewer must be read-only. Remove human review, manual editing, approval/sign-off, graph building, connectivity extraction, and DEXPI/export machinery after extracting shared dependencies. First inspect the actual baseline and local changes, then implement the smallest end-to-end detection-only slice. Preserve source-aligned geometry, checkpoints/resume, machine uncertainty, provider configuration, and English/Chinese UI. Follow the document's dependency map and acceptance checks. Do not rewrite the UI or silently replace detection with a different model. Deliver the working fork, updated setup instructions, and an honest validation report.
