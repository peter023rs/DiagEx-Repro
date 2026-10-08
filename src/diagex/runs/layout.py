"""Allocate run directories without changing naming or collision policies."""

from __future__ import annotations

import datetime as dt
import re
import secrets
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from diagex.config import Config


_STEM_SAFE = re.compile(r"[^a-z0-9._-]+")


def safe_stem(path: Path) -> str:
    stem = path.stem.lower()
    stem = _STEM_SAFE.sub("-", stem).strip("-")
    return stem or "diagram"


def safe_model_name(model: str) -> str:
    value = _STEM_SAFE.sub("-", model.lower()).strip("-")
    return value[:80] or "model"


def new_run_id() -> str:
    return "r-" + secrets.token_hex(2)


def timestamp() -> str:
    return dt.datetime.now().strftime("%Y-%m-%dT%H-%M-%S")


def prepare_run_dir(cfg: Config, stem: str) -> tuple[Path, str]:
    runs_root = cfg.runs_dir / stem
    runs_root.mkdir(parents=True, exist_ok=True)
    run_id = new_run_id()
    run_dir = runs_root / f"{timestamp()}_{safe_model_name(cfg.llm.model)}_{run_id}"
    run_dir.mkdir(parents=True, exist_ok=False)
    (run_dir / "tiles").mkdir(exist_ok=True)
    return run_dir, run_id


def append_index(runs_root: Path, run_id: str, action: str, snippet: str) -> None:
    idx = runs_root / "index.md"
    ts = dt.datetime.now().strftime("%Y-%m-%d %H:%M")
    snippet_one_line = snippet.replace("\n", " ").strip()
    if len(snippet_one_line) > 100:
        snippet_one_line = snippet_one_line[:97] + "..."
    with idx.open("a", encoding="utf-8") as f:
        f.write(f"{ts}  {run_id}  {action!r} → {snippet_one_line}\n")


def prepare_evidence_run_dir(cfg: Config, stem: str, vision_model: str) -> tuple[Path, str]:
    runs_root = cfg.runs_dir / stem
    runs_root.mkdir(parents=True, exist_ok=True)
    for _ in range(16):
        run_id = new_run_id()
        run_dir = runs_root / f"{timestamp()}_{safe_model_name(vision_model)}_{run_id}"
        try:
            run_dir.mkdir(parents=True, exist_ok=False)
            break
        except FileExistsError:
            continue
    else:
        raise FileExistsError("Could not allocate a unique run directory after 16 attempts")
    (run_dir / "evidence").mkdir(exist_ok=True)
    return run_dir, run_id
