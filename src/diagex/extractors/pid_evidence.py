"""Evidence-first P&ID extraction engine (opt-in ``evidence-v2``)."""

from __future__ import annotations

import base64
import hashlib
import io
import json
import re
import time
from dataclasses import asdict, replace
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

import fitz

from diagex.config import EFFORT_PROFILES, Config, EffortLevel
from diagex.extractors.evidence_checkpoint import (
    CheckpointStore,
    atomic_write_json,
    atomic_write_text,
    find_resumable_run_with_report,
)
from diagex.extractors.pid import (
    PidExtractionResult,
    _new_run_id,
    _safe_model_name,
    _safe_stem,
    _timestamp,
    _write_confidence_report,
    _write_run_artefacts,
)
from diagex.llm.client import LLMClient, is_non_retryable_api_error
from diagex.llm.cost import CostTracker
from diagex.vision.contextual import (
    ContextualPageResult,
    apply_contextual_results,
    find_contextual_candidates,
    resolve_contextual_page,
)
from diagex.vision.evidence import (
    PageEvidence,
    extract_page_evidence,
    sha256_file,
)
from diagex.vision.fusion import assemble_graph, fuse_objects
from diagex.vision.legend_models import LegendPack, SymbolStandard
from diagex.vision.native_text import build_native_text_inventory
from diagex.vision.page_graph import (
    PageGraphResult,
    PageLineEvidence,
    classify_page_line_evidence,
    solve_page_graph,
)
from diagex.vision.perception import DetectionRecord, perceive_tile
from diagex.vision.quality import QualityReport, add_dexpi_results, assess_quality
from diagex.vision.tiling import AspectAwareStrategy, ownership_core, tile
from diagex.vision.topology import TopologyResult, build_page_topology
from diagex.vision.views import ViewProvider

if TYPE_CHECKING:
    from rich.console import Console


