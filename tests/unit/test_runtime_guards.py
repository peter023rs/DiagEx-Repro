"""Completion guards for dense page extraction loops."""

from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import anthropic
import httpx
import pytest

from diagex.agent.runtime import ReactRuntime, RunConfig
from diagex.agent.state import AgentState
from diagex.agent.tools import dispatch
from diagex.config import RuntimeBudgets
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


@pytest.mark.parametrize("limit", [4, 2, 1])
def test_scanned_legend_navigation_does_not_accumulate_unbounded_images(limit):
    from PIL import Image

    from diagex.vision.views import ViewProvider

    drawing = _page().model_copy(update={"image": Image.new("RGB", (100, 100), "white")})
    calls = []

    class Client:
        def messages_create(self, **kwargs):
            images = [block for message in kwargs["messages"] for result in message["content"]
                      if result["type"] == "tool_result" for block in result["content"] if block["type"] == "image"]
            assert len(images) <= 4, f"Too many images in request: {len(images)} > 4"
            if len(images) > limit:
                raise anthropic.BadRequestError(
                    f"Too many images in request: {len(images)} > {limit}",
                    response=httpx.Response(400, request=httpx.Request("POST", "https://test.invalid")),
                    body=None,
                )
            calls.append(len(images))
            finished = len(calls) == 8
            return SimpleNamespace(content=[{
                "type": "tool_use", "id": str(len(calls)),
                "name": "finish" if finished else "get_region",
                "input": {"answer": "done", "confidence": "high"} if finished else
                {"x": len(calls), "y": 0, "w": 50, "h": 50},
            }], stop_reason="tool_use", usage=None)

    state = AgentState(question="Extract legend", page=drawing)
    runtime = ReactRuntime(client=Client(), system_blocks=[], cost_tracker=CostTracker(), budgets=RuntimeBudgets())
    runtime.run(state=state, view_provider=ViewProvider(drawing, []), run_cfg=RunConfig(effort="medium", max_steps=10))
    assert len(calls) == 8 and state.done
    assert len(state.region_fetches) == 7


def test_old_view_expiration_keeps_metadata_and_recent_pixels():
    from diagex.agent.runtime import _bound_tool_images

    results = [{"type": "tool_result", "tool_use_id": str(i), "content": [
        {"type": "text", "text": f"view_tag=region-{i}; origin=(10,20)"},
        {"type": "image", "source": {"data": str(i)}},
    ]} for i in range(6)]
    messages = [{"role": "user", "content": results}]
    _bound_tool_images(messages, 4)
    assert all(result["content"][0]["text"].startswith("view_tag=") for result in results)
    assert all("Fetch this view again" in result["content"][1]["text"] for result in results[:2])
    assert [r["content"][1]["source"]["data"] for r in results[2:]] == ["2", "3", "4", "5"]
