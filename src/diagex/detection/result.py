"""Detection result without graph or exporter dependencies."""

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path

from diagex.llm.cost import format_elapsed, format_tokens_millions, total_tokens_from_summary


@dataclass
class DetectionResult:
    diagram_stem: str
    effort: str
    model: str
    observation_count: int = 0
    candidate_count: int = 0
    legend_source: str = ""
    legend_entry_count: int = 0
    cost_summary: dict = field(default_factory=dict)
    run_dir: Path | None = None
    run_id: str = ""
    engine: str = "evidence-v2"
    quality_status: str = "complete"
    workflow_stage: str = "detection"

    def to_json(self):
        paths = (
            {
                kind: str(self.run_dir / filename)
                for kind, filename in {
                    "detection": "detection.json",
                    "legend": "legend.json",
                    "cost": "cost.json",
                }.items()
            }
            if self.run_dir
            else {}
        )
        return json.dumps({**asdict(self), "artifacts": paths}, default=str, indent=2)

    def to_text(self):
        return (
            f"{self.diagram_stem}: {self.quality_status}\n"
            f"Symbol observations: {self.observation_count} (overlapping crops may repeat symbols)\n"
            f"Native candidates: {self.candidate_count}; legend entries: {self.legend_entry_count}\n"
            f"Model: {self.model}\n"
            f"tokens: {format_tokens_millions(total_tokens_from_summary(self.cost_summary))} "
            f"({format_tokens_millions(self.cost_summary.get('input_tokens', 0))} in / "
            f"{format_tokens_millions(self.cost_summary.get('output_tokens', 0))} out)   "
            f"elapsed: {format_elapsed(self.cost_summary.get('wall_clock_s', 0))}\n"
            f"Run: {self.run_dir}"
        )