def run_pid_evidence_extract(
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
    out_path: Path | None,
    confidence_report_path: Path | None,
    console: Console | None,
) -> PidExtractionResult:
    from rich.console import Console as RichConsole

    from diagex.extractors.pid_legend import load_builtin_pack, resolve_evidence_legend
    from diagex.ui.progress import make_reporter
    from diagex.vision.loader import load

    cfg = config
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
        store, resume_report = find_resumable_run_with_report(
            runs_root=runs_root,
            source_sha256=source_hash,
            config_sha256=config_hash,
        )
        if store is not None:
            run_dir = store.run_dir
            run_id = store.manifest.run_id
            resumed = True
        else:
            run_dir, run_id = _prepare_v2_run_dir(cfg, stem, vision_model)
            store = CheckpointStore.create(
                run_dir=run_dir,
                source_sha256=source_hash,
                config_sha256=config_hash,
                run_id=run_id,
            )

    prior_cost = _load_prior_cost(run_dir) if resumed and run_dir is not None else {}
    if store is not None:
        initial_completed = {
            stage: len(items) for stage, items in sorted(store.manifest.completed.items())
        }
        store.ensure_stage_version(
            "page_graph_pipeline",
            "1.7.0",
            invalidate=("contextual", "topology", "line_evidence", "page_graph", "assembly", "export"),
        )
        remaining = {
            stage: len(items) for stage, items in sorted(store.manifest.completed.items())
        }
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
        available={
            stage: len(items)
            for stage, items in sorted(store.manifest.completed.items())
        }
        if store is not None
        else {},
        invalidated=invalidated_completed,
    )
    if run_dir is not None:
        atomic_write_json(
            run_dir / "reuse.report.json",
            {
                "mode": "resumed" if resumed else "new",
                "run_dir": str(run_dir),
                "decision": resume_report,
                "initial_completed_by_stage": initial_completed,
                "available_after_invalidation_by_stage": {
                    stage: len(items)
                    for stage, items in sorted(store.manifest.completed.items())
                }
                if store is not None
                else {},
                "invalidated_by_stage": invalidated_completed,
                "status": "running",
            },
        )
    reporter_factory = lambda: make_reporter(progress_console, effort=effort)  # noqa: E731

    cost = CostTracker(pricing=cfg.pricing)
    vision_cfg = replace(
        cfg.llm,
        model=vision_model,
        reasoning_mode="disabled",
    )
    reasoning_mode = cfg.llm.reasoning_mode
    if reasoning_mode == "auto":
        reasoning_mode = "enabled"
    reasoning_cfg = replace(
        cfg.llm,
        model=reasoning_model,
        reasoning_mode=reasoning_mode,
    )
    vision_llm = LLMClient(vision_cfg, budgets=cfg.budgets)
    reasoning_llm = LLMClient(reasoning_cfg, budgets=cfg.budgets)
    vision_llm.reset_retry_counter()
    reasoning_llm.reset_retry_counter()

    # 1. Inspect pages and persist immutable native evidence.
    evidence_pages, page_states = _inspect_pages(
        source=source,
        diagram=diagram,
        store=store,
        run_dir=run_dir,
        reporter=reporter_factory(),
    )
    # 2. Resolve only explicitly selected or deterministically classified legend pages.
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
            )
            resolution = routed.resolution
            legend_pack = resolution.pack
            legend_source = resolution.source
            legend_reporter.on_phase_end(
                detail=f"{len(legend_pack.entries)} entries · source={legend_source}"
            )
    except Exception as exc:  # noqa: BLE001 - built-in pack is a safe fallback
        if is_non_retryable_api_error(exc):
            raise
        legend_pack = load_builtin_pack(symbol_standard)
        legend_source = f"fallback_builtin(error={exc!r})"
    _checkpoint_cost(run_dir, prior_cost, cost)

    legend_summary = [
        {
            "label": entry.label,
            "kind": entry.kind,
            "symbol_class": entry.symbol_class,
            "description": entry.description or "",
            "attributes": dict(entry.attributes),
        }
        for entry in legend_pack.entries
    ]
    legend_visual_entries = [entry.model_dump(mode="json") for entry in legend_pack.entries]
    fallback_legend_line_images = [
        {
            "label": entry.label,
            "description": entry.description or "",
            "image_b64": entry.image_b64,
        }
        for entry in legend_pack.entries
        if entry.kind == "line" and entry.image_b64
    ]
    native_legend_line_images = _native_line_legend_images(
        source=source,
        pages=evidence_pages,
        legend_pack=legend_pack,
    )
    native_labels = {_legend_text_key(entry["label"]) for entry in native_legend_line_images}
    legend_line_images = [
        *native_legend_line_images,
        *(
            entry
            for entry in fallback_legend_line_images
            if _legend_text_key(entry["label"]) not in native_labels
        ),
    ]

    # 3. Deterministic full-page crop coverage and low-thinking perception.
    detections, per_page_status, perception_call_counts = _run_perception(
        source=source,
        pages=evidence_pages,
        cfg=cfg,
        client=vision_llm,
        cost=cost,
        reporter=reporter_factory(),
        store=store,
        legend_summary=legend_summary,
        run_dir=run_dir,
        prior_cost=prior_cost,
    )

    # 4. Fuse overlapping object observations exactly once.
    object_fusion = fuse_objects(
        source_name=diagram.name,
        pages=evidence_pages,
        detections=detections,
        per_page_status=per_page_status,
        legend_pack=legend_pack,
    )
    if store is not None:
        store.write_json_artifact(
            "assembly",
            "objects",
            {"nodes": [node.model_dump(mode="json") for node in object_fusion.graph.nodes]},
        )

    # 5. Resolve only ambiguous small glyphs attached to valve bodies, using
    # project-specific legend crops and page context before topology can snap
    # symbol strokes as process connections.
    contextual_results, contextual_calls = _run_contextual_resolution(
        source=source,
        pages=evidence_pages,
        nodes=object_fusion.graph.nodes,
        legend_entries=legend_visual_entries,
        client=vision_llm,
        cost=cost,
        reporter=reporter_factory(),
        store=store,
        per_page_status=per_page_status,
        run_dir=run_dir,
        prior_cost=prior_cost,
    )
    object_fusion = apply_contextual_results(object_fusion, contextual_results)
    if store is not None:
        store.write_json_artifact(
            "assembly",
            "contextual_objects",
            {"nodes": [node.model_dump(mode="json") for node in object_fusion.graph.nodes]},
        )

    # 6. Build deterministic topology candidates from PDF/raster line evidence.
    topology_results = _run_topology(
        source=source,
        pages=evidence_pages,
        nodes=object_fusion.graph.nodes,
        reporter=reporter_factory(),
        store=store,
        per_page_status=per_page_status,
    )
    # 7. Collect bounded, non-thinking visual facts for recovered line candidates.
    line_evidence, line_evidence_calls = _run_line_evidence(
        source=source,
        pages=evidence_pages,
        topology=topology_results,
        nodes=object_fusion.graph.nodes,
        client=vision_llm,
        cost=cost,
        reporter=reporter_factory(),
        store=store,
        per_page_status=per_page_status,
        run_dir=run_dir,
        prior_cost=prior_cost,
        legend_line_images=legend_line_images,
    )
    # 8. Resolve only the remaining semantic relationships from structured evidence.
    page_graph_results, page_graph_calls = _run_page_graphs(
        source=source,
        pages=evidence_pages,
        topology=topology_results,
        nodes=object_fusion.graph.nodes,
        client=reasoning_llm,
        cost=cost,
        reporter=reporter_factory(),
        store=store,
        per_page_status=per_page_status,
        run_dir=run_dir,
        prior_cost=prior_cost,
        effort=effort,
        legend_summary=legend_summary,
        legend_line_images=legend_line_images,
        line_evidence=line_evidence,
        include_visual_context=False,
    )
    fusion = assemble_graph(
        objects=object_fusion,
        pages=evidence_pages,
        topology=topology_results,
        page_graph_results=page_graph_results,
        per_page_status=per_page_status,
    )
    graph = fusion.graph
    _checkpoint_cost(run_dir, prior_cost, cost)

    native_text_inventory = build_native_text_inventory(
        pages=evidence_pages,
        graph=graph,
        legend_pack=legend_pack,
    )
    quality = assess_quality(
        graph=graph,
        pages=evidence_pages,
        topology=topology_results,
        native_text_inventory=native_text_inventory,
    )

    # 9. Existing deterministic DEXPI build, semantic validation, JSON and XML.
    dexpi_stats: dict[str, Any] = {}
    dexpi_issues: list[str] = []
    validation_issues: list[dict[str, Any]] = []
    dexpi_model = None
    dexpi_json_path: Path | None = None
    dexpi_xml_path: Path | None = None
    export_reporter = reporter_factory()
    with export_reporter:
        export_reporter.on_phase_start(name="v2 validate and export", total_items=3)
        try:
            from diagex.extractors.dexpi_builder import build_dexpi, serialize_model, validate_model

            export_reporter.on_phase_item_start(item=1, total_items=3, label="build DEXPI")
            build = build_dexpi(graph)
            dexpi_model = build.model
            dexpi_stats = dict(build.stats)
            dexpi_issues = list(build.issues)
            export_reporter.on_phase_item_end(
                detail=f"{dexpi_stats.get('segment_count', 0)} segments"
            )

            export_reporter.on_phase_item_start(item=2, total_items=3, label="semantic validation")
            validation_issues = list(validate_model(dexpi_model))
            export_reporter.on_phase_item_end(
                detail=f"{len(validation_issues)} issue(s)",
                is_error=bool(validation_issues),
            )

            export_reporter.on_phase_item_start(item=3, total_items=3, label="write JSON and XML")
            if persist:
                if out_path is not None:
                    output = Path(out_path)
                    output.parent.mkdir(parents=True, exist_ok=True)
                    serial_stem = output.name[:-5] if output.name.endswith(".json") else output.name
                    dexpi_json_path = serialize_model(dexpi_model, output.parent, serial_stem)
                elif run_dir is not None:
                    dexpi_json_path = serialize_model(dexpi_model, run_dir, "pid.dexpi")
                if run_dir is not None:
                    try:
                        from diagex.dexpi import validate as dexpi_validate
                        from diagex.dexpi.xml_io import dump as dump_xml
                        from diagex.dexpi.xml_io import load as load_xml

                        dexpi_xml_path = dump_xml(dexpi_model, run_dir / "pid.dexpi.xml")
                        # JSON validation alone cannot catch duplicate XML IDs,
                        # unresolved References, or envelope/schema failures.
                        # Parse the exact written artifact and report only
                        # error-severity findings as completion blockers.
                        parsed_xml_model = load_xml(dexpi_xml_path)
                        for issue in dexpi_validate.semantic_validate(parsed_xml_model):
                            record = {
                                "path": issue.path or "<xml-semantic>",
                                "msg": f"{issue.rule_id}: {issue.message}",
                            }
                            if issue.severity == "error":
                                validation_issues.append(record)
                            else:
                                dexpi_issues.append(
                                    f"DEXPI XML warning at {record['path']}: {record['msg']}"
                                )
                        try:
                            xsd_issues = dexpi_validate.xsd_validate(dexpi_xml_path)
                        except dexpi_validate.XmlschemaUnavailableError:
                            dexpi_issues.append(
                                "DEXPI XML XSD validation skipped: install the 'validate' extra"
                            )
                        else:
                            validation_issues.extend(
                                {
                                    "path": issue.path or "<xml-xsd>",
                                    "msg": f"{issue.rule_id}: {issue.message}",
                                }
                                for issue in xsd_issues
                                if issue.severity == "error"
                            )
                    except Exception as exc:  # noqa: BLE001 - JSON remains usable
                        validation_issues.append({"path": "<xml-roundtrip>", "msg": repr(exc)})
                        dexpi_issues.append(f"DEXPI XML serialise/validate failed: {exc!r}")
            export_reporter.on_phase_item_end(
                detail=(
                    f"json={dexpi_json_path.name if dexpi_json_path else 'none'}, "
                    f"xml={dexpi_xml_path.name if dexpi_xml_path else 'none'}"
                )
            )
        except Exception as exc:  # noqa: BLE001
            dexpi_issues.append(f"dexpi build failed: {exc!r}")
            export_reporter.on_phase_item_end(detail=repr(exc), is_error=True)
        export_reporter.on_phase_end(detail="complete")

    quality = add_dexpi_results(
        quality,
        stats=dexpi_stats,
        build_issues=dexpi_issues,
        validation_issues=validation_issues,
    )

    current_cost = cost.summary()
    current_cost["retries"] = vision_llm.retries_total + reasoning_llm.retries_total
    current_cost["tool_call_counts"] = {
        **perception_call_counts,
        "submit_contextual_symbol_corrections": contextual_calls,
        "submit_line_evidence": line_evidence_calls,
        "submit_page_graph": page_graph_calls,
    }
    current_cost["n_tool_calls"] = (
        sum(perception_call_counts.values())
        + contextual_calls
        + line_evidence_calls
        + page_graph_calls
    )
    current_cost["wall_clock_s"] = round(time.perf_counter() - started, 3)
    cost_summary = _merge_cost_summaries(prior_cost, current_cost)

    if run_dir is not None:
        atomic_write_text(
            run_dir / "evidence" / "native-text-inventory.json",
            native_text_inventory.model_dump_json(indent=2),
        )
        _write_run_artefacts(
            run_dir=run_dir,
            runs_root=run_dir.parent,
            run_id=run_id,
            stem=stem,
            effort=effort,
            model=f"vision={vision_model}; reasoning={reasoning_model}",
            graph=graph,
            cost_summary=cost_summary,
            dexpi_stats=dexpi_stats,
            dexpi_issues=dexpi_issues,
            validation_issues=validation_issues,
            dexpi_json_path=dexpi_json_path,
            legend_pack=legend_pack,
            legend_source_tag=legend_source,
            states=page_states,
            per_page_status=per_page_status,
            confidence_report_path=confidence_report_path,
            engine="evidence-v2",
        )
        atomic_write_text(
            run_dir / "quality.report.json",
            quality.model_dump_json(indent=2),
        )
        _augment_public_manifests(
            run_dir=run_dir,
            pages=evidence_pages,
            quality=quality,
            dexpi_xml_path=dexpi_xml_path,
            resumed=resumed,
        )
        if store is not None:
            store.write_json_artifact(
                "export",
                "result",
                {
                    "dexpi_json_path": str(dexpi_json_path) if dexpi_json_path else None,
                    "dexpi_xml_path": str(dexpi_xml_path) if dexpi_xml_path else None,
                    "build_issues": dexpi_issues,
                    "validation_issues": validation_issues,
                },
            )
        atomic_write_text(
            run_dir / "evidence" / "document.json",
            json.dumps(
                {
                    "schema_version": "1.0.0",
                    "source_name": diagram.name,
                    "source_sha256": source_hash,
                    "pages": [
                        {
                            "page_index": page.page_index,
                            "role": page.role,
                            "role_confidence": page.role_confidence,
                            "role_reason": page.role_reason,
                            "text_count": len(page.text_spans),
                            "path_count": len(page.paths),
                        }
                        for page in evidence_pages
                    ],
                },
                indent=2,
                ensure_ascii=False,
            ),
        )
        if store is not None:
            store.write_json_artifact("assembly", "graph", graph.model_dump(mode="json"))
            if store.manifest.errors:
                store.set_status("partial")
            else:
                store.set_status("complete")
            reuse_summary = store.reuse_summary()
            atomic_write_json(
                run_dir / "reuse.report.json",
                {
                    "mode": "resumed" if resumed else "new",
                    "run_dir": str(run_dir),
                    "decision": resume_report,
                    "initial_completed_by_stage": initial_completed,
                    "invalidated_by_stage": invalidated_completed,
                    **reuse_summary,
                    "legend_source": legend_source,
                    "status": store.manifest.status,
                },
            )
            _print_reuse_end(progress_console, summary=reuse_summary)
    elif confidence_report_path is not None:
        _write_confidence_report(
            Path(confidence_report_path),
            stem=stem,
            run_id=run_id,
            effort=effort,
            cost_summary=cost_summary,
            legend_source_tag=legend_source,
            legend_entry_count=len(legend_pack.entries),
            dexpi_stats=dexpi_stats,
            dexpi_issues=dexpi_issues,
            validation_issues=validation_issues,
            graph=graph,
            per_page_status=per_page_status,
        )

    return PidExtractionResult(
        diagram_stem=stem,
        effort=effort,
        model=f"vision={vision_model}; reasoning={reasoning_model}",
        graph=graph,
        dexpi_json_path=dexpi_json_path,
        dexpi_stats=dexpi_stats,
        dexpi_issues=dexpi_issues,
        validation_issues=validation_issues,
        legend_source=legend_source,
        legend_entry_count=len(legend_pack.entries),
        cost_summary=cost_summary,
        run_dir=run_dir,
        run_id=run_id,
        engine="evidence-v2",
        quality_status=quality.status,
    )


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
                    and public_path is not None
                    and public_path.is_file()
                ):
                    page_evidence = PageEvidence.model_validate_json(
                        public_path.read_text(encoding="utf-8")
                    )
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
                evidence.append(page_evidence)
                states.append(
                    SimpleNamespace(
                        page=page.model_copy(update={"image": None}),
                        transcript=[],
                    )
                )
                reporter.on_phase_item_end(
                    detail=(
                        f"role={page_evidence.role} ({page_evidence.role_confidence}), "
                        f"text={len(page_evidence.text_spans)}, paths={len(page_evidence.paths)}"
                    )
                )
            reporter.on_phase_end(detail=f"{len(evidence)} pages classified")
    finally:
        if pdf_doc is not None:
            pdf_doc.close()
    return evidence, states


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
) -> tuple[list[DetectionRecord], dict[int, str], dict[str, int]]:
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

    def next_step() -> int:
        # Parsing can fail after the provider has returned billable usage.  In
        # that case CostTracker already contains the attempt even though no
        # structured tool call was accepted, so use recorded steps rather than
        # successful-call counters to avoid duplicate step identifiers.
        return max((row.step for row in cost.steps), default=0) + 1

    def record_model_attempt() -> None:
        call_counts["submit_pid_objects"] += 1

    planned_total = sum(
        len(tile(rendered_page, strategy))
        for rendered_page in iter_pages(source)
        if evidence_by_index[rendered_page.page_index].role == "pid"
    )

    progress_item = 0
    with reporter:
        reporter.on_phase_start(name="v2 fixed-crop object perception", total_items=planned_total)
        for rendered_page in iter_pages(source):
            evidence = evidence_by_index[rendered_page.page_index]
            if evidence.role != "pid":
                continue
            fixed_tiles = tile(rendered_page, strategy)
            page_view_counts[evidence.page_index] = len(fixed_tiles)
            provider = ViewProvider(rendered_page, fixed_tiles)
            for current_tile in fixed_tiles:
                progress_item += 1
                item = f"p{rendered_page.page_index + 1:04d}__{current_tile.id}"
                reporter.on_phase_item_start(
                    item=progress_item,
                    total_items=planned_total,
                    label=(f"page {rendered_page.page_index + 1} · {current_tile.id}"),
                )
                try:
                    if store is not None and store.is_done("perception", item):
                        saved = store.read_json_artifact("perception", item)
                        tile_detections = [
                            DetectionRecord.model_validate(value)
                            for value in saved.get("detections", [])
                        ]
                        detail = f"checkpoint · {len(tile_detections)} objects"
                        rejected_count = len(saved.get("rejected_objects", []))
                        if rejected_count:
                            page_error_counts[evidence.page_index] += 1
                            detail += f", {rejected_count} malformed object(s) skipped"
                    else:
                        view_image, view_info = provider.get_tile(current_tile.id)
                        core = ownership_core(current_tile, fixed_tiles)
                        outcome = perceive_tile(
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
                            page_context={"coverage": "deterministic fixed grid"},
                            on_attempt=record_model_attempt,
                        )
                        tile_detections = outcome.detections
                        batch = outcome.batch
                        if store is not None:
                            store.invalidate(
                                "contextual", "topology", "line_evidence", "page_graph", "assembly", "export"
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
                                    "ownership_core": core.model_dump(mode="json"),
                                    "reason": "deterministic fixed grid",
                                    "model_attempts": outcome.attempts,
                                    "format_recovery": outcome.recovery_diagnostics,
                                },
                            )
                        _checkpoint_cost(run_dir, prior_cost, cost)
                        detail = f"{len(tile_detections)} objects"
                        if outcome.attempts > 1:
                            detail += f" · recovered after {outcome.attempts} attempts"
                        if batch.rejected_objects:
                            page_error_counts[evidence.page_index] += 1
                            detail += f", {len(batch.rejected_objects)} malformed object(s) skipped"
                    detections.extend(tile_detections)
                    reporter.on_phase_item_end(detail=detail)
                except Exception as exc:  # noqa: BLE001 - preserve other tiles and resume later
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
        reporter.on_phase_end(
            detail=(
                f"{len(detections)} raw detections; "
                f"{call_counts['submit_pid_objects']} fixed-crop calls"
            )
        )

    for page in pid_pages:
        errors = page_error_counts.get(page.page_index, 0)
        inspected = page_view_counts.get(page.page_index, 0)
        page_detections = [value for value in detections if value.page_index == page.page_index]
        if errors:
            statuses[page.page_index] = (
                "error" if not page_detections and errors >= inspected else "partial"
            )

    return detections, statuses, call_counts


