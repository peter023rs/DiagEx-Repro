"""Persistence and shared results remain usable without extraction engines."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from diagex.config import Config, LLMConfig
from diagex.runs import files, layout
from diagex.runs.checkpoints import CheckpointStore
from diagex.workflows.results import PidExtractionResult


@pytest.mark.parametrize(
    ("modules", "blocked"),
    [
        (
            ["diagex.runs.files", "diagex.runs.layout", "diagex.runs.checkpoints"],
            [
                "diagex.extractors",
                "diagex.workflows",
                "diagex.llm",
                "diagex.vision",
                "diagex.web",
                "diagex.review",
            ],
        ),
        (
            ["diagex.workflows.results", "diagex.workflows.artifacts"],
            ["diagex.extractors", "diagex.agent", "diagex.web", "diagex.review"],
        ),
    ],
)
def test_shared_modules_import_without_their_consumers(modules, blocked):
    # A fresh interpreter avoids hiding a dependency in pytest's import cache.
    code = (
        "import importlib, json, sys\n"
        "modules, blocked = json.loads(sys.argv[1])\n"
        "for name in blocked: sys.modules[name] = None\n"
        "for name in modules: importlib.import_module(name)\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code, json.dumps([modules, blocked])],
        capture_output=True,
        text=True,
        check=False,
    )
    assert result.returncode == 0, result.stderr


def test_legacy_imports_keep_the_same_checkpoint_and_result_types():
    from diagex.extractors.evidence_checkpoint import CheckpointStore as LegacyStore
    from diagex.extractors.pid import PidExtractionResult as LegacyResult

    assert LegacyStore is CheckpointStore
    assert LegacyResult is PidExtractionResult


def test_failed_atomic_replace_preserves_previous_artifact(tmp_path, monkeypatch):
    target = tmp_path / "result.json"
    files.atomic_write_json(target, {"state": "reviewed", "label": "T-101"})
    before = target.read_bytes()

    def fail_replace(source, destination):
        raise OSError("replacement failed")

    monkeypatch.setattr(files.os, "replace", fail_replace)
    with pytest.raises(OSError, match="replacement failed"):
        files.atomic_write_json(target, {"state": "replacement"})

    assert target.read_bytes() == before
    assert list(tmp_path.iterdir()) == [target]


def test_existing_checkpoint_manifest_loads_without_migration(tmp_path):
    manifest_path = tmp_path / "checkpoints" / "manifest.json"
    manifest_path.parent.mkdir()
    manifest_path.write_text(
        json.dumps(
            {
                "schema_version": "2.0.0",
                "engine": "evidence-v2",
                "source_sha256": "source",
                "config_sha256": "config",
                "run_id": "r-old",
                "status": "paused",
                "pause_reason": "budget",
                "completed": {"perception": ["p0"]},
                "errors": [],
                "stage_versions": {"perception": "old-version"},
            }
        )
    )
    before = manifest_path.read_bytes()

    store = CheckpointStore.load(tmp_path)

    assert store.matches(source_sha256="source", config_sha256="config")
    assert store.is_done("perception", "p0")
    assert store.manifest.status == "paused"
    assert store.manifest.pause_reason == "budget"
    assert store.manifest.stage_versions == {"perception": "old-version"}
    assert manifest_path.read_bytes() == before


def test_evidence_run_collision_exhaustion_never_overwrites(tmp_path, monkeypatch):
    cfg = Config(runs_dir=tmp_path, llm=LLMConfig(model="test/model"))
    monkeypatch.setattr(layout, "timestamp", lambda: "fixed-time")
    monkeypatch.setattr(layout, "new_run_id", lambda: "r-fixed")
    run_dir, _ = layout.prepare_evidence_run_dir(cfg, "drawing", "test/model")
    sentinel = run_dir / "reviewed.json"
    sentinel.write_text("preserve review")

    with pytest.raises(FileExistsError, match="after 16 attempts"):
        layout.prepare_evidence_run_dir(cfg, "drawing", "test/model")

    assert sentinel.read_text() == "preserve review"
    assert len(list((tmp_path / "drawing").iterdir())) == 1


def test_legacy_run_collision_preserves_original_directory(tmp_path: Path, monkeypatch):
    cfg = Config(runs_dir=tmp_path, llm=LLMConfig(model="test/model"))
    monkeypatch.setattr(layout, "timestamp", lambda: "fixed-time")
    monkeypatch.setattr(layout, "new_run_id", lambda: "r-fixed")
    run_dir, _ = layout.prepare_run_dir(cfg, "drawing")
    sentinel = run_dir / "graph.json"
    sentinel.write_text("original graph")

    with pytest.raises(FileExistsError):
        layout.prepare_run_dir(cfg, "drawing")

    assert sentinel.read_text() == "original graph"
