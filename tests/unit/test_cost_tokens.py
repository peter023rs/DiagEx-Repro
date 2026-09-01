"""Token-total helpers used by progress and report displays."""

from __future__ import annotations

from types import SimpleNamespace

from diagex.extractors.pid import PidExtractionResult
from diagex.llm.cost import (
    CostTracker,
    format_elapsed,
    format_tokens_millions,
    total_tokens_from_summary,
)
from diagex.vision.models import ReconciledGraph


def test_cost_tracker_total_tokens_includes_cache_categories() -> None:
    tracker = CostTracker()
    tracker.record(
        SimpleNamespace(
            usage=SimpleNamespace(
                input_tokens=1_000_000,
                output_tokens=200_000,
                cache_read_input_tokens=300_000,
                cache_creation_input_tokens=40_000,
            )
        ),
        step=1,
    )

    assert tracker.total_tokens() == 1_540_000
    assert tracker.summary()["total_tokens"] == 1_540_000
    assert format_tokens_millions(tracker.total_tokens()) == "1.540M"


def test_total_tokens_from_summary_supports_legacy_cost_files() -> None:
    assert total_tokens_from_summary(
        {
            "input_tokens": 1_000_000,
            "output_tokens": 200_000,
            "cache_read_tokens": 300_000,
            "cache_write_tokens": 40_000,
        }
    ) == 1_540_000


def test_format_elapsed_uses_compact_clock_format() -> None:
    assert format_elapsed(125.9) == "02:05"
    assert format_elapsed(3_725.9) == "1:02:05"


def test_pid_console_summary_places_elapsed_time_next_to_tokens() -> None:
    result = PidExtractionResult(
        diagram_stem="drawing",
        effort="medium",
        model="model",
        graph=ReconciledGraph(source_path="drawing"),
        dexpi_json_path=None,
        cost_summary={
            "total_tokens": 12_017_000,
            "input_tokens": 9_535_000,
            "output_tokens": 511_000,
            "wall_clock_s": 3_725.9,
        },
    )

    assert (
        "tokens: 12.017M (9.535M in / 0.511M out)   elapsed: 1:02:05"
        in result.to_text()
    )