def _native_line_legend_images(
    *,
    source: Any,
    pages: list[PageEvidence],
    legend_pack: LegendPack,
) -> list[dict[str, Any]]:
    """Recover complete line-style rows from vector legend pages.

    Model-produced legend boxes are deliberately tight around the glyph. For
    line samples that can clip the route to a single dash. Positioned native
    text lets us recrop the whole row deterministically from a vector PDF.
    """
    from diagex.vision.loader import iter_pages

    line_entries = [entry for entry in legend_pack.entries if entry.kind == "line"]
    if not line_entries:
        return []
    evidence_by_index = {page.page_index: page for page in pages}
    results: list[dict[str, Any]] = []
    found: set[str] = set()
    for rendered_page in iter_pages(source):
        evidence = evidence_by_index.get(rendered_page.page_index)
        if (
            evidence is None
            or evidence.role != "legend"
            or evidence.is_scanned
            or rendered_page.image is None
        ):
            continue
        for entry in line_entries:
            label_key = _legend_text_key(entry.label)
            if not label_key or label_key in found:
                continue
            span = next(
                (
                    candidate
                    for candidate in evidence.text_spans
                    if _legend_span_matches(label_key, _legend_text_key(candidate.text))
                ),
                None,
            )
            if span is None:
                continue
            height = max(1, span.bbox.h)
            bounds = (
                max(0, span.bbox.x - max(320, height * 10)),
                max(0, span.bbox.y - max(24, height)),
                min(rendered_page.image.width, span.bbox.x2 + max(100, height * 3)),
                min(rendered_page.image.height, span.bbox.y2 + max(24, height)),
            )
            if bounds[2] <= bounds[0] or bounds[3] <= bounds[1]:
                continue
            crop = rendered_page.image.crop(bounds).convert("RGB")
            buffer = io.BytesIO()
            crop.save(buffer, format="PNG", optimize=True)
            results.append(
                {
                    "label": entry.label,
                    "description": entry.description or "",
                    "image_b64": base64.b64encode(buffer.getvalue()).decode("ascii"),
                    "source": "native_vector_legend_row",
                    "page": evidence.page_index + 1,
                }
            )
            found.add(label_key)
    return results


