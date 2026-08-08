"""Regression tests for the runtime progress reporter package."""

from __future__ import annotations

from io import StringIO

from rich.console import Console

from diagex.ui.progress import (
    LiveProgressReporter,
    NullReporter,
    PlainProgressReporter,
    make_reporter,
)


def test_null_reporter_supports_runtime_events_and_context_manager() -> None:
    reporter = NullReporter()

    with reporter:
        reporter.on_run_start(page_index=0, max_steps=3, effort="high")
        reporter.on_phase_start(name="legend scan", total_items=2)
        reporter.on_phase_item_start(item=1, total_items=2, label="classifying page 1")
        reporter.on_phase_item_end(detail="not a legend")
        reporter.on_phase_end(detail="0 legend pages detected")
        reporter.on_step_start(step=1)
        reporter.on_token_update(total_tokens=1_250_000)
        reporter.on_stream_delta(kind="thinking", text="check")
        reporter.on_thinking(text="checking")
        reporter.on_text(text="answering")
        reporter.on_tool_call(name="get_overview", input={"max_dim": 1000})
        reporter.on_tool_result(name="get_overview", elapsed_s=0.1, is_error=False)
        reporter.on_run_end(
            status="complete", final_answer="done", confidence="high"
        )


def test_non_terminal_console_gets_plain_progress_lines() -> None:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    reporter = make_reporter(console, effort="medium")

    assert isinstance(reporter, PlainProgressReporter)
    with reporter:
        reporter.on_run_start(page_index=0, max_steps=3, effort="medium")
        reporter.on_step_start(step=1)
        reporter.on_token_update(total_tokens=1_250_000)
        reporter.on_run_end(
            status="complete", final_answer="done", confidence="medium"
        )

    output = stream.getvalue()
    assert "page 1" in output
    assert "step 1" in output
    assert "1.250M" in output
    assert "$" not in output
    assert "confidence medium" in output


def test_plain_reporter_labels_step_limit_as_partial() -> None:
    stream = StringIO()
    reporter = PlainProgressReporter(
        Console(file=stream, force_terminal=False, width=120), effort="medium"
    )

    reporter.on_run_start(page_index=0, max_steps=40, effort="medium")
    reporter.on_step_start(step=40)
    reporter.on_run_end(
        status="partial",
        final_answer="partial extraction",
        confidence="low",
        detail="step limit reached (40/40)",
    )

    output = stream.getvalue()
    assert "partial" in output
    assert "step limit reached (40/40)" in output
    assert "complete" not in output


def test_terminal_console_gets_live_progress_reporter() -> None:
    console = Console(file=StringIO(), force_terminal=True, width=120)

    assert isinstance(make_reporter(console, effort="medium"), LiveProgressReporter)


def test_plain_reporter_displays_phase_page_counter_and_result() -> None:
    stream = StringIO()
    reporter = PlainProgressReporter(
        Console(file=stream, force_terminal=False, width=120), effort="medium"
    )

    reporter.on_phase_start(name="legend scan", total_items=12)
    reporter.on_phase_item_start(
        item=1, total_items=12, label="classifying page 1"
    )
    reporter.on_phase_item_end(detail="not a legend")
    reporter.on_phase_end(detail="0 legend page(s) detected")

    output = stream.getvalue()
    assert "legend scan" in output
    assert "1/12" in output
    assert "classifying page 1" in output
    assert "not a legend" in output


def test_live_reporter_renders_running_phase_elapsed_panel() -> None:
    reporter = LiveProgressReporter(
        Console(file=StringIO(), force_terminal=True, width=120), effort="medium"
    )
    reporter.on_phase_start(name="legend scan", total_items=12)
    reporter.on_phase_item_start(
        item=3, total_items=12, label="classifying page 3"
    )

    rendered = reporter._render()
    stream = StringIO()
    Console(file=stream, force_terminal=False, width=120).print(rendered)
    output = stream.getvalue()

    assert "legend scan" in output
    assert "item 3/12" in output
    assert "classifying page 3" in output


def test_live_reporter_keeps_completed_progress_in_terminal_scrollback() -> None:
    stream = StringIO()
    reporter = LiveProgressReporter(
        Console(file=stream, force_terminal=True, width=120), effort="medium"
    )

    with reporter:
        reporter.on_phase_start(name="legend scan", total_items=2)
        reporter.on_phase_item_start(
            item=1, total_items=2, label="classifying page 1"
        )
        reporter.on_phase_item_end(detail="not a legend")
        reporter.on_phase_item_start(
            item=2, total_items=2, label="classifying page 2"
        )

    output = stream.getvalue()
    assert "classifying page 1" in output
    assert "item 1" in output
    assert "not a legend" in output
    assert "classifying page 2" in output


def test_live_reporter_renders_streaming_reasoning_preview() -> None:
    reporter = LiveProgressReporter(
        Console(file=StringIO(), force_terminal=True, width=120), effort="medium"
    )
    reporter.on_run_start(page_index=0, max_steps=3, effort="medium")
    reporter.on_step_start(step=1)
    reporter.on_stream_delta(kind="thinking", text="Looking closely at the valves")

    rendered = reporter._render()
    stream = StringIO()
    Console(file=stream, force_terminal=False, width=120).print(rendered)
    output = stream.getvalue()

    assert "reasoning" in output
    assert "Looking closely at the valves" in output
