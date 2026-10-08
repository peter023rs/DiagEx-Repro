# DiagEx symbol detection workbench

Detect legends and symbols in P&IDs, then inspect machine results against the source drawing. This fork retains the evidence-v2 detector, local Python server, and English/Chinese workbench. Results are read-only: there are no editing, approval, graph-building, connectivity, or DEXPI export actions.

## Install and launch

Python 3.11 or newer is required.

```sh
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[dev]'
diagex web --no-open
```

Open http://127.0.0.1:8765. The default bind address is localhost. `--port 0` selects an available port. Select a model profile or custom provider/model, enter an API key or use an environment key, and upload a drawing. Choose **Detect symbols**, then **View results**.

Supported providers: OpenRouter, Kimi, Anthropic, and Azure AI Anthropic-compatible endpoints. Model profiles are suggestions configured in `src/diagex/web/model_profiles.py`; custom model IDs and supported endpoint settings remain editable. The reinspection model is used for bounded symbol reinspection. Keys entered in the workbench remain in server memory and are omitted from job settings and saved run metadata.

The vision presets include **GLM-5.3-Flash** (default), **MiMo-V2.6-Pro**, **Kimi K3**, and **Qwen3-VL-235B** through OpenRouter. Each preset uses the same model for detection and reinspection unless you override it. GLM-5.3 requires reasoning, so its requests retain reasoning even during the fast pass. Qwen3-VL Instruct requests omit unsupported reasoning settings. These are selectable models, not an accuracy ranking; compare saved runs on the same source to evaluate them.