def _legend_text_key(value: Any) -> str:
    return re.sub(r"[^a-z0-9\u4e00-\u9fff]+", "", str(value or "").casefold())


def _legend_span_matches(label_key: str, span_key: str) -> bool:
    if not span_key:
        return False
    if label_key == span_key:
        return True
    # Native PDF text may split a long wrapped legend label across two spans.
    return len(span_key) >= 4 and (label_key.startswith(span_key) or span_key.startswith(label_key))


def _run_contextual_resolution(
    *,
    source: Any,
    pages: list[PageEvidence],
    nodes: list[Any],
    legend_entries: list[dict[str, Any]],
    client: LLMClient,
    cost: CostTracker,
    reporter: Any,
    store: CheckpointStore | None,
    per_page_status: dict[int, str],
    run_dir: Path | None,
    prior_cost: dict[str, Any],
) -> tuple[list[ContextualPageResult], int]:
    """Run one project-legend comparison for each page that needs it."""
    from diagex.vision.loader import iter_pages

    nodes_by_page: dict[int, list[Any]] = {}
    for node in nodes:
        nodes_by_page.setdefault(node.page_index, []).append(node)
    eligible = {
        page.page_index
        for page in pages
        if page.role == "pid"
        and find_contextual_candidates(nodes, page_index=page.page_index)
        and any(entry.get("image_b64") and entry.get("kind") != "line" for entry in legend_entries)
    }
    if not eligible:
        return [], 0

    results: list[ContextualPageResult] = []
    calls = 0

    def next_step() -> int:
        return max((row.step for row in cost.steps), default=0) + 1

    def record_attempt() -> None:
        nonlocal calls
        calls += 1

    with reporter:
        reporter.on_phase_start(name="v2 contextual symbol resolution", total_items=len(eligible))
        item_number = 0
        for rendered_page in iter_pages(source):
            if rendered_page.page_index not in eligible:
                continue
            item_number += 1
            item = f"page-{rendered_page.page_index + 1:04d}"
            reporter.on_phase_item_start(
                item=item_number,
                total_items=len(eligible),
                label=f"page {rendered_page.page_index + 1} · project legend comparison",
            )
            try:
                if store is not None and store.is_done("contextual", item):
                    result = ContextualPageResult.model_validate(
                        store.read_json_artifact("contextual", item)
                    )
                    detail = f"checkpoint · {len(result.resolutions)} correction(s)"
                else:
                    if rendered_page.image is None:
                        raise ValueError("rendered page image unavailable")
                    result = resolve_contextual_page(
                        client=client,
                        cost_tracker=cost,
                        reporter=reporter,
                        page_index=rendered_page.page_index,
                        rendered_image=rendered_page.image,
                        nodes=nodes_by_page.get(rendered_page.page_index, []),
                        legend_entries=legend_entries,
                        step=next_step(),
                        on_attempt=record_attempt,
                    )
                    if store is not None:
                        store.invalidate("topology", "line_evidence", "page_graph", "assembly", "export")
                        store.write_json_artifact(
                            "contextual", item, result.model_dump(mode="json")
                        )
                    _checkpoint_cost(run_dir, prior_cost, cost)
                    detail = (
                        f"corrections={len(result.resolutions)}, "
                        f"uncertainties={sum(1 for value in result.conflicts if value.get('status') == 'unresolved')}"
                    )
                    if result.attempts > 1:
                        detail += f" · recovered after {result.attempts} attempts"
                results.append(result)
                reporter.on_phase_item_end(detail=detail)
            except Exception as exc:  # noqa: BLE001 - preserve fused objects
                if per_page_status.get(rendered_page.page_index) == "ok":
                    per_page_status[rendered_page.page_index] = "partial"
                if store is not None:
                    store.mark_error("contextual", item, repr(exc))
                _checkpoint_cost(run_dir, prior_cost, cost)
                reporter.on_phase_item_end(detail=repr(exc), is_error=True)
                if is_non_retryable_api_error(exc):
                    raise
        reporter.on_phase_end(
            detail=f"{sum(len(result.resolutions) for result in results)} applied correction(s); {calls} call(s)"
        )
    return results, calls


