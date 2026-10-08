"""Evidence-v2 legend and symbol detection, stopping before object fusion."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import fitz

from diagex.config import Config, EffortLevel
from diagex.detection.result import DetectionResult
from diagex.extractors.evidence_checkpoint import (
    CheckpointStore,
    atomic_write_json,
    atomic_write_text,
    find_resumable_run_with_report,
)
from diagex.llm.client import LLMClient, is_non_retryable_api_error
from diagex.llm.cost import CostTracker
from diagex.runs.layout import new_run_id as _new_run_id
from diagex.runs.layout import prepare_evidence_run_dir as _prepare_v2_run_dir
from diagex.runs.layout import safe_stem as _safe_stem
from diagex.symbol_library import augment_legend, reference_pack
from diagex.vision.evidence import PageEvidence, extract_page_evidence, sha256_file
from diagex.vision.legend_models import LegendPack, SymbolStandard
from diagex.vision.perception import (
    RESPONSE_CONTRACT_VERSION,
    DetectionRecord,
    PerceptionRunGuard,
    perceive_tile,
)
from diagex.vision.symbol_candidates import (
    PERCEPTION_DEPENDENT_STAGES,
    SYMBOL_PERCEPTION_VERSION,
    symbol_candidates,
)
from diagex.vision.tiling import AspectAwareStrategy, ownership_core, tile
from diagex.vision.views import ViewProvider

if TYPE_CHECKING:
    from rich.console import Console


def run_symbol_detection(
    *,
    diagram: Path,
    symbol_standard: SymbolStandard,
    legend_path: Path | None,
    legend_pages: list[int] | None,
    legend_region: tuple[int, int, int, int, int] | None,
    no_legend: bool,
    legend_key: str | None,
    effort: EffortLevel,
    config: Config,
    persist: bool,
    fresh: bool = False,
    console: Console | None,
) -> DetectionResult:
    from rich.console import Console as RichConsole

    from diagex.extractors.pid_legend import (
        LEGEND_EXTRACTOR_VERSION,
        load_builtin_pack,
        resolve_evidence_legend,
    )
    from diagex.ui.progress import make_reporter
    from diagex.vision.loader import load

    cfg = config
    if (
        cfg.raster_symbol_mode != "baseline"
        or cfg.raster_proposals is not None
        or cfg.raster_ink_filter
    ):
        raise ValueError("Experimental raster proposal routes are not supported")
    stem = _safe_stem(diagram)
    started = time.perf_counter()
    source_hash = sha256_file(diagram)
    vision_model = cfg.llm.vision_model or cfg.llm.model
    reasoning_model = cfg.llm.reasoning_model or cfg.llm.model
    config_hash = _configuration_hash(
        cfg=cfg,
        symbol_standard=symbol_standard,
        vision_model=vision_model,
        reasoning_model=reasoning_model,
        legend_path=legend_path,
        legend_pages=legend_pages,
        legend_region=legend_region,
        no_legend=no_legend,
        legend_key=legend_key,
        effort=effort,
    )
    run_dir: Path | None = None
    run_id = _new_run_id()
    store: CheckpointStore | None = None
    resumed = False
    resume_report: dict[str, Any] = {"reason": "persistence disabled"}
    initial_completed: dict[str, int] = {}
    invalidated_completed: dict[str, int] = {}
    runs_root = cfg.runs_dir / stem
    if persist:
        runs_root.mkdir(parents=True, exist_ok=True)
        if fresh:
            resume_report = {
                "reason": "fresh run requested; checkpoint discovery skipped",
                "considered_runs": 0,
                "fresh_requested": True,
            }
        else:
            store, resume_report = find_resumable_run_with_report(
                runs_root=runs_root,
                source_sha256=source_hash,
                config_sha256=config_hash,
                include_complete=True,
                required_stage_versions={
                    "legend_extraction": LEGEND_EXTRACTOR_VERSION,
                    "symbol_perception": SYMBOL_PERCEPTION_VERSION,
                },
            )
        if store is not None and (
            store.manifest.status == "complete" or (store.run_dir / "detection.json").exists()
        ):
            source_store = store
            run_dir, run_id = _prepare_v2_run_dir(cfg, stem, vision_model)
            store = CheckpointStore.create(
                run_dir=run_dir, source_sha256=source_hash, config_sha256=config_hash, run_id=run_id
            )
            store.seed_raw_evidence_from(source_store, include_contextual=False)
            resume_report["source_run_dir"] = str(source_store.run_dir)
            resume_report["reason"] = "compatible detection evidence copied into a new run"
            resumed = True
        elif store is not None:
            run_dir = store.run_dir
            run_id = store.manifest.run_id
            resumed = True
        else:
            run_dir, run_id = _prepare_v2_run_dir(cfg, stem, vision_model)
            store = CheckpointStore.create(
                run_dir=run_dir, source_sha256=source_hash, config_sha256=config_hash, run_id=run_id
            )
    prior_cost = _load_prior_cost(run_dir) if resumed and run_dir is not None else {}
    if store is not None:
        initial_completed = {
            stage: len(items) for stage, items in sorted(store.manifest.completed.items())
        }
        store.ensure_stage_version(
            "legend_extraction", LEGEND_EXTRACTOR_VERSION, invalidate=PERCEPTION_DEPENDENT_STAGES
        )
        store.ensure_stage_version(
            "symbol_perception", SYMBOL_PERCEPTION_VERSION, invalidate=PERCEPTION_DEPENDENT_STAGES
        )
        remaining = {stage: len(items) for stage, items in sorted(store.manifest.completed.items())}
        invalidated_completed = {
            stage: count - remaining.get(stage, 0)
            for stage, count in initial_completed.items()
            if count > remaining.get(stage, 0)
        }
    source = load(diagram, tiling=cfg.tiling, scan_cfg=cfg.scan)
    progress_console = console or RichConsole()
    _print_reuse_start(
        progress_console,
        resumed=resumed,
        run_dir=run_dir,
        reason=str(resume_report.get("reason") or ""),
        available={stage: len(items) for stage, items in sorted(store.manifest.completed.items())}
        if store is not None
        else {},
        invalidated=invalidated_completed,
    )
    if run_dir is not None:
        atomic_write_json(
            run_dir / "reuse.report.json",
            {
                "mode": "resumed" if resumed else "new",
                "fresh_requested": fresh,
                "run_dir": str(run_dir),
                "decision": resume_report,
                "initial_completed_by_stage": initial_completed,
                "available_after_invalidation_by_stage": {
                    stage: len(items) for stage, items in sorted(store.manifest.completed.items())
                }
                if store is not None
                else {},
                "invalidated_by_stage": invalidated_completed,
                "status": "running",
            },
        )

    def reporter_factory():
        return make_reporter(progress_console, effort=effort)

    cost = CostTracker(pricing=cfg.pricing)
    vision_cfg = replace(cfg.llm, model=vision_model, reasoning_mode="disabled")
    vision_llm = LLMClient(vision_cfg, budgets=cfg.budgets)
    escalation_llm = (
        LLMClient(
            replace(cfg.llm, model=cfg.llm.escalation_model, reasoning_mode="enabled"),
            budgets=cfg.budgets,
        )
        if cfg.llm.escalation_model
        else None
    )
    vision_llm.reset_retry_counter()
    evidence_pages, page_states = _inspect_pages(
        source=source, diagram=diagram, store=store, run_dir=run_dir, reporter=reporter_factory()
    )
    detected_legends = [page.page_index for page in evidence_pages if page.role == "legend"]
    legend_pack: LegendPack
    legend_source = ""
    legend_reporter = reporter_factory()
    try:
        with legend_reporter:
            legend_reporter.on_phase_start(
                name="v2 legend resolution", total_items=len(detected_legends) or 1
            )
            routed = resolve_evidence_legend(
                source=source,
                pages=evidence_pages,
                symbol_standard=symbol_standard,
                cfg=cfg,
                client=vision_llm,
                cost_tracker=cost,
                legend_path=legend_path,
                legend_pages=legend_pages,
                legend_region=legend_region,
                no_legend=no_legend,
                legend_key=legend_key,
                runs_dir_for_stem=runs_root if persist else None,
                reporter=legend_reporter,
                fresh=fresh,
            )
            resolution = routed.resolution
            legend_pack = resolution.pack
            legend_source = resolution.source
            legend_reporter.on_phase_end(
                detail=f"{len(legend_pack.entries)} entries · source={legend_source}"
            )
    except Exception as exc:
        if is_non_retryable_api_error(exc):
            raise
        legend_pack = load_builtin_pack(symbol_standard)
        legend_source = f"fallback_builtin(error={exc!r})"
    _checkpoint_cost(run_dir, prior_cost, cost)
    legend_failure = _legend_prerequisite_error(legend_pack, legend_source)
    references = reference_pack(
        cfg.symbol_database_dir, document_hash=source_hash, standard=symbol_standard,
        include_project=not (fresh or no_legend),
    )
    legend_pack = augment_legend(legend_pack, references)
    if store is not None:
        store.manifest.errors = [e for e in store.manifest.errors if e.stage != "legend"]
        if legend_failure:
            store.mark_error("legend", "coverage", legend_failure)
        else:
            store.save()
    interpretation_entries = [
        entry
        for entry in legend_pack.entries
        if entry.source == "customer_override"
        or entry.attributes.get("row_status") not in {"uncertain", "reject"}
    ]
    legend_visual_entries = [entry.model_dump(mode="json") for entry in interpretation_entries]
    if store is not None:
        content_hash = hashlib.sha256(
            json.dumps(legend_visual_entries, sort_keys=True).encode()
        ).hexdigest()
        store.ensure_stage_version(
            "legend_content", content_hash, invalidate=PERCEPTION_DEPENDENT_STAGES
        )
    perception_stop_reason = None
    detections, per_page_status, perception_call_counts, perception_stop_reason = _run_perception(
        source=source,
        pages=evidence_pages,
        cfg=cfg,
        client=vision_llm,
        cost=cost,
        reporter=reporter_factory(),
        store=store,
        legend_summary=legend_visual_entries,
        run_dir=run_dir,
        prior_cost=prior_cost,
        prerequisite_error=legend_failure,
        escalation_client=escalation_llm,
    )
    for region_coverage in legend_pack.coverage:
        if region_coverage.status != "complete":
            per_page_status[region_coverage.page_index] = "partial"
    if run_dir is not None:
        from diagex.detection.artifacts import write_detection_bundle

        audit_path = run_dir / "perception.review.json"
        reviews = (
            json.loads(audit_path.read_text()).get("reviews", []) if audit_path.exists() else []
        )
        write_detection_bundle(
            run_dir,
            source_hash=source_hash,
            pages=evidence_pages,
            detections=detections,
            legend_pack=legend_pack,
            per_page_status=per_page_status,
            candidates=[
                c.model_dump(mode="json")
                for p in evidence_pages
                if p.role == "pid"
                for c in symbol_candidates(p)
            ],
            reviews=reviews,
        )
        atomic_write_json(run_dir / "legend.json", legend_pack.model_dump(mode="json"))
        atomic_write_json(
            run_dir / "rendering.json", {"tiling": asdict(cfg.tiling), "scan": asdict(cfg.scan)}
        )
        atomic_write_json(
            run_dir / "source.json",
            {"source_path": str(diagram.resolve()), "source_sha256": source_hash},
        )
    current_cost = cost.summary()
    current_cost["tool_call_counts"] = perception_call_counts
    current_cost["n_tool_calls"] = sum(perception_call_counts.values())
    current_cost["wall_clock_s"] = round(time.perf_counter() - started, 3)
    current_cost["retries"] = vision_llm.retries_total
    cost_summary = _merge_cost_summaries(prior_cost, current_cost)
    quality_status = "partial" if any(v != "ok" for v in per_page_status.values()) else "complete"
    result = DetectionResult(
        diagram_stem=stem,
        effort=effort,
        model=vision_model,
        observation_count=len(detections),
        candidate_count=sum(len(symbol_candidates(p)) for p in evidence_pages if p.role == "pid"),
        cost_summary=cost_summary,
        legend_source=legend_source,
        legend_entry_count=len(legend_pack.entries),
        run_dir=run_dir,
        run_id=run_id,
        engine="evidence-v2",
        quality_status=quality_status,
        workflow_stage="detection",
    )

    if run_dir is not None:
        atomic_write_json(run_dir / "cost.json", cost_summary)
        atomic_write_json(
            run_dir / "result.json",
            {**json.loads(result.to_json()), "stop_reason": perception_stop_reason},
        )
        if store is not None:
            store.manifest.pause_reason = perception_stop_reason
            store.set_status(
                "paused"
                if perception_stop_reason
                else "partial"
                if store.manifest.errors or perception_stop_reason or quality_status == "partial"
                else "complete"
            )
        atomic_write_json(
            run_dir / "reuse.report.json",
            {
                "mode": "resumed" if resumed else "new",
                "decision": resume_report,
                "fresh_requested": fresh,
                **(store.reuse_summary() if store else {}),
                "workflow_stage": "detection",
                "status": quality_status,
            },
        )
    if store is not None:
        _print_reuse_end(progress_console, summary=store.reuse_summary())
    return result


def _inspect_pages(
    *,
    source: Any,
    diagram: Path,
    store: CheckpointStore | None,
    run_dir: Path | None,
    reporter: Any,
) -> tuple[list[PageEvidence], list[Any]]:
    from diagex.vision.loader import iter_pages

    evidence: list[PageEvidence] = []
    states: list[Any] = []
    pdf_doc = fitz.open(diagram) if diagram.suffix.lower() == ".pdf" else None
    total = int(source.metadata.get("page_count", 0) or 0)
    try:
        with reporter:
            reporter.on_phase_start(name="v2 page inspection", total_items=total)
            for page in iter_pages(source):
                item = f"page-{page.page_index + 1:04d}"
                reporter.on_phase_item_start(
                    item=page.page_index + 1,
                    total_items=total,
                    label=f"inspect page {page.page_index + 1}",
                )
                public_path = (
                    run_dir / "evidence" / f"page-{page.page_index + 1:04d}.json"
                    if run_dir is not None
                    else None
                )
                if (
                    store is not None
                    and store.is_done("inspection", item)
                    and (public_path is not None)
                    and public_path.is_file()
                ):
                    page_evidence = PageEvidence.model_validate_json(
                        public_path.read_text(encoding="utf-8")
                    )
                    if page_evidence.role_reason == "sparse first page" and not page_evidence.text_spans and not page_evidence.paths:
                        page_evidence = extract_page_evidence(
                            page=page, source_path=diagram,
                            pdf_page=pdf_doc[page.page_index] if pdf_doc is not None else None,
                        )
                        atomic_write_text(public_path, page_evidence.model_dump_json(indent=2))
                    elif (
                        pdf_doc is not None
                        and pdf_doc[page.page_index].rotation
                        and (page_evidence.native_coordinate_frame != "rendered_page")
                    ):
                        page_evidence = extract_page_evidence(
                            page=page, source_path=diagram, pdf_page=pdf_doc[page.page_index]
                        )
                        atomic_write_text(public_path, page_evidence.model_dump_json(indent=2))
                    else:
                        store.record_reuse("inspection", item)
                else:
                    page_evidence = extract_page_evidence(
                        page=page,
                        source_path=diagram,
                        pdf_page=pdf_doc[page.page_index] if pdf_doc is not None else None,
                    )
                    if public_path is not None:
                        atomic_write_text(public_path, page_evidence.model_dump_json(indent=2))
                    if store is not None:
                        store.mark_done("inspection", item)
                if run_dir is not None and page.is_scanned:
                    image_path = run_dir / "evidence" / f"page-{page.page_index + 1:04d}.png"
                    image_path.parent.mkdir(parents=True, exist_ok=True)
                    page.image.save(image_path, format="PNG")
                evidence.append(page_evidence)
                states.append(
                    SimpleNamespace(page=page.model_copy(update={"image": None}), transcript=[])
                )
                reporter.on_phase_item_end(
                    detail=f"role={page_evidence.role} ({page_evidence.role_confidence}), text={len(page_evidence.text_spans)}, paths={len(page_evidence.paths)}"
                )
            reporter.on_phase_end(detail=f"{len(evidence)} pages classified")
    finally:
        if pdf_doc is not None:
            pdf_doc.close()
    return (evidence, states)


def _legend_prerequisite_error(pack, source):
    failed = [c for c in pack.coverage if c.status != "complete" and c.failure_kind != "ambiguity"]
    if failed:
        return f"Symbol extraction paused: {len(failed)} source legend rows/regions were not successfully inspected. Completed legend rows are saved; retry the unresolved rows before symbol extraction."
    if source.startswith("fallback_builtin(error="):
        return "Symbol extraction paused because source legend extraction failed; built-in definitions do not replace the missing source review."
    return None


def _run_perception(
    *,
    source: Any,
    pages: list[PageEvidence],
    cfg: Config,
    client: LLMClient,
    cost: CostTracker,
    reporter: Any,
    store: CheckpointStore | None,
    legend_summary: list[dict[str, Any]],
    run_dir: Path | None,
    prior_cost: dict[str, Any],
    prerequisite_error: str | None = None,
    escalation_client: LLMClient | None = None,
) -> tuple[list[DetectionRecord], dict[int, str], dict[str, int], str | None]:
    from diagex.vision.loader import iter_pages

    evidence_by_index = {page.page_index: page for page in pages}
    pid_pages = [page for page in pages if page.role == "pid"]
    strategy = AspectAwareStrategy(
        max_tokens_per_tile=cfg.tiling.max_tokens_per_tile,
        overlap_frac=cfg.tiling.overlap_frac,
        token_per_pixel=cfg.tiling.token_per_pixel,
    )
    detections: list[DetectionRecord] = []
    statuses = {page.page_index: "ok" for page in pages}
    page_error_counts: dict[int, int] = {page.page_index: 0 for page in pid_pages}
    page_view_counts: dict[int, int] = {page.page_index: 0 for page in pid_pages}
    call_counts = {"submit_pid_objects": 0}
    perception_reviews: list[dict[str, Any]] = []
    guard = PerceptionRunGuard(cfg.symbol_perception)
    deadline = time.monotonic() + cfg.symbol_perception.run_timeout_s
    stop_reason: str | None = prerequisite_error
    if run_dir is not None:
        (run_dir / "perception.stop.json").unlink(missing_ok=True)
    if store is not None:
        store.manifest.errors = [
            e
            for e in store.manifest.errors
            if not (e.stage == "perception" and e.item == "run_guard")
        ]
        store.save()

    def next_step() -> int:
        return max((row.step for row in cost.steps), default=0) + 1

    def record_model_attempt(tool_name="submit_pid_objects") -> None:
        call_counts[tool_name] = call_counts.get(tool_name, 0) + 1

    planned_total = sum(
        len(tile(rendered_page, strategy))
        for rendered_page in iter_pages(source)
        if evidence_by_index[rendered_page.page_index].role == "pid"
    )
    progress_item = 0
    with reporter:
        reporter.on_phase_start(name="v2 fixed-crop object perception", total_items=planned_total)
        for rendered_page in iter_pages(source):
            if stop_reason:
                break
            evidence = evidence_by_index[rendered_page.page_index]
            if evidence.role != "pid":
                continue
            fixed_tiles = tile(rendered_page, strategy)
            candidates = symbol_candidates(evidence)
            page_view_counts[evidence.page_index] = len(fixed_tiles)
            provider = ViewProvider(rendered_page, fixed_tiles)
            for current_tile in fixed_tiles:
                if time.monotonic() >= deadline:
                    stop_reason = "Symbol extraction stopped early at its configured time limit; completed crops are saved."
                    break
                progress_item += 1
                item = f"p{rendered_page.page_index + 1:04d}__{current_tile.id}"
                reporter.on_phase_item_start(
                    item=progress_item,
                    total_items=planned_total,
                    label=f"page {rendered_page.page_index + 1} · {current_tile.id}",
                )
                failed: bool | None = None
                diagnostic_events: list[dict[str, Any]] = []

                def record_diagnostic(
                    event: dict[str, Any],
                    events: list[dict[str, Any]] = diagnostic_events,
                    artifact_item: str = item,
                    tile_id: str = current_tile.id,
                ) -> None:
                    events.append(event)
                    if store is not None:
                        atomic_write_json(
                            store.artifact_path("perception_diagnostics", artifact_item),
                            {"tile_id": tile_id, "events": events},
                        )

                try:
                    saved = None
                    if store is not None and store.is_done("perception", item):
                        saved = json.loads(store.artifact_path("perception", item).read_text())
                        if (
                            saved.get("response_contract_version") != RESPONSE_CONTRACT_VERSION
                            and any(
                                review.get("reason", "").startswith("Invalid candidate result:")
                                for review in saved.get("candidate_reviews", [])
                            )
                        ):
                            # Retry only failed old-contract crops during an explicit job.
                            # Successful cached crops and semantic uncertainty stay reusable.
                            saved = None
                    if saved is not None:
                        store.record_reuse("perception", item)
                        failed = (
                            saved.get("contract_failed") if saved.get("native_candidates") else None
                        )
                        tile_detections = [
                            DetectionRecord.model_validate(value)
                            for value in saved.get("detections", [])
                        ]
                        detail = f"checkpoint · {len(tile_detections)} objects"
                        perception_reviews.extend(saved.get("candidate_reviews", []))
                        rejected_count = len(saved.get("rejected_objects", []))
                        if rejected_count:
                            page_error_counts[evidence.page_index] += 1
                            detail += f", {rejected_count} malformed object(s) skipped"
                    else:
                        view_image, view_info = provider.get_tile(current_tile.id)
                        core = ownership_core(current_tile, fixed_tiles)
                        page_context = {"coverage": "deterministic fixed grid"}
                        tile_perception = perceive_tile
                        outcome = tile_perception(
                            client=client,
                            cost_tracker=cost,
                            reporter=reporter,
                            page=evidence,
                            tile=current_tile,
                            view_image=view_image,
                            view_info=view_info,
                            ownership_bbox=core,
                            legend_summary=legend_summary,
                            step=next_step(),
                            page_context=page_context,
                            overview_image=provider.get_overview()[0]
                            if cfg.symbol_perception.workflow == "adaptive"
                            else None,
                            region_provider=provider.get_region,
                            escalation_client=escalation_client,
                            on_attempt=record_model_attempt,
                            candidates=candidates,
                            reasoning_mode=cfg.llm.reasoning_mode,
                            policy=cfg.symbol_perception,
                            deadline=deadline,
                            on_diagnostic=record_diagnostic,
                        )
                        failed = outcome.contract_failed if outcome.candidates else None
                        tile_detections = outcome.detections
                        batch = outcome.batch
                        for review in batch.candidate_reviews:
                            review.update(page_index=evidence.page_index, tile_id=current_tile.id)
                        perception_reviews.extend(batch.candidate_reviews)
                        if store is not None:
                            store.invalidate(
                                "contextual",
                                "topology",
                                "line_evidence",
                                "page_graph",
                                "assembly",
                                "export",
                            )
                            store.write_json_artifact(
                                "perception",
                                item,
                                {
                                    "detections": [
                                        value.model_dump(mode="json") for value in tile_detections
                                    ],
                                    "observations": batch.observations,
                                    "uncertainties": batch.uncertainties,
                                    "rejected_objects": batch.rejected_objects,
                                    "symbol_perception_version": SYMBOL_PERCEPTION_VERSION,
                                    "response_contract_version": RESPONSE_CONTRACT_VERSION,
                                    "native_candidates": [
                                        c.model_dump(mode="json") for c in outcome.candidates
                                    ],
                                    "candidate_reviews": batch.candidate_reviews,
                                    "ownership_core": core.model_dump(mode="json"),
                                    "reason": "deterministic fixed grid",
                                    "model_attempts": outcome.attempts,
                                    "format_recovery": outcome.recovery_diagnostics,
                                    "contract_failed": outcome.contract_failed,
                                },
                            )
                        _checkpoint_cost(run_dir, prior_cost, cost)
                        detail = f"{len(tile_detections)} objects"
                        if outcome.attempts > 1:
                            detail += f" · {outcome.attempts} attempts"
                        if batch.rejected_objects:
                            page_error_counts[evidence.page_index] += 1
                            detail += f", {len(batch.rejected_objects)} malformed object(s) skipped"
                        if any(r.get("status") == "unreviewed" for r in batch.candidate_reviews):
                            page_error_counts[evidence.page_index] += 1
                    detections.extend(tile_detections)
                    reporter.on_phase_item_end(detail=detail)
                except Exception as exc:
                    failed = True
                    page_error_counts[evidence.page_index] += 1
                    if store is not None:
                        diagnostics = getattr(exc, "diagnostics", None)
                        if diagnostics:
                            atomic_write_json(
                                store.artifact_path("perception_errors", item),
                                {
                                    "error": str(exc),
                                    "attempts": getattr(exc, "attempts", 1),
                                    "invalid_responses": diagnostics,
                                },
                            )
                        store.mark_error("perception", item, repr(exc))
                    _checkpoint_cost(run_dir, prior_cost, cost)
                    reporter.on_phase_item_end(detail=repr(exc), is_error=True)
                    if is_non_retryable_api_error(exc):
                        raise
                stop_reason = guard.observe(failed)
                if stop_reason:
                    break
            if stop_reason:
                break
        reporter.on_phase_end(
            detail=stop_reason
            or f"{len(detections)} raw detections; {sum(call_counts.values())} fixed-crop calls"
        )
    if stop_reason:
        if store is not None:
            store.mark_error("perception", "run_guard", stop_reason)
        if run_dir is not None:
            atomic_write_json(
                run_dir / "perception.stop.json",
                {
                    "reason": stop_reason,
                    "processed_crops": progress_item,
                    "planned_crops": planned_total,
                },
            )
        assessed = {r.get("candidate_id") for r in perception_reviews}
        for page in pid_pages:
            statuses[page.page_index] = "partial"
            perception_reviews.extend(
                {
                    "candidate_id": c.id,
                    "page_index": page.page_index,
                    "bbox": c.bbox.model_dump(mode="json"),
                    "source_path_ids": c.source_path_ids,
                    "status": "unreviewed",
                    "reason": stop_reason,
                }
                for c in symbol_candidates(page)
                if c.id not in assessed
            )
    for page in pid_pages:
        errors = page_error_counts.get(page.page_index, 0)
        inspected = page_view_counts.get(page.page_index, 0)
        page_detections = [value for value in detections if value.page_index == page.page_index]
        if errors:
            statuses[page.page_index] = (
                "error" if not page_detections and errors >= inspected else "partial"
            )
    if run_dir is not None:
        atomic_write_json(
            run_dir / "perception.review.json",
            {
                "version": SYMBOL_PERCEPTION_VERSION,
                "reviews": perception_reviews,
                "note": "Unreviewed candidates and unanchored proposals are not confirmed detections.",
            },
        )
    return (detections, statuses, call_counts, stop_reason)


def _stage_count_text(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join((f"{stage}={count}" for stage, count in sorted(values.items())))


def _print_reuse_start(
    console: Any,
    *,
    resumed: bool,
    run_dir: Path | None,
    reason: str,
    available: dict[str, int],
    invalidated: dict[str, int],
) -> None:
    if run_dir is None:
        console.print("[diagex.cache] persistence disabled; no checkpoint artifacts will be reused")
        return
    mode = "RESUME" if resumed else "NEW RUN"
    console.print(f"[diagex.cache] {mode} · {run_dir}")
    console.print(f"[diagex.cache] decision: {reason}")
    console.print(f"[diagex.cache] reusable checkpoint items: {_stage_count_text(available)}")
    if invalidated:
        console.print(
            "[diagex.cache] invalidated by pipeline version change: "
            + _stage_count_text(invalidated)
        )


def _print_reuse_end(console: Any, *, summary: dict[str, Any]) -> None:
    console.print(
        f"[diagex.cache] final checkpoint reuse: {summary['reused_total']} reused vs {summary['computed_total']} computed ({summary['reuse_percent']:.1f}% reused)"
    )
    console.print(
        "[diagex.cache] reused by stage: " + _stage_count_text(summary["reused_by_stage"])
    )
    console.print(
        "[diagex.cache] computed by stage: " + _stage_count_text(summary["computed_by_stage"])
    )
    console.print("[diagex.cache] details saved to reuse.report.json")


def _configuration_hash(
    *,
    cfg: Config,
    symbol_standard: str,
    vision_model: str,
    reasoning_model: str,
    legend_path: Path | None,
    legend_pages: list[int] | None,
    legend_region: tuple[int, int, int, int, int] | None,
    no_legend: bool,
    legend_key: str | None,
    effort: EffortLevel,
) -> str:
    legend_hash = sha256_file(legend_path) if legend_path is not None else None
    payload = {
        "engine": "evidence-v2",
        "engine_schema": "3.6.0",
        "transport": cfg.llm.transport,
        **({"openrouter_routing": {
            "order": cfg.llm.openrouter_provider_order,
            "ignore": cfg.llm.openrouter_provider_ignore,
            "allow_fallbacks": cfg.llm.openrouter_allow_fallbacks,
        }} if cfg.llm.transport == "openrouter" and (
            cfg.llm.openrouter_provider_order or cfg.llm.openrouter_provider_ignore
            or not cfg.llm.openrouter_allow_fallbacks
        ) else {}),
        "vision_model": vision_model,
        "reasoning_model": reasoning_model,
        "reasoning_mode": cfg.llm.reasoning_mode,
        "escalation_model": cfg.llm.escalation_model,
        "production_open_weight": cfg.llm.production_open_weight,
        "process_context": cfg.process_context,
        "symbol_perception": asdict(cfg.symbol_perception),
        "effort": effort,
        "tiling": asdict(cfg.tiling),
        "scan": asdict(cfg.scan),
        "symbol_standard": symbol_standard,
        "legend": {
            "path_hash": legend_hash,
            "pages": legend_pages,
            "region": legend_region,
            "disabled": no_legend,
            "key": legend_key,
        },
        # Historical constant preserves compatibility with existing raw evidence caches.
        "page_graph_pipeline": "1.9.0",
    }
    return hashlib.sha256(
        json.dumps(payload, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()


def _load_prior_cost(run_dir: Path | None) -> dict[str, Any]:
    if run_dir is None:
        return {}
    path = run_dir / "cost.json"
    if not path.is_file():
        return {}
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}


def _merge_cost_summaries(prior: dict[str, Any], current: dict[str, Any]) -> dict[str, Any]:
    if not prior:
        return dict(current)
    additive = {
        "total_usd",
        "total_tokens",
        "input_tokens",
        "output_tokens",
        "cache_read_tokens",
        "cache_write_tokens",
        "image_tokens",
        "retries",
        "n_tool_calls",
        "wall_clock_s",
    }
    merged = dict(current)
    for key in additive:
        merged[key] = prior.get(key, 0) + current.get(key, 0)
    merged["steps"] = [*(prior.get("steps") or []), *(current.get("steps") or [])]
    tool_counts: dict[str, int] = {}
    for summary in (prior, current):
        for key, value in (summary.get("tool_call_counts") or {}).items():
            tool_counts[key] = tool_counts.get(key, 0) + int(value or 0)
    merged["tool_call_counts"] = tool_counts
    return merged


def _checkpoint_cost(run_dir: Path | None, prior: dict[str, Any], current: CostTracker) -> None:
    if run_dir is None:
        return
    atomic_write_text(
        run_dir / "cost.json",
        json.dumps(_merge_cost_summaries(prior, current.summary()), indent=2, sort_keys=True),
    )
