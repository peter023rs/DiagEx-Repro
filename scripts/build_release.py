#!/usr/bin/env python3
"""Assemble the public reproducibility package for the diagex manuscript.

Reads canonical artefacts from this repo and writes a clean two-tier release
tree under ``release/``:

    release/diagex-repro/                  Tier A — light GitHub-ready repo
    release/diagex-repro-supplementary/    Tier B — Zenodo supplementary staging
    release/diagex-repro-supplementary.zip Tier B archive ready for upload

The script is idempotent: re-running it from scratch produces the same tree
(modulo file mtimes). It does not touch the source repo's canonical paths.

Plan reference: ``plan/etfa2026-reproducibility-package.md`` (filename
retained from git history; the plan describes the diagex reproducibility
package and is not venue-coupled).
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import shutil
import sys
import zipfile
from collections import defaultdict
from collections.abc import Iterable
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = REPO_ROOT / "scripts" / "release_templates"

TIER_A_DIRNAME = "diagex-repro"
TIER_B_DIRNAME = "diagex-repro-supplementary"

# --- Tier A: file-set knobs ---------------------------------------------------

# Eval modules that go into Tier A under ``code/eval/``. Anything not listed
# here is dropped (we strip e.g. ``__pycache__`` and stale snapshots).
TIER_A_EVAL_MODULES = [
    "__init__.py",
    "_loader.py",
    "aggregate.py",
    "conditions.py",
    "gpt_singleshot.py",
    "latex_tables.py",
    "qa_analysis.py",
    "rater_action_rates.py",
    "report_md.py",
    "rescore.py",
    "run_paper_eval.py",
    "scoring.py",
]

# Scripts kept in Tier A under ``code/scripts/`` (the plan's keep-list).
TIER_A_SCRIPTS = [
    "build_release.py",
    "gpt41_dry_run.py",
    "measure_retention.py",
    "phase2_diagnostics.py",
    "record_cassettes.py",
    "rerender_eval_artifacts.py",
    "rerun_one_query.py",
    "rescore_phase1_inplace.py",
    "rescore_phase2.py",
    "stabilise_phase2.py",
]

# Unit tests we ship in Tier A. Two groups: eval-harness tests (so reviewers
# can validate the harness) and DEXPI 2.0 layer tests (so they can validate
# our AGPL-free DEXPI replacement without the [codegen] extra).
TIER_A_UNIT_TESTS = [
    "test_eval_aggregate.py",
    "test_eval_run_cassette.py",
    "test_eval_scoring.py",
    "test_vision_encode.py",
    # DEXPI 2.0 layer
    "test_dexpi_builder.py",
    "test_dexpi_builder_coverage.py",
    "test_dexpi_codegen.py",
    "test_dexpi_concrete_fallback.py",
    "test_dexpi_drawio.py",
    "test_dexpi_extensions.py",
    "test_dexpi_json_io.py",
    "test_dexpi_model_namespaces.py",
    "test_dexpi_process.py",
    "test_dexpi_quantities.py",
    "test_dexpi_refs.py",
    "test_dexpi_schema.py",
    "test_dexpi_svg.py",
    "test_dexpi_validate.py",
    "test_dexpi_xml_io.py",
]

# Files inside ``eval/datasets/<stem>/`` to keep verbatim. The
# ``graph.bootstrap*.json`` intermediates are stripped (truth supersedes them
# per plan §10).
GROUND_TRUTH_KEEP = {
    "annotations.truth.jsonl",
    "graph.truth.json",
    "graph.truth.svg",
    "graph.truth.history.json",
    "graph.truth.debug.md",
    "meta.yaml",
    "queries.truth.yaml",
    "via_correction.summary.json",
}

# Files inside out/diagex-{phase1,phase2,ablation,gpt41}/ to keep at the top
# level (under results/<bucket>/). Snapshot CSVs are stripped.
TIER_A_RESULTS_KEEP_FILES = {
    "results.csv",
    "report.md",
    "invocation.txt",
    "qa_analysis.xlsx",
    "delta_vs_baseline.md",
    "rater_action_rates.json",
}
TIER_A_RESULTS_KEEP_DIRS = {"tables", "figures", "diagnostics"}

# --- Tier B: per-run artefact set --------------------------------------------

# Per-run files we keep in Tier B. We do NOT keep the full ``tiles/`` dir for
# every run (would balloon the archive); we keep the canonical artefacts the
# manuscript references.
TIER_B_RUN_KEEP_FILES = {
    # Phase 1 (under runs/<fixture>/<run>)
    "answer.md",
    "cost.json",
    "query.txt",
    "result.json",
    "transcript.jsonl",
    # Phase 2 / ablation extras
    "arbitration.jsonl",
    "confidence_report.html",
    "debug_report.md",
    "graph.json",
    "legend.json",
    "pid.pydexpi.json",
    "pid.svg",
}


# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def log(msg: str) -> None:
    print(f"[build_release] {msg}", flush=True)


def reset_dir(path: Path) -> None:
    if path.exists():
        shutil.rmtree(path)
    path.mkdir(parents=True)


def copy_file(src: Path, dst: Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def copy_tree(src: Path, dst: Path, *, ignore: Iterable[str] | None = None) -> None:
    """Recursive copy with __pycache__ and editor cruft stripped."""
    ignore_names = set(ignore or ())
    ignore_names.update({"__pycache__", ".pytest_cache", ".DS_Store", "Thumbs.db"})

    def _ignore(_dir: str, names: list[str]) -> list[str]:
        return [n for n in names if n in ignore_names or n.endswith(".pyc")]

    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src, dst, ignore=_ignore)


def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(64 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def dir_size_mb(path: Path) -> float:
    total = 0
    for f in path.rglob("*"):
        if f.is_file():
            total += f.stat().st_size
    return total / (1024 * 1024)


def filter_run_dir(src_run: Path, dst_run: Path) -> None:
    """Copy a per-fixture run dir, keeping only TIER_B_RUN_KEEP_FILES."""
    dst_run.mkdir(parents=True, exist_ok=True)
    for child in src_run.iterdir():
        if child.is_file() and child.name in TIER_B_RUN_KEEP_FILES:
            copy_file(child, dst_run / child.name)


def latest_run_dir_per_fixture(runs_root: Path) -> dict[str, Path]:
    """Map fixture name → most recent <timestamp>_r-<short> dir under runs_root.

    Selection key is the directory NAME (which starts with an ISO-format
    timestamp like ``2026-04-27T14-49-56``), not filesystem mtime — bulk
    file rewrites elsewhere in the repo can bump mtimes uniformly and break
    mtime-based ordering. Lexicographic order on the timestamp prefix
    matches chronological order.

    For Phase 2 layouts (out/diagex-phase2/baseline/runs/<fixture>/...).
    """
    out: dict[str, Path] = {}
    if not runs_root.exists():
        return out
    for fixture_dir in runs_root.iterdir():
        if not fixture_dir.is_dir():
            continue
        candidates = [d for d in fixture_dir.iterdir()
                      if d.is_dir() and d.name.startswith("2026-")]
        if not candidates:
            continue
        out[fixture_dir.name] = max(candidates, key=lambda p: p.name)
    return out


def _is_phase1_query_run(run_dir: Path) -> bool:
    """A Phase 1 query-run has query.txt + answer.md but no pid.pydexpi.json
    (which would mark it as a Phase 2 extract-pid run; runs/ is shared by
    both code paths in the source repo)."""
    return (
        (run_dir / "query.txt").exists()
        and (run_dir / "answer.md").exists()
        and not (run_dir / "pid.pydexpi.json").exists()
    )


def latest_runs_per_fixture_phase1(runs_root: Path, *, per_fixture_limit: int = 4
                                   ) -> dict[str, list[Path]]:
    """For Phase 1 (runs/<fixture>/<query-run>) keep the N most recent runs
    that look like query-runs (not extract-pid runs).

    Sorts by directory NAME (timestamp prefix) for the same reason as
    ``latest_run_dir_per_fixture`` — robust against mtime bumps from bulk
    rewrites.
    """
    out: dict[str, list[Path]] = {}
    if not runs_root.exists():
        return out
    for fixture_dir in runs_root.iterdir():
        if not fixture_dir.is_dir():
            continue
        candidates = sorted(
            [d for d in fixture_dir.iterdir()
             if d.is_dir() and d.name.startswith("2026-")
             and _is_phase1_query_run(d)],
            key=lambda p: p.name,
            reverse=True,
        )
        if candidates:
            out[fixture_dir.name] = candidates[:per_fixture_limit]
    return out


def fixtures_in_results_csv(csv_path: Path) -> set[str]:
    fixtures: set[str] = set()
    with csv_path.open(newline="", encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            f = row.get("fixture", "").strip()
            if f:
                fixtures.add(f)
    return fixtures


def corpus_fixture_stems(manifest_path: Path) -> set[str]:
    """Authoritative corpus list from eval/datasets/manifest.yaml.

    Tier B run-dir picks must filter against this — runs/ in the source repo
    contains exploration runs for fixtures that never made the corpus
    (desalination2, nitrates*, h2first1, ...). Those are not paper evidence.
    """
    import yaml  # local import: pyyaml is already a runtime dep.
    with manifest_path.open(encoding="utf-8") as fh:
        doc = yaml.safe_load(fh)
    return {fx["stem"] for fx in doc.get("fixtures", []) if "stem" in fx}


# -----------------------------------------------------------------------------
# Tier A — assembly
# -----------------------------------------------------------------------------

def build_tier_a(release_root: Path) -> Path:
    """Assemble release/diagex-repro/. Returns the Tier A root path."""
    tier_a = release_root / TIER_A_DIRNAME
    reset_dir(tier_a)
    log(f"writing Tier A under {tier_a}")

    # 1. Repo-root metadata copied verbatim.
    for name in ("LICENSE", "NOTICE", "pyproject.toml"):
        src = REPO_ROOT / name
        if not src.exists():
            log(f"WARNING: {name} missing at repo root — skipping")
            continue
        copy_file(src, tier_a / name)

    # 2. Files authored from templates.
    template_files = [
        ("README.md", "README.md"),
        ("CITATION.cff", "CITATION.cff"),
        (".zenodo.json", ".zenodo.json"),
        ("docs/REPRODUCE.md", "docs/REPRODUCE.md"),
        ("docs/DATA_CARD.md", "docs/DATA_CARD.md"),
        ("docs/ARCHITECTURE.md", "docs/ARCHITECTURE.md"),
        ("docs/VIA_WORKFLOW.md", "docs/VIA_WORKFLOW.md"),
        ("results/README.md", "results/README.md"),
    ]
    for tpl_rel, dst_rel in template_files:
        src = TEMPLATES_DIR / tpl_rel
        if not src.exists():
            log(f"WARNING: template missing: {src}")
            continue
        copy_file(src, tier_a / dst_rel)

    # 3. .gitignore for the public repo.
    (tier_a / ".gitignore").write_text(
        "# Reproducibility-package gitignore\n"
        "__pycache__/\n*.pyc\n.venv/\n.pytest_cache/\n"
        ".ruff_cache/\n.mypy_cache/\n.coverage\n.idea/\n.vscode/\n"
        "build/\ndist/\n*.egg-info/\n",
        encoding="utf-8",
    )

    # 4. Paper PDF — neutral filename per user direction (manuscript under
    #    review, do not associate with diagex).
    paper_dir = tier_a / "paper"
    paper_dir.mkdir(parents=True, exist_ok=True)
    candidates = [
        REPO_ROOT / "paper" / "manuscript.pdf",
        REPO_ROOT / "manuscript.pdf",
    ]
    for cand in candidates:
        if cand.exists():
            copy_file(cand, paper_dir / "manuscript.pdf")
            log(f"included manuscript: {cand}")
            break
    else:
        (paper_dir / "MANUSCRIPT_PLACEHOLDER.txt").write_text(
            "The manuscript PDF is not yet bundled. Drop it at\n"
            "  paper/manuscript.pdf\n"
            "(in the source repo, at the location the build script expects)\n"
            "and re-run scripts/build_release.py.\n",
            encoding="utf-8",
        )
        log("manuscript.pdf not found — placeholder written")

    # The evaluation plan ships as design context (renamed to drop the
    # venue tag — paper is under review, do not commit to a venue here).
    eval_plan = REPO_ROOT / "plan" / "etfa2026-evaluation-plan.md"
    if eval_plan.exists():
        copy_file(eval_plan, paper_dir / "evaluation-plan.md")

    # 5. src/diagex/ — entire tree (mirrors source repo layout so
    #    ``pip install -e .`` and ``pyproject.toml`` work as-is).
    #    Includes diagex/dexpi/_generated and diagex/dexpi/codegen/vendored
    #    (CC-BY 4.0). Strip src/diagex/ui (out of paper scope per plan).
    copy_tree(
        REPO_ROOT / "src" / "diagex",
        tier_a / "src" / "diagex",
        ignore={"ui"},
    )

    # 6. eval/ — only the modules listed; figures + cassettes dirs as-is;
    #    datasets handled in step 8 below.
    eval_src = REPO_ROOT / "eval"
    eval_dst = tier_a / "eval"
    eval_dst.mkdir(parents=True, exist_ok=True)
    for mod in TIER_A_EVAL_MODULES:
        src = eval_src / mod
        if src.exists():
            copy_file(src, eval_dst / mod)
        else:
            log(f"WARNING: eval module missing: {mod}")
    figures_src = eval_src / "figures"
    if figures_src.exists():
        copy_tree(figures_src, eval_dst / "figures")

    # 7. scripts/ — keep-list only.
    scripts_dst = tier_a / "scripts"
    scripts_dst.mkdir(parents=True, exist_ok=True)
    for s in TIER_A_SCRIPTS:
        src = REPO_ROOT / "scripts" / s
        if src.exists():
            copy_file(src, scripts_dst / s)
        else:
            log(f"WARNING: script missing: {s}")
    # Also ship the release_templates so the build is auditable end-to-end.
    copy_tree(TEMPLATES_DIR, scripts_dst / "release_templates")

    # 8. eval/datasets/ — manifest + per-fixture truth files (strip
    #    bootstrap intermediates). Same path as the source repo so the
    #    eval harness's default --fixtures resolution works without a flag.
    gt_src_root = REPO_ROOT / "eval" / "datasets"
    gt_dst_root = tier_a / "eval" / "datasets"
    gt_dst_root.mkdir(parents=True, exist_ok=True)
    for top in ("manifest.yaml", "_retention.v0.2.json"):
        s = gt_src_root / top
        if s.exists():
            copy_file(s, gt_dst_root / top)
    for fixture_dir in sorted(gt_src_root.iterdir()):
        if not fixture_dir.is_dir():
            continue
        if fixture_dir.name.startswith("_") or fixture_dir.name.startswith("."):
            continue
        for f in fixture_dir.iterdir():
            if f.is_file() and f.name in GROUND_TRUTH_KEEP:
                copy_file(f, gt_dst_root / fixture_dir.name / f.name)

    # 9. tests/p-ids-public/ — the 10 public PDFs plus SOURCES.md (same
    #    path as in the source repo so cassette/eval defaults resolve).
    pdf_src_root = REPO_ROOT / "tests" / "p-ids-public"
    pdf_dst_root = tier_a / "tests" / "p-ids-public"
    if pdf_src_root.exists():
        for pdf in sorted(pdf_src_root.glob("*.pdf")):
            copy_file(pdf, pdf_dst_root / pdf.name)
        sources_md = pdf_src_root / "SOURCES.md"
        if sources_md.exists():
            copy_file(sources_md, pdf_dst_root / "SOURCES.md")

    # 10. data/two_tanks_hires.png — illustration asset referenced by
    #     paper/evaluation-plan.md §10 step 12 (kept under data/ rather
    #     than tools/via/images/ to avoid pulling the whole VIA toolchain).
    src_png = REPO_ROOT / "tools" / "via" / "images" / "two-tanks.png"
    if src_png.exists():
        copy_file(src_png, tier_a / "data" / "two_tanks_hires.png")

    # 11. eval/cassettes/ — verbatim, same path as source repo.
    cassette_src = REPO_ROOT / "eval" / "cassettes"
    if cassette_src.exists():
        copy_tree(cassette_src, tier_a / "eval" / "cassettes")

    # 12. results/<bucket>/ — selectively from out/diagex-*.
    bucket_map = {
        "phase1": REPO_ROOT / "out" / "diagex-phase1",
        "phase2": REPO_ROOT / "out" / "diagex-phase2",
        "ablation": REPO_ROOT / "out" / "diagex-ablation",
        "gpt41": REPO_ROOT / "out" / "diagex-gpt41",
    }
    for bucket, src_dir in bucket_map.items():
        if not src_dir.exists():
            log(f"WARNING: results bucket missing: {bucket} ({src_dir})")
            continue
        dst_dir = tier_a / "results" / bucket
        dst_dir.mkdir(parents=True, exist_ok=True)
        for entry in src_dir.iterdir():
            if entry.is_file() and entry.name in TIER_A_RESULTS_KEEP_FILES:
                copy_file(entry, dst_dir / entry.name)
            elif entry.is_dir() and entry.name in TIER_A_RESULTS_KEEP_DIRS:
                copy_tree(entry, dst_dir / entry.name)

    # 13. tests/unit — keep-list only. The Tier A tree mirrors the source
    #     repo layout (src/diagex/, eval/datasets/, etc.) so tests need no
    #     path patching.
    test_src_root = REPO_ROOT / "tests" / "unit"
    test_dst_root = tier_a / "tests" / "unit"
    test_dst_root.mkdir(parents=True, exist_ok=True)
    init = test_src_root / "__init__.py"
    if init.exists():
        copy_file(init, test_dst_root / "__init__.py")

    # tests/fixtures/dexpi_2_0/ — official DEXPI 2.0 reference P&ID needed by
    # several test_dexpi_xml_io.py tests. Vendored under CC-BY 4.0; PROVENANCE
    # document travels with it.
    fixtures_src = REPO_ROOT / "tests" / "fixtures"
    if fixtures_src.exists():
        copy_tree(fixtures_src, tier_a / "tests" / "fixtures")

    for tname in TIER_A_UNIT_TESTS:
        s = test_src_root / tname
        if not s.exists():
            log(f"WARNING: test missing: {tname}")
            continue
        copy_file(s, test_dst_root / tname)

    log(f"Tier A size: {dir_size_mb(tier_a):.1f} MB")
    return tier_a


# -----------------------------------------------------------------------------
# Tier B — supplementary archive
# -----------------------------------------------------------------------------

def build_tier_b(release_root: Path) -> Path:
    """Assemble Tier B staging tree and zip it. Returns the zip path."""
    tier_b = release_root / TIER_B_DIRNAME
    reset_dir(tier_b)
    log(f"writing Tier B under {tier_b}")

    corpus = corpus_fixture_stems(
        REPO_ROOT / "eval" / "datasets" / "manifest.yaml"
    )
    log(f"corpus filter: {len(corpus)} fixtures — "
        f"{', '.join(sorted(corpus))}")

    manifest_rows: list[dict[str, str]] = []

    # Phase 1: per-fixture latest 4 query runs (one per query, approx).
    # Filter against the corpus — runs/ contains exploration-era fixtures
    # (desalination2, nitrates*, h2first1, ...) that are not paper evidence.
    p1_runs_root = REPO_ROOT / "runs"
    if p1_runs_root.exists():
        p1_picks = latest_runs_per_fixture_phase1(p1_runs_root, per_fixture_limit=4)
        skipped = sorted(set(p1_picks) - corpus)
        if skipped:
            log(f"phase1: skipping out-of-corpus fixtures: "
                f"{', '.join(skipped)}")
        for fixture, run_dirs in sorted(p1_picks.items()):
            if fixture not in corpus:
                continue
            for run_dir in run_dirs:
                rel_dst = Path("runs") / "phase1" / fixture / run_dir.name
                filter_run_dir(run_dir, tier_b / rel_dst)
                _record_manifest(manifest_rows, tier_b, rel_dst, fixture,
                                 condition="baseline", phase="1")

    # Phase 2 baseline.
    p2_baseline_root = REPO_ROOT / "out" / "diagex-phase2" / "baseline" / "runs"
    p2_picks = latest_run_dir_per_fixture(p2_baseline_root)
    for fixture, run_dir in sorted(p2_picks.items()):
        if fixture not in corpus:
            log(f"phase2: skipping out-of-corpus fixture: {fixture}")
            continue
        rel_dst = Path("runs") / "phase2" / fixture / run_dir.name
        filter_run_dir(run_dir, tier_b / rel_dst)
        _record_manifest(manifest_rows, tier_b, rel_dst, fixture,
                         condition="baseline", phase="2")
        # Also include tiles/ if present — small enough per-fixture and
        # reviewers asked to see what the agent saw (plan default).
        tiles_src = run_dir / "tiles"
        if tiles_src.exists():
            tiles_dst = tier_b / rel_dst / "tiles"
            copy_tree(tiles_src, tiles_dst)
            for tile_file in sorted(tiles_dst.rglob("*")):
                if tile_file.is_file():
                    rel = tile_file.relative_to(tier_b)
                    manifest_rows.append({
                        "phase": "2",
                        "fixture": fixture,
                        "condition": "baseline",
                        "path": str(rel).replace("\\", "/"),
                        "sha256": sha256_of(tile_file),
                    })

    # Ablation (no-tile).
    abl_root = REPO_ROOT / "out" / "diagex-ablation" / "ablation-no-tile" / "runs"
    abl_picks = latest_run_dir_per_fixture(abl_root)
    for fixture, run_dir in sorted(abl_picks.items()):
        if fixture not in corpus:
            log(f"ablation: skipping out-of-corpus fixture: {fixture}")
            continue
        rel_dst = Path("runs") / "ablation" / fixture / run_dir.name
        filter_run_dir(run_dir, tier_b / rel_dst)
        _record_manifest(manifest_rows, tier_b, rel_dst, fixture,
                         condition="ablation-no-tile", phase="2")

    # GPT-4.1 baseline.
    gpt_root = REPO_ROOT / "out" / "diagex-gpt41"
    # GPT-4.1 layout: out/diagex-gpt41/runs/<fixture>/... if present.
    gpt_runs_candidates = [
        gpt_root / "gpt41-singleshot" / "runs",
        gpt_root / "runs",
    ]
    gpt_runs_root = next((p for p in gpt_runs_candidates if p.exists()), None)
    if gpt_runs_root is not None:
        gpt_picks = latest_run_dir_per_fixture(gpt_runs_root)
        for fixture, run_dir in sorted(gpt_picks.items()):
            if fixture not in corpus:
                log(f"gpt41: skipping out-of-corpus fixture: {fixture}")
                continue
            rel_dst = Path("runs") / "gpt41" / fixture / run_dir.name
            filter_run_dir(run_dir, tier_b / rel_dst)
            _record_manifest(manifest_rows, tier_b, rel_dst, fixture,
                             condition="gpt41-singleshot", phase="1")
    else:
        log("note: no per-fixture run dirs found for gpt41 baseline; skipping")

    # qa_analysis.xlsx per condition (the per-trial drilldown).
    qa_dst = tier_b / "qa"
    qa_dst.mkdir(parents=True, exist_ok=True)
    for bucket, src_dir in [
        ("phase1", REPO_ROOT / "out" / "diagex-phase1"),
        ("phase2", REPO_ROOT / "out" / "diagex-phase2"),
    ]:
        qa_src = src_dir / "qa_analysis.xlsx"
        if qa_src.exists():
            dst = qa_dst / f"{bucket}.qa_analysis.xlsx"
            copy_file(qa_src, dst)
            manifest_rows.append({
                "phase": "qa",
                "fixture": "",
                "condition": bucket,
                "path": str(dst.relative_to(tier_b)).replace("\\", "/"),
                "sha256": sha256_of(dst),
            })

    # ≤2 retained _failed_runs/ for transparency on the 5 MiB image-cap
    # incident (plan §10 step 11).
    failed_root = REPO_ROOT / "out" / "diagex-phase2" / "_failed_runs"
    if failed_root.exists():
        kept = 0
        for fixture_dir in sorted(failed_root.iterdir()):
            if not fixture_dir.is_dir() or kept >= 2:
                continue
            if fixture_dir.name not in corpus:
                continue
            for run_dir in sorted(fixture_dir.iterdir(),
                                  key=lambda p: p.stat().st_mtime,
                                  reverse=True):
                if run_dir.is_dir():
                    rel_dst = Path("_failed_runs") / fixture_dir.name / run_dir.name
                    filter_run_dir(run_dir, tier_b / rel_dst)
                    _record_manifest(manifest_rows, tier_b, rel_dst,
                                     fixture_dir.name, condition="failed",
                                     phase="2")
                    kept += 1
                    break

    # MANIFEST.csv (sorted for stable diffs).
    manifest_path = tier_b / "MANIFEST.csv"
    manifest_rows.sort(key=lambda r: (r["phase"], r["fixture"], r["path"]))
    with manifest_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=["phase", "fixture", "condition",
                                                "path", "sha256"])
        writer.writeheader()
        writer.writerows(manifest_rows)

    # Per-condition row count summary (handy for reviewers).
    summary: dict[tuple[str, str], int] = defaultdict(int)
    for row in manifest_rows:
        summary[(row["phase"], row["condition"])] += 1
    summary_lines = ["# Tier B contents summary\n",
                     "Per-(phase, condition) file counts:\n"]
    for (phase, cond), n in sorted(summary.items()):
        summary_lines.append(f"- phase={phase} condition={cond}: {n} files\n")
    (tier_b / "README.md").write_text(
        "# diagex — supplementary archive\n\n"
        "Per-run agent transcripts, intermediate DEXPI 2.0 JSON, debug HTML, "
        "and tile crops for the canonical run per (fixture, condition) "
        "underlying the published numbers in the Tier A repo. Cross-DOI'd "
        "to the GitHub release via `.zenodo.json` `related_identifiers`.\n\n"
        "The legacy filename `pid.pydexpi.json` is intentional: the payload "
        "is DEXPI 2.0 JSON via `diagex.dexpi.json_io` (no AGPL pyDEXPI "
        "involved); the name is kept for diff hygiene with prior runs and "
        "with the canonical paths cited in the manuscript.\n\n"
        "Verify integrity by re-hashing the files listed in `MANIFEST.csv`\n"
        "against the `sha256` column.\n\n"
        + "".join(summary_lines),
        encoding="utf-8",
    )

    # Zip it.
    zip_path = release_root / f"{TIER_B_DIRNAME}.zip"
    if zip_path.exists():
        zip_path.unlink()
    log(f"creating zip {zip_path}")
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
        for f in sorted(tier_b.rglob("*")):
            if f.is_file():
                zf.write(f, f.relative_to(release_root))

    log(f"Tier B size: {dir_size_mb(tier_b):.1f} MB; zip = "
        f"{zip_path.stat().st_size / (1024 * 1024):.1f} MB; "
        f"{len(manifest_rows)} files in MANIFEST.csv")
    return zip_path


def _record_manifest(rows: list[dict[str, str]], tier_b: Path, rel_dst: Path,
                     fixture: str, *, condition: str, phase: str) -> None:
    for f in sorted((tier_b / rel_dst).rglob("*")):
        if not f.is_file():
            continue
        rows.append({
            "phase": phase,
            "fixture": fixture,
            "condition": condition,
            "path": str(f.relative_to(tier_b)).replace("\\", "/"),
            "sha256": sha256_of(f),
        })


# -----------------------------------------------------------------------------
# Entry point
# -----------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-root", type=Path,
        default=REPO_ROOT / "release",
        help="Where to write the staging trees (default: ./release).",
    )
    parser.add_argument(
        "--skip-tier-b", action="store_true",
        help="Build only the Tier A GitHub-ready tree (faster smoke).",
    )
    args = parser.parse_args(argv)

    args.release_root.mkdir(parents=True, exist_ok=True)
    build_tier_a(args.release_root)
    if args.skip_tier_b:
        log("--skip-tier-b: leaving Tier B unchanged")
    else:
        build_tier_b(args.release_root)
    log("done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