def _run_topology(
    *,
    source: Any,
    pages: list[PageEvidence],
    nodes: list[Any],
    reporter: Any,
    store: CheckpointStore | None,
    per_page_status: dict[int, str],
) -> list[TopologyResult]:
    from diagex.vision.loader import iter_pages

    page_by_index = {page.page_index: page for page in pages}
    nodes_by_page: dict[int, list[Any]] = {}
    for node in nodes:
        nodes_by_page.setdefault(node.page_index, []).append(node)
    results: list[TopologyResult] = []
    with reporter:
        reporter.on_phase_start(name="v2 deterministic topology", total_items=len(pages))
        for rendered_page in iter_pages(source):
            evidence = page_by_index[rendered_page.page_index]
            item = f"page-{rendered_page.page_index + 1:04d}"
            reporter.on_phase_item_start(
                item=rendered_page.page_index + 1,
                total_items=len(pages),
                label=f"page {rendered_page.page_index + 1} · {evidence.role}",
            )
            if evidence.role != "pid":
                result = TopologyResult(page_index=rendered_page.page_index)
            elif store is not None and store.is_done("topology", item):
                result = TopologyResult.model_validate(store.read_json_artifact("topology", item))
            else:
                result = build_page_topology(
                    page=evidence,
                    nodes=nodes_by_page.get(rendered_page.page_index, []),
                    raster_image=rendered_page.image,
                )
                if store is not None:
                    store.write_json_artifact("topology", item, result.model_dump(mode="json"))
            if (
                evidence.role == "pid"
                and result.warnings
                and len(nodes_by_page.get(rendered_page.page_index, [])) > 1
            ):
                if per_page_status.get(rendered_page.page_index) == "ok":
                    per_page_status[rendered_page.page_index] = "partial"
            results.append(result)
            reporter.on_phase_item_end(
                detail=(
                    f"edges={len(result.edges)}, used_paths={len(result.used_path_ids)}, "
                    f"styled_runs={len(result.line_style_evidence)}, "
                    f"ambiguities={len(result.ambiguities)}"
                )
            )
        reporter.on_phase_end(detail=f"{sum(len(result.edges) for result in results)} edges")
    return results


