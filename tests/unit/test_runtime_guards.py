"""Completion guards for dense page extraction loops."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

from diagex.agent.runtime import ReactRuntime, RunConfig
from diagex.agent.state import AgentState
from diagex.agent.tools import dispatch
from diagex.config import PidConfig, RuntimeBudgets
from diagex.extractors.pid import _page_step_limit
from diagex.llm.cost import CostTracker
from diagex.vision.models import DiagramPage


def _page() -> DiagramPage:
    return DiagramPage(
        page_index=0,
        width=100,
        height=100,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        source_ref="test#page=1",
    )


def test_dynamic_pid_step_limit_scales_with_tile_count_and_clamps() -> None:
    cfg = PidConfig(
        page_min_steps=20,
        page_step_buffer=15,
        page_max_steps=60,
    )

    assert _page_step_limit(tile_count=1, cfg=cfg, explicit_max_steps=None) == 20
    assert _page_step_limit(tile_count=25, cfg=cfg, explicit_max_steps=None) == 40
    assert _page_step_limit(tile_count=100, cfg=cfg, explicit_max_steps=None) == 60
    assert _page_step_limit(tile_count=25, cfg=cfg, explicit_max_steps=47) == 47


def test_finish_is_rejected_until_required_tile_coverage_is_met() -> None:
    state = AgentState(question="extract", page=_page())
    state.required_tile_ids = {"p0-r0-c0", "p0-r0-c1"}
    state.minimum_tile_coverage = 1.0
    state.tile_fetch_counts["p0-r0-c0"] = 1
    provider = SimpleNamespace()

    rejected = dispatch(
        "finish",
        {"answer": "done", "confidence": "high"},
        state,
        provider,
    )

    assert rejected.is_error is True
    assert "1/2" in rejected.content[0]["text"]
    assert state.done is False

    state.tile_fetch_counts["p0-r0-c1"] = 1
    accepted = dispatch(
        "finish",
        {"answer": "done", "confidence": "high"},
        state,
        provider,
    )

    assert accepted.is_error is False
    assert state.done is True
    assert state.completion_status == "complete"


def test_runtime_stops_repeated_nonproductive_actions_as_partial() -> None:
    response = SimpleNamespace(
        content=[
            {
                "type": "tool_use",
                "id": "repeat",
                "name": "list_annotations",
                "input": {},
            }
        ],
        stop_reason="tool_use",
        usage=None,
    )

    class RepeatingClient:
        def messages_create(self, **kwargs: Any) -> Any:
            return response

    runtime = ReactRuntime(
        client=RepeatingClient(),  # type: ignore[arg-type]
        system_blocks=[],
        cost_tracker=CostTracker(),
        budgets=RuntimeBudgets(),
    )
    state = AgentState(question="extract", page=_page())

    runtime.run(
        state=state,
        view_provider=SimpleNamespace(tiles=[]),
        run_cfg=RunConfig(
            effort="medium",
            max_steps=10,
            no_progress_step_limit=3,
        ),
    )

    # The first unique list call counts as progress; the next three do not.
    assert state.steps == 4
    assert state.completion_status == "partial"
    assert state.completion_reason == "no progress for 3 consecutive model steps"
    assert any(step.kind == "no_progress_stop" for step in state.transcript)


def test_runtime_marks_step_limit_as_partial() -> None:
    responses = [
        SimpleNamespace(
            content=[
                {
                    "type": "tool_use",
                    "id": f"list-{index}",
                    "name": "list_annotations",
                    "input": {"kind": kind},
                }
            ],
            stop_reason="tool_use",
            usage=None,
        )
        for index, kind in enumerate(("equipment", "instrument"))
    ]

    class FiniteClient:
        def messages_create(self, **kwargs: Any) -> Any:
            return responses.pop(0)

    runtime = ReactRuntime(
        client=FiniteClient(),  # type: ignore[arg-type]
        system_blocks=[],
        cost_tracker=CostTracker(),
        budgets=RuntimeBudgets(),
    )
    state = AgentState(question="extract", page=_page())

    runtime.run(
        state=state,
        view_provider=SimpleNamespace(tiles=[]),
        run_cfg=RunConfig(effort="medium", max_steps=2),
    )

    assert state.completion_status == "partial"
    assert state.completion_reason == "step limit reached (2/2)"
    assert state.final_confidence == "low"
    assert any(step.kind == "step_limit" for step in state.transcript)
