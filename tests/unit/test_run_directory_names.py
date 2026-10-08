"""Run-directory naming keeps provider/model identity visible and path-safe."""

from __future__ import annotations

from pathlib import Path

import pytest

from diagex.config import Config, LLMConfig
from diagex.runs import layout


@pytest.mark.parametrize("module", [layout])
def test_run_directory_contains_sanitized_model_after_timestamp(
    module: object,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    monkeypatch.setattr(module, "timestamp", lambda: "2026-08-16T10-30-00")
    monkeypatch.setattr(module, "new_run_id", lambda: "r-ab12")
    cfg = Config(
        llm=LLMConfig(model="qwen/qwen3.7-flash:free"),
        runs_dir=tmp_path / "runs",
    )

    run_dir, run_id = module.prepare_run_dir(cfg, "2401")  # type: ignore[attr-defined]

    assert run_id == "r-ab12"
    assert run_dir.name == "2026-08-16T10-30-00_qwen-qwen3.7-flash-free_r-ab12"
    assert (run_dir / "tiles").is_dir()