def _run_line_evidence(
    *,
    source: Any,
    pages: list[PageEvidence],
    topology: list[TopologyResult],
    nodes: list[Any],
    client: LLMClient,
    cost: CostTracker,
    reporter: Any,
    store: CheckpointStore | None,
    per_page_status: dict[int, str],
    run_dir: Path | None,
    prior_cost: dict[str, Any],
    legend_line_images: list[dict[str, Any]],
) -> tuple[list[PageLineEvidence], int]:
    """Run one bounded non-thinking visual line pass per non-empty P&ID page."""
    from diagex.vision.loader import iter_pages

    page_by_index = {page.page_index: page for page in pages}
    topology_by_page = {result.page_index: result for result in topology}
    nodes_by_page: dict[int, list[Any]] = {}
    for node in nodes:
        nodes_by_page.setdefault(node.page_index, []).append(node)
    eligible = [
        page
        for page in pages
        if page.role == "pid"
        and topology_by_page.get(page.page_index, TopologyResult(page_index=page.page_index)).edges
    ]
    results: list[PageLineEvidence] = []
    calls = 0

    def next_step() -> int:
        return max((row.step for row in cost.steps), default=0) + 1

    def record_attempt() -> None:
        nonlocal calls
        calls += 1

    with reporter:
        reporter.on_phase_start(
            name="v2 non-thinking visual line evidence", total_items=len(eligible)
        )
        progress_item = 0
        for rendered_page in iter_pages(source):
            evidence = page_by_index[rendered_page.page_index]
            page_topology = topology_by_page.get(
                rendered_page.page_index,
                TopologyResult(page_index=rendered_page.page_index),
            )
            if evidence.role != "pid" or not page_topology.edges:
                continue
            progress_item += 1
            item = f"page-{rendered_page.page_index + 1:04d}"
            reporter.on_phase_item_start(
                item=progress_item,
                total_items=len(eligible),
                label=f"page {rendered_page.page_index + 1} · visible line facts",
            )
            try:
                if store is not None and store.is_done("line_evidence", item):
                    result = PageLineEvidence.model_validate(
                        store.read_json_artifact("line_evidence", item)
                    )
                    detail = f"checkpoint · {len(result.assessments)} candidates"
                else:
                    if rendered_page.image is None:
                        raise ValueError("rendered page image unavailable")
                    result = classify_page_line_evidence(
                        client=client,
                        cost_tracker=cost,
                        reporter=reporter,
                        page=evidence,
                        rendered_image=rendered_page.image,
                        nodes=nodes_by_page.get(rendered_page.page_index, []),
                        topology=page_topology,
                        step=next_step(),
                        legend_line_images=legend_line_images,
                        max_tokens=max(2500, min(6000, 800 + len(page_topology.edges) * 90)),
                        on_attempt=record_attempt,
                    )
                    if store is not None:
                        store.invalidate("page_graph", "assembly", "export")
                        store.write_json_artifact(
                            "line_evidence", item, result.model_dump(mode="json")
                        )
                    _checkpoint_cost(run_dir, prior_cost, cost)
                    detail = (
                        f"assessed={len(result.assessments)}, diagnostics={len(result.diagnostics)}"
                    )
                    if result.format_recovery:
                        detail += " · recovered after 2 attempts"
                results.append(result)
                reporter.on_phase_item_end(detail=detail)
            except Exception as exc:  # noqa: BLE001 - preserve topology and continue cautiously
                if per_page_status.get(evidence.page_index) == "ok":
                    per_page_status[evidence.page_index] = "partial"
                if store is not None:
                    diagnostics = getattr(exc, "diagnostics", None)
                    if diagnostics:
                        atomic_write_json(
                            store.artifact_path("line_evidence_errors", item),
                            {
                                "error": str(exc),
                                "attempts": getattr(exc, "attempts", 1),
                                "invalid_responses": diagnostics,
                            },
                        )
                    store.mark_error("line_evidence", item, repr(exc))
                _checkpoint_cost(run_dir, prior_cost, cost)
                reporter.on_phase_item_end(detail=repr(exc), is_error=True)
                if is_non_retryable_api_error(exc):
                    raise
        reporter.on_phase_end(
            detail=f"{len(results)}/{len(eligible)} pages assessed; {calls} model calls"
        )
    return results, calls


