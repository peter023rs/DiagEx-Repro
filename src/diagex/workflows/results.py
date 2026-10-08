"""Engine-independent extraction result, including its compatible wire and text forms."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from diagex.config import EffortLevel
from diagex.llm.cost import format_elapsed, format_tokens_millions, total_tokens_from_summary
from diagex.vision.models import ReconciledGraph


@dataclass
class PidExtractionResult:
    diagram_stem: str
    effort: EffortLevel
    model: str
    graph: ReconciledGraph
    dexpi_json_path: Path | None
    dexpi_stats: dict = field(default_factory=dict)
    dexpi_issues: list[str] = field(default_factory=list)
    validation_issues: list[dict] = field(default_factory=list)
    legend_source: str = ""
    legend_entry_count: int = 0
    cost_summary: dict = field(default_factory=dict)
    run_dir: Path | None = None
    run_id: str = ""
    engine: str = "legacy"
    quality_status: str = ""
    workflow_stage: str = "graph"

    def to_text(self) -> str:
        lines: list[str] = []
        lines.append(f"P&ID: {self.diagram_stem}")
        lines.append(f"effort: {self.effort}   model: {self.model}   engine: {self.engine}")
        s = self.dexpi_stats or {}
        lines.append(
            "stats: "
            f"equipment={s.get('equipment_count', 0)}, "
            f"valves={s.get('valve_count', 0)}, "
            f"instruments={s.get('instrument_count', 0)}, "
            f"segments={s.get('segment_count', 0)}, "
            f"opcs={s.get('opc_count', 0)}, "
            f"unclassified={s.get('unclassified_count', 0)}, "
            f"dropped_edges={s.get('dropped_edges', 0)}"
        )
        lines.append(f"legend: source={self.legend_source} entries={self.legend_entry_count}")
        if self.validation_issues:
            lines.append(f"validation: {len(self.validation_issues)} issue(s)")
        if self.dexpi_issues:
            lines.append(f"build issues: {len(self.dexpi_issues)}")
        if self.quality_status:
            lines.append(f"quality: {self.quality_status}")
        partial_pages = sorted(
            page + 1 for page, status in self.graph.per_page_status.items() if status == "partial"
        )
        if partial_pages:
            lines.append("partial pages: " + ", ".join(str(page) for page in partial_pages))
        lines.append(
            "tokens: "
            f"{format_tokens_millions(total_tokens_from_summary(self.cost_summary))} "
            f"({format_tokens_millions(self.cost_summary.get('input_tokens', 0))} in / "
            f"{format_tokens_millions(self.cost_summary.get('output_tokens', 0))} out)   "
            f"elapsed: {format_elapsed(self.cost_summary.get('wall_clock_s', 0.0))}"
        )
        if self.dexpi_json_path is not None:
            lines.append(f"dexpi: {self.dexpi_json_path}")
        if self.run_dir is not None:
            lines.append(f"run: {self.run_dir}")
        return "\n".join(lines)

    def to_json(self) -> str:
        return json.dumps(
            {
                "diagram_stem": self.diagram_stem,
                "effort": self.effort,
                "model": self.model,
                "engine": self.engine,
                "quality_status": self.quality_status or None,
                "run_id": self.run_id,
                "run_dir": str(self.run_dir) if self.run_dir else None,
                "dexpi_json_path": str(self.dexpi_json_path) if self.dexpi_json_path else None,
                "dexpi_stats": self.dexpi_stats,
                "dexpi_issues": self.dexpi_issues,
                "validation_issues": self.validation_issues,
                "legend": {"source": self.legend_source, "entry_count": self.legend_entry_count},
                "cost": self.cost_summary,
                "graph": json.loads(self.graph.model_dump_json()),
            },
            indent=2,
        )
