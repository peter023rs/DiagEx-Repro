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
        reporter.on_step_start(step=1)
        reporter.on_cost_update(total_usd=0.1)
        reporter.on_thinking(text="checking")
        reporter.on_text(text="answering")
        reporter.on_tool_call(name="get_overview", input={"max_dim": 1000})
        reporter.on_tool_result(name="get_overview", elapsed_s=0.1, is_error=False)
        reporter.on_run_end(final_answer="done", confidence="high")


def test_non_terminal_console_gets_plain_progress_lines() -> None:
    stream = StringIO()
    console = Console(file=stream, force_terminal=False, width=120)
    reporter = make_reporter(console, effort="medium")

    assert isinstance(reporter, PlainProgressReporter)
    with reporter:
        reporter.on_run_start(page_index=0, max_steps=3, effort="medium")
        reporter.on_step_start(step=1)
        reporter.on_run_end(final_answer="done", confidence="medium")

    output = stream.getvalue()
    assert "page 1" in output
    assert "step 1" in output
    assert "confidence medium" in output


def test_terminal_console_gets_live_progress_reporter() -> None:
    console = Console(file=StringIO(), force_terminal=True, width=120)

    assert isinstance(make_reporter(console, effort="medium"), LiveProgressReporter)