def _run_page_graphs(
    *,
    source: Any,
    pages: list[PageEvidence],
    topology: list[TopologyResult],
    nodes: list[Any],
    client: LLMClient,
    cost: CostTracker,
    reporter: Any,
    store: CheckpointStore | None,
    per_page_status: dict[int, str],
    run_dir: Path | None,
    prior_cost: dict[str, Any],
    effort: EffortLevel,
    legend_summary: list[dict[str, Any]],
    legend_line_images: list[dict[str, Any]],
    line_evidence: list[PageLineEvidence],
    include_visual_context: bool,
) -> tuple[list[PageGraphResult], int]:
    """Run one relationship solve for each non-empty P&ID page."""
    from diagex.vision.loader import iter_pages

    page_by_index = {page.page_index: page for page in pages}
    topology_by_page = {result.page_index: result for result in topology}
    line_evidence_by_page = {result.page_index: result for result in line_evidence}
    nodes_by_page: dict[int, list[Any]] = {}
    for node in nodes:
        nodes_by_page.setdefault(node.page_index, []).append(node)
    eligible = [page for page in pages if page.role == "pid" and nodes_by_page.get(page.page_index)]
    results: list[PageGraphResult] = []
    calls = 0

    def next_step() -> int:
        return max((row.step for row in cost.steps), default=0) + 1

    def record_page_graph_attempt() -> None:
        nonlocal calls
        calls += 1

    with reporter:
        reporter.on_phase_start(name="v2 page relationship solving", total_items=len(eligible))
        progress_item = 0
        for rendered_page in iter_pages(source):
            evidence = page_by_index[rendered_page.page_index]
            local_nodes = nodes_by_page.get(rendered_page.page_index, [])
            if evidence.role != "pid" or not local_nodes:
                continue
            progress_item += 1
            item = f"page-{rendered_page.page_index + 1:04d}"
            reporter.on_phase_item_start(
                item=progress_item,
                total_items=len(eligible),
                label=f"page {rendered_page.page_index + 1} · typed relationships",
            )
            try:
                if store is not None and store.is_done("page_graph", item):
                    result = PageGraphResult.model_validate(
                        store.read_json_artifact("page_graph", item)
                    )
                    detail = f"checkpoint · {len(result.edges)} edges"
                else:
                    if rendered_page.image is None:
                        raise ValueError("rendered page image unavailable")
                    result = solve_page_graph(
                        client=client,
                        cost_tracker=cost,
                        reporter=reporter,
                        page=evidence,
                        rendered_image=rendered_page.image,
                        nodes=local_nodes,
                        all_nodes=nodes,
                        topology=topology_by_page.get(
                            rendered_page.page_index,
                            TopologyResult(page_index=rendered_page.page_index),
                        ),
                        pages=pages,
                        step=next_step(),
                        output_effort=EFFORT_PROFILES[effort].api_effort,
                        max_tokens=max(6000, EFFORT_PROFILES[effort].max_output_tokens),
                        legend_summary=legend_summary,
                        legend_line_images=legend_line_images,
                        visual_evidence=line_evidence_by_page.get(rendered_page.page_index),
                        on_attempt=record_page_graph_attempt,
                        include_visual_context=include_visual_context,
                    )
                    if store is not None:
                        store.invalidate("assembly", "export")
                        store.write_json_artifact(
                            "page_graph", item, result.model_dump(mode="json")
                        )
                    _checkpoint_cost(run_dir, prior_cost, cost)
                    detail = (
                        f"edges={len(result.edges)}, conflicts={len(result.conflicts)}, "
                        f"rejected_output={len(result.diagnostics)}"
                    )
                    if result.format_recovery:
                        detail += " · recovered after 2 attempts"
                results.append(result)
                reporter.on_phase_item_end(detail=detail)
            except Exception as exc:  # noqa: BLE001 - preserve objects/topology
                if per_page_status.get(evidence.page_index) == "ok":
                    per_page_status[evidence.page_index] = "partial"
                if store is not None:
                    diagnostics = getattr(exc, "diagnostics", None)
                    if diagnostics:
                        atomic_write_json(
                            store.artifact_path("page_graph_errors", item),
                            {
                                "error": str(exc),
                                "attempts": getattr(exc, "attempts", 1),
                                "invalid_responses": diagnostics,
                            },
                        )
                    store.mark_error("page_graph", item, repr(exc))
                _checkpoint_cost(run_dir, prior_cost, cost)
                reporter.on_phase_item_end(detail=repr(exc), is_error=True)
                if is_non_retryable_api_error(exc):
                    raise
        reporter.on_phase_end(
            detail=f"{len(results)}/{len(eligible)} pages solved; {calls} model calls"
        )
    return results, calls


