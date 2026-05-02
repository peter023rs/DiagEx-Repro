"""Ground-truth dataset linter — `diagex gt lint`.

Validates ground-truth fixtures under ``eval/datasets/<stem>/`` per spec §9.1:
schema conformance, id uniqueness, referential integrity of edges, OPC pairing
state. Also accepts standalone paths to ``graph.json``, ``queries.truth.yaml``,
``annotations.truth.jsonl``, or ``meta.yaml`` for focused checks — which makes
it reusable for run-output graphs (e.g. the Phase 2 stabilisation gate).
"""

from __future__ import annotations

import json
from collections import Counter
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Literal

import yaml
from pydantic import ValidationError

from diagex.vision.models import Annotation, ReconciledGraph

Level = Literal["error", "warn", "info"]

# Per spec §9.1.
VALID_SCORINGS = {"exact", "contains", "set_match", "graph_reachability", "numeric_tolerance"}
VALID_SOURCE_TYPES = {"scanned", "raster", "vector"}  # spec §9.1 names {scanned, vector};
                                                      # `raster` is an accepted alias for Acrobat
                                                      # image-conversion exports — pipeline-equivalent
                                                      # (adaptive-DPI path) for stratification.
REQUIRED_QUERY_FIELDS = ("question", "expected_answer", "expected_kind", "scoring")
REQUIRED_META_FIELDS = ("source_type", "symbol_standard", "dataset_version")


@dataclass
class Issue:
    path: Path
    level: Level
    message: str

    def __str__(self) -> str:
        return f"  {self.level.upper():5}  {self.path}: {self.message}"


@dataclass
class Report:
    issues: list[Issue] = field(default_factory=list)
    files_seen: list[Path] = field(default_factory=list)

    def add(self, path: Path, level: Level, message: str) -> None:
        self.issues.append(Issue(path, level, message))

    @property
    def error_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "error")

    @property
    def warn_count(self) -> int:
        return sum(1 for i in self.issues if i.level == "warn")

    def ok(self, strict: bool = False) -> bool:
        if self.error_count:
            return False
        if strict and self.warn_count:
            return False
        return True


# ---------------------------------------------------------------------------
# File-level linters
# ---------------------------------------------------------------------------


def lint_graph_file(path: Path, report: Report) -> None:
    """Validate a ReconciledGraph JSON (graph.truth.json or run graph.json)."""
    report.files_seen.append(path)
    try:
        raw = json.loads(path.read_text())
    except Exception as exc:
        report.add(path, "error", f"unparseable JSON ({exc})")
        return
    try:
        g = ReconciledGraph.model_validate(raw)
    except ValidationError as exc:
        report.add(path, "error", f"schema: {_pyd_summary(exc)}")
        return

    # uniqueness
    node_ids = [n.id for n in g.nodes]
    dups = [x for x, c in Counter(node_ids).items() if c > 1]
    if dups:
        report.add(path, "error", f"{len(dups)} duplicate node id(s): {dups[:3]}{'…' if len(dups) > 3 else ''}")
    edge_ids = [e.id for e in g.edges]
    edge_dups = [x for x, c in Counter(edge_ids).items() if c > 1]
    if edge_dups:
        report.add(path, "error", f"{len(edge_dups)} duplicate edge id(s)")

    # referential integrity
    known = set(node_ids)
    dangling = [e for e in g.edges if e.from_node not in known or e.to_node not in known]
    if dangling:
        report.add(path, "error", f"{len(dangling)} edge(s) with dangling endpoint (e.g. {dangling[0].id})")

    # OPC pairing state (info-level — dangling OPCs are allowed but tracked)
    if g.dangling_opcs:
        report.add(path, "info", f"{len(g.dangling_opcs)} dangling OPC(s) — expected to pair with off-sheet references")

    # per-page status
    bad_pages = [p for p, s in g.per_page_status.items() if s != "ok"]
    if bad_pages:
        report.add(path, "warn", f"per-page status not ok: {bad_pages}")