Under **OpenRouter provider routing**, enter comma-separated provider slugs to prefer or exclude providers. For example, exclude `deepinfra`, or prefer `xiaomi` and disable fallbacks to restrict routing to that provider. A provider must actually serve the selected model; availability is not guaranteed. Blank fields keep automatic routing. Routing choices are saved with run settings and participate in cache compatibility. See [OpenRouter provider routing](https://openrouter.ai/docs/guides/routing/provider-selection).

Symbol requests process one page crop at a time and contain at most four images, including reinspection. Small legend thumbnails are combined into a numbered reference sheet with their original entry IDs; auxiliary reinspection crops use separate labeled sheets. The primary source crop and its detection coordinate frame stay unchanged. This addresses provider image-count limits such as `12 > 4` without dropping the selected legend references. Providers with stricter limits can still reject a request; select a compatible route in that case.

Native legend rows are classified in batches of four and split automatically if the provider reports a lower image limit; all row identities and completed classifications are retained. Scanned-legend navigation retains the latest four view images (or the provider's reported lower limit), keeping earlier view metadata and annotations and explicitly asking the model to fetch an older view again when needed.

To change OpenRouter models, keep **Provider: OpenRouter** and edit **Vision model** directly. Search the live suggestions or paste a `provider/model-id`; editing a model automatically selects **Custom models**. Suggestions come from OpenRouter's public catalog and include models advertising image input and tool support. **Refresh OpenRouter models** reloads the list, and manual IDs work even when the catalog is unavailable. Leave **Reinspection model** blank to use the vision model, or choose a separate one. Changing models produces a different cache configuration, so prior results are preserved.

Inputs: multi-page PDF, PNG, JPEG, TIFF, and BMP. Image inputs use their first frame. Vector PDFs retain native text and geometry and support high-resolution detail crops. Processed scans save their detection image frame so overlays use the same coordinates.

## Results and reuse

The [symbol library](http://127.0.0.1:8765/symbols) shows saved legend crops, names, provenance, and standard coverage. Its SQLite database and PNGs live separately in [`symbol_database/`](symbol_database/README.md). Detection uses applicable references automatically, with the current drawing legend taking precedence. Machine-extracted references are not verified ground truth.

The viewer provides symbol observations, legend thumbnails and definitions, native candidates, machine diagnostics, and native PDF text. Search and filter results, select boxes or list entries, pan/zoom/fit/focus, compare the original with overlays, adjust the background, collapse panels, and switch language.

- **Observations are not unique physical symbol counts.** Overlapping crops can repeat a symbol. This fork does not introduce deduplication.
- Candidates, uncertain proposals, non-symbol decisions, and native text remain separate from model detections. Native text does not receive an invented symbol assignment.
- Complete means processing finished. Partial or paused runs retain diagnostics and available results; model output has not been verified by an engineer.
- Reopening and downloading saved results makes no model calls and creates no review directory. Detection downloads preserve the stored JSON bytes.
- **Resume compatible artifacts** reuses matching source/configuration/model/version checkpoints. A run with published detections is copied before resuming so its original artifacts remain unchanged. **Start a brand-new run** bypasses detection and legend caches.
- Resume retries crops with candidate-validation failures from an older response contract. Successful cached crops remain reusable; reopening the viewer alone never retries detection.
- Missing sources can be reattached from recent runs. The SHA-256 must match. Results and JSON downloads remain accessible without the source; rendering requires a verified source.

Each run lives under `runs/<drawing>/<timestamp>_<model>_<id>/` and includes:

- `detection.json`: version-1 machine observations, pages, native candidates, diagnostics, and legend pack.
- `legend.json`, `result.json`, `cost.json`, `reuse.report.json`.
- `evidence/`: native page evidence and processed scan frames when applicable.
- `checkpoints/`: completed work, stage versions, failures, and pause reasons.
- `source.json` and optional `workbench.json`: source linkage and redacted job metadata.

The bundle's `reviews` field and `perception.review.json` retain their historical names for compatibility. They contain machine diagnostics. Existing version-1 detection bundles open without migration; graph-only runs are unsupported.

Downloads contain machine data and may include printed drawing text and embedded legend thumbnails. Estimated cost uses the configured pricing and is not an assertion of actual provider billing.

## Batch detection

```sh
export DIAGEX_LLM_PROVIDER=openrouter
export OPENROUTER_API_KEY='your-key'
export DIAGEX_VISION_MODEL='provider/model-id'
diagex detect tests/p-ids-public/two-tanks.pdf --out-dir runs
```

Other environment keys: `KIMI_API_KEY`, `ANTHROPIC_API_KEY`, or Azure's `AZURE_OPENAI_API_KEY`, `AZURE_OPENAI_ENDPOINT`, and `AZURE_OPENAI_DEPLOYMENT_NAME`. See `src/diagex/config.py` for supported transport/model settings. `--fresh`, `--no-legend`, and `--effort low|medium|high|xhigh` are available. `DIAGEX_PID_ENGINE`, if set, must select evidence-v2.

Only `detect`, `web`, and `version` are public commands. The server rejects legacy engines, graph stages, reviewed-build payloads, experimental raster proposal routes, and removed review mutation endpoints.

## Validation

```sh
python -m pytest tests/unit
ruff check src/diagex tests/unit tests/browser/run_detection_smoke.py
python tests/browser/run_detection_smoke.py
uv build
```

The browser check requires Node's `playwright` package and a Chrome/Chromium installation (`CHROME_PATH` can select one). It uses a temporary synthetic multi-page PDF and a deterministic runner, checks that browsing is immutable, and saves screenshots under `output/detection-smoke/`. Unit/integration tests cover the real detection pipeline with replayed model responses, completed-run reuse, fresh runs, failure guards, rotated PDF geometry, scan frames, source hashes, downloads, and removed endpoint rejection. A live provider run is a separate check and requires credentials.

## Fork scope and attribution

Hand-maintained graph/review/export code and research/training scripts have been retired. Generated DEXPI sources, vendored attribution material, and historical research data remain untouched in this checkout and are excluded from distributions. The pre-existing local `workflows/` extraction is also preserved outside the package; the active result contract is `diagex.detection.result.DetectionResult`. Runtime persistence uses `diagex.runs`.

The implementation specification is [docs/SYMBOL_DETECTION_UI_FORK_HANDOFF.md](docs/SYMBOL_DETECTION_UI_FORK_HANDOFF.md). Original project and third-party attribution remain in [LICENSE](LICENSE) and [NOTICE](NOTICE). Retained public drawing fixtures keep their provenance under `tests/p-ids-public/`.