def _prepare_v2_run_dir(cfg: Config, stem: str, vision_model: str) -> tuple[Path, str]:
    runs_root = cfg.runs_dir / stem
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = _new_run_id()
    run_dir = runs_root / f"{_timestamp()}_{_safe_model_name(vision_model)}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "evidence").mkdir(exist_ok=True)
    return run_dir, run_id


def _stage_count_text(values: dict[str, int]) -> str:
    if not values:
        return "none"
    return ", ".join(f"{stage}={count}" for stage, count in sorted(values.items()))


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
        "[diagex.cache] final checkpoint reuse: "
        f"{summary['reused_total']} reused vs {summary['computed_total']} computed "
        f"({summary['reuse_percent']:.1f}% reused)"
    )
    console.print(
        "[diagex.cache] reused by stage: "
        + _stage_count_text(summary["reused_by_stage"])
    )
    console.print(
        "[diagex.cache] computed by stage: "
        + _stage_count_text(summary["computed_by_stage"])
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
        "engine_schema": "3.5.0",
        "transport": cfg.llm.transport,
        "vision_model": vision_model,
        "reasoning_model": reasoning_model,
        "reasoning_mode": cfg.llm.reasoning_mode,
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
        "page_graph_pipeline": "1.7.0",
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


def _checkpoint_cost(
    run_dir: Path | None,
    prior: dict[str, Any],
    current: CostTracker,
) -> None:
    if run_dir is None:
        return
    atomic_write_text(
        run_dir / "cost.json",
        json.dumps(_merge_cost_summaries(prior, current.summary()), indent=2, sort_keys=True),
    )


def _augment_public_manifests(
    *,
    run_dir: Path,
    pages: list[PageEvidence],
    quality: QualityReport,
    dexpi_xml_path: Path | None,
    resumed: bool,
) -> None:
    pages_path = run_dir / "pages.json"
    try:
        pages_value = json.loads(pages_path.read_text(encoding="utf-8"))
        evidence_by_index = {page.page_index: page for page in pages}
        for row in pages_value.get("pages", []):
            evidence = evidence_by_index.get(int(row.get("page_index", -1)))
            if evidence is None:
                continue
            row.update(
                {
                    "role": evidence.role,
                    "role_confidence": evidence.role_confidence,
                    "role_reason": evidence.role_reason,
                    "fail_open": evidence.fail_open,
                    "native_text_count": len(evidence.text_spans),
                    "native_path_count": len(evidence.paths),
                }
            )
        atomic_write_text(
            pages_path,
            json.dumps(pages_value, indent=2, ensure_ascii=False),
        )
    except (OSError, ValueError, TypeError):
        pass

    result_path = run_dir / "result.json"
    try:
        result_value = json.loads(result_path.read_text(encoding="utf-8"))
        result_value.update(
            {
                "quality_status": quality.status,
                "quality_report_path": str(run_dir / "quality.report.json"),
                "dexpi_xml_path": str(dexpi_xml_path) if dexpi_xml_path else None,
                "resumed": resumed,
                "reuse_report_path": str(run_dir / "reuse.report.json"),
            }
        )
        atomic_write_text(
            result_path,
            json.dumps(result_value, indent=2, ensure_ascii=False),
        )
    except (OSError, ValueError, TypeError):
        pass