def lint_queries_file(path: Path, report: Report) -> None:
    """Validate a queries.truth.yaml (spec §9.1)."""
    report.files_seen.append(path)
    try:
        doc = yaml.safe_load(path.read_text())
    except Exception as exc:
        report.add(path, "error", f"unparseable YAML ({exc})")
        return
    if not isinstance(doc, dict):
        report.add(path, "error", "top-level must be a mapping")
        return
    queries = doc.get("queries")
    if not isinstance(queries, list) or not queries:
        report.add(path, "error", "missing or empty `queries` list")
        return

    ids_seen: list[str] = []
    for i, q in enumerate(queries):
        qpos = f"queries[{i}]"
        if not isinstance(q, dict):
            report.add(path, "error", f"{qpos}: not a mapping")
            continue
        missing = [f for f in REQUIRED_QUERY_FIELDS if f not in q]
        if missing:
            report.add(path, "error", f"{qpos}: missing required field(s) {missing}")
        scoring = q.get("scoring")
        if scoring is not None and scoring not in VALID_SCORINGS:
            report.add(path, "error", f"{qpos}: scoring '{scoring}' not in {sorted(VALID_SCORINGS)}")
        if "id" in q:
            ids_seen.append(str(q["id"]))

    dup_q = [x for x, c in Counter(ids_seen).items() if c > 1]
    if dup_q:
        report.add(path, "error", f"{len(dup_q)} duplicate query id(s): {dup_q}")

    # advisory: fixture-level coherence
    if doc.get("fixture") and path.parent.name != doc["fixture"]:
        report.add(path, "warn", f"fixture='{doc['fixture']}' does not match directory '{path.parent.name}'")


def lint_annotations_file(path: Path, report: Report) -> None:
    """Validate an annotations.truth.jsonl (one Annotation per line)."""
    report.files_seen.append(path)
    ids: list[str] = []
    try:
        lines = path.read_text().splitlines()
    except Exception as exc:
        report.add(path, "error", f"unreadable ({exc})")
        return
    for lineno, line in enumerate(lines, 1):
        if not line.strip():
            continue
        try:
            raw = json.loads(line)
            a = Annotation.model_validate(raw)
            ids.append(a.id)
        except json.JSONDecodeError as exc:
            report.add(path, "error", f"line {lineno}: invalid JSON ({exc.msg})")
        except ValidationError as exc:
            report.add(path, "error", f"line {lineno}: schema: {_pyd_summary(exc)}")
    dup_a = [x for x, c in Counter(ids).items() if c > 1]
    if dup_a:
        report.add(path, "error", f"{len(dup_a)} duplicate annotation id(s)")


def lint_meta_file(path: Path, report: Report) -> None:
    """Validate a meta.yaml (spec §9.1)."""
    report.files_seen.append(path)
    try:
        doc = yaml.safe_load(path.read_text())
    except Exception as exc:
        report.add(path, "error", f"unparseable YAML ({exc})")
        return
    if not isinstance(doc, dict):
        report.add(path, "error", "top-level must be a mapping")
        return
    missing = [f for f in REQUIRED_META_FIELDS if f not in doc]
    if missing:
        report.add(path, "warn", f"missing recommended field(s) {missing}")
    if "source_type" in doc and doc["source_type"] not in VALID_SOURCE_TYPES:
        report.add(path, "error", f"source_type '{doc['source_type']}' not in {sorted(VALID_SOURCE_TYPES)}")


def lint_manifest_file(path: Path, report: Report, known_dirs: Iterable[str] = ()) -> None:
    """Cross-check a manifest (dataset-root only)."""
    report.files_seen.append(path)
    try:
        doc = yaml.safe_load(path.read_text())
    except Exception as exc:
        report.add(path, "error", f"unparseable YAML ({exc})")
        return
    fixtures = (doc or {}).get("fixtures", [])
    declared = {f.get("stem") for f in fixtures if isinstance(f, dict)}
    present = set(known_dirs)
    missing_dirs = sorted(declared - present)
    if missing_dirs:
        report.add(path, "warn", f"manifest declares fixtures with no directory: {missing_dirs}")
    unlisted = sorted(present - declared - {"_archive", "_template"})
    # Only report dirs that genuinely look like fixtures (contain at least one truth file).
    unlisted_with_content = [
        d for d in unlisted
        if any((path.parent / d / name).exists() for name in
               ("queries.truth.yaml", "graph.truth.json", "annotations.truth.jsonl", "meta.yaml"))
    ]
    if unlisted_with_content:
        report.add(path, "warn", f"directories present but not in manifest: {unlisted_with_content}")


# ---------------------------------------------------------------------------
# Directory-level driver
# ---------------------------------------------------------------------------


def lint_fixture_dir(path: Path, report: Report, strict: bool = False) -> None:
    """Lint a single ``eval/datasets/<stem>/`` fixture dir."""
    if not path.is_dir():
        report.add(path, "error", "not a directory")
        return
    level_for_missing: Level = "error" if strict else "warn"
    required_files = ("queries.truth.yaml",)
    recommended = ("meta.yaml",)
    optional = ("graph.truth.json", "annotations.truth.jsonl")

    for fname in required_files:
        fp = path / fname
        if not fp.exists():
            report.add(fp, level_for_missing, "missing required file")
            continue
        lint_queries_file(fp, report)

    for fname in recommended:
        fp = path / fname
        if fp.exists():
            lint_meta_file(fp, report)
        else:
            report.add(fp, "warn", "missing recommended file")

    # optional — only lint if present
    g = path / "graph.truth.json"
    if g.exists():
        lint_graph_file(g, report)
    a = path / "annotations.truth.jsonl"
    if a.exists():
        lint_annotations_file(a, report)


def lint_dataset_root(path: Path, report: Report, strict: bool = False) -> None:
    """Lint a dataset root (``eval/datasets/``) — manifest + every fixture dir."""
    if not path.is_dir():
        report.add(path, "error", "not a directory")
        return
    fixture_dirs = sorted(p for p in path.iterdir() if p.is_dir() and not p.name.startswith("_"))
    manifest = _find_manifest(path)
    if manifest:
        lint_manifest_file(manifest, report, known_dirs=(d.name for d in fixture_dirs))
    else:
        report.add(path / "manifest.yaml", "warn", "no manifest found at dataset root")
    for d in fixture_dirs:
        lint_fixture_dir(d, report, strict=strict)


def _find_manifest(root: Path) -> Path | None:
    for cand in root.glob("*.manifest.yaml"):
        return cand
    return None


# ---------------------------------------------------------------------------
# Entry point (dispatch by file type / dir)
# ---------------------------------------------------------------------------


def lint(path: Path, strict: bool = False) -> Report:
    report = Report()
    if path.is_dir():
        # Dataset root vs single fixture dir — detect by presence of fixture subdirs.
        has_fixture_subdirs = any(
            (sub / "queries.truth.yaml").exists()
            for sub in path.iterdir()
            if sub.is_dir() and not sub.name.startswith("_")
        )
        if has_fixture_subdirs:
            lint_dataset_root(path, report, strict=strict)
        else:
            lint_fixture_dir(path, report, strict=strict)
        return report

    name = path.name
    if name.endswith(".jsonl"):
        lint_annotations_file(path, report)
    elif name.endswith(".json"):
        lint_graph_file(path, report)
    elif name.endswith(("queries.truth.yaml", "queries.yaml")):
        lint_queries_file(path, report)
    elif "manifest" in name and name.endswith((".yaml", ".yml")):
        known = [d.name for d in path.parent.iterdir() if d.is_dir()] if path.parent.is_dir() else []
        lint_manifest_file(path, report, known_dirs=known)
    elif name in {"meta.yaml", "meta.yml"} or name.endswith(("meta.yaml", "meta.yml")):
        lint_meta_file(path, report)
    else:
        report.add(path, "error", "unrecognised file type (expected graph.json / queries.truth.yaml / annotations.truth.jsonl / meta.yaml / *.manifest.yaml)")
    return report


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _pyd_summary(exc: ValidationError) -> str:
    errs = exc.errors()
    if not errs:
        return str(exc)
    first = errs[0]
    loc = ".".join(str(p) for p in first.get("loc", ()))
    msg = first.get("msg", "invalid")
    tail = f" (+{len(errs) - 1} more)" if len(errs) > 1 else ""
    return f"{loc}: {msg}{tail}"
