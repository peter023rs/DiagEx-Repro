"""Progress reporting for long-running extraction agent loops.

Interactive terminals get a live-updating status panel. Redirected output gets
timestamped lines so logs remain readable, while internal sub-runs can use the
no-op reporter.
"""

from __future__ import annotations

import datetime as dt
import json
import time
from types import TracebackType
from typing import Any, Protocol, Self

from rich.console import Console, Group
from rich.live import Live
from rich.panel import Panel
from rich.text import Text


class ProgressReporter(Protocol):
    """Events emitted by the extraction runtime."""

    def __enter__(self) -> Self: ...

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None: ...

    def on_run_start(
        self, *, page_index: int, max_steps: int, effort: str
    ) -> None: ...

    def on_step_start(self, *, step: int) -> None: ...

    def on_cost_update(self, *, total_usd: float) -> None: ...

    def on_thinking(self, *, text: str) -> None: ...

    def on_text(self, *, text: str) -> None: ...

    def on_tool_call(self, *, name: str, input: dict[str, Any]) -> None: ...

    def on_tool_result(
        self, *, name: str, elapsed_s: float, is_error: bool
    ) -> None: ...

    def on_run_end(
        self, *, final_answer: str | None, confidence: str | None
    ) -> None: ...


class NullReporter:
    """No-op reporter used when progress output is not wanted."""

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        return None

    def on_run_start(self, *, page_index: int, max_steps: int, effort: str) -> None:
        return None

    def on_step_start(self, *, step: int) -> None:
        return None

    def on_cost_update(self, *, total_usd: float) -> None:
        return None

    def on_thinking(self, *, text: str) -> None:
        return None

    def on_text(self, *, text: str) -> None:
        return None

    def on_tool_call(self, *, name: str, input: dict[str, Any]) -> None:
        return None

    def on_tool_result(
        self, *, name: str, elapsed_s: float, is_error: bool
    ) -> None:
        return None

    def on_run_end(
        self, *, final_answer: str | None, confidence: str | None
    ) -> None:
        return None


def _one_line(value: Any, *, limit: int = 180) -> str:
    if isinstance(value, str):
        rendered = " ".join(value.split())
    else:
        try:
            rendered = json.dumps(value, ensure_ascii=False, separators=(",", ":"))
        except (TypeError, ValueError):
            rendered = str(value)
        rendered = " ".join(rendered.split())
    if len(rendered) > limit:
        return rendered[: limit - 1] + "…"
    return rendered


def _format_elapsed(elapsed_s: float) -> str:
    total_seconds = max(0, int(elapsed_s))
    hours, remainder = divmod(total_seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    if hours:
        return f"{hours}:{minutes:02d}:{seconds:02d}"
    return f"{minutes:02d}:{seconds:02d}"


class PlainProgressReporter(NullReporter):
    """Timestamped progress lines suitable for redirected output and logs."""

    def __init__(self, console: Console, *, effort: str) -> None:
        self.console = console
        self.effort = effort
        self.step = 0
        self._run_started_at: float | None = None
        self._step_started_at: float | None = None

    def _finish_step(self, *, now: float | None = None) -> None:
        if self.step == 0 or self._step_started_at is None:
            return
        finished_at = time.monotonic() if now is None else now
        self._emit(
            "elapsed",
            f"step {self.step} · {_format_elapsed(finished_at - self._step_started_at)}",
            style="dim cyan",
        )
        self._step_started_at = None

    def _emit(self, label: str, message: str, *, style: str = "") -> None:
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        line = Text.assemble(
            (timestamp, "dim"), "  ", (label, style), "  ", message
        )
        self.console.print(line)

    def on_run_start(self, *, page_index: int, max_steps: int, effort: str) -> None:
        self._run_started_at = time.monotonic()
        self._emit(
            "start",
            f"page {page_index + 1} · effort {effort} · up to {max_steps} steps",
            style="bold cyan",
        )

    def on_step_start(self, *, step: int) -> None:
        now = time.monotonic()
        self._finish_step(now=now)
        self.step = step
        self._step_started_at = now
        self._emit("step", str(step), style="cyan")

    def on_cost_update(self, *, total_usd: float) -> None:
        self._emit("cost", f"${total_usd:.4f}", style="green")

    def on_thinking(self, *, text: str) -> None:
        if text:
            self._emit(
                "reasoning", _one_line(text, limit=240), style="dim magenta"
            )

    def on_text(self, *, text: str) -> None:
        if text:
            self._emit("model", _one_line(text, limit=240), style="magenta")

    def on_tool_call(self, *, name: str, input: dict[str, Any]) -> None:
        self._emit("tool", f"{name} {_one_line(input)}", style="bold yellow")

    def on_tool_result(
        self, *, name: str, elapsed_s: float, is_error: bool
    ) -> None:
        marker = "failed" if is_error else "done"
        style = "bold red" if is_error else "green"
        self._emit(marker, f"{name} · {elapsed_s:.1f}s", style=style)

    def on_run_end(
        self, *, final_answer: str | None, confidence: str | None
    ) -> None:
        now = time.monotonic()
        self._finish_step(now=now)
        state = "complete" if final_answer else "no answer"
        suffix = f" · confidence {confidence}" if confidence else ""
        total = (
            f" · total {_format_elapsed(now - self._run_started_at)}"
            if self._run_started_at is not None
            else ""
        )
        self._emit("finish", state + suffix + total, style="bold green")


class _LiveProgressView:
    def __init__(self, reporter: LiveProgressReporter) -> None:
        self.reporter = reporter

    def __rich_console__(self, console: Console, options: Any) -> Any:
        yield self.reporter._render()


class LiveProgressReporter(NullReporter):
    """Continuously refreshed progress panel for interactive terminals."""

    def __init__(self, console: Console, *, effort: str) -> None:
        self.console = console
        self.effort = effort
        self.page = 0
        self.step = 0
        self.max_steps = 0
        self.total_usd = 0.0
        self.status = "preparing"
        self.events: list[tuple[str, str]] = []
        self._live: Live | None = None
        self._run_started_at: float | None = None
        self._step_started_at: float | None = None

    def __enter__(self) -> Self:
        self._live = Live(
            _LiveProgressView(self),
            console=self.console,
            refresh_per_second=4,
            transient=False,
        )
        self._live.start()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if exc is not None:
            self.status = f"failed: {_one_line(exc)}"
            self._refresh()
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _render(self) -> Panel:
        now = time.monotonic()
        step_elapsed = (
            _format_elapsed(now - self._step_started_at)
            if self._step_started_at is not None
            else "00:00"
        )
        total_elapsed = (
            _format_elapsed(now - self._run_started_at)
            if self._run_started_at is not None
            else "00:00"
        )
        headline = Text(
            f"page {self.page + 1}  ·  {self.status}  ·  "
            f"step {self.step}/{self.max_steps or '?'} ({step_elapsed})  ·  "
            f"total {total_elapsed}  ·  ${self.total_usd:.4f}",
            style="bold cyan",
        )
        event_lines = [
            Text.assemble(
                (label, "yellow" if label == "tool" else "dim"), "  ", message
            )
            for label, message in self.events[-6:]
        ]
        return Panel(Group(headline, *event_lines), title=f"DiagEx · {self.effort}")

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.refresh()

    def _event(self, label: str, message: str) -> None:
        self.events.append((label, _one_line(message, limit=200)))
        self._refresh()

    def on_run_start(self, *, page_index: int, max_steps: int, effort: str) -> None:
        self._run_started_at = time.monotonic()
        self.page = page_index
        self.max_steps = max_steps
        self.effort = effort
        self.status = "running"
        self._refresh()

    def on_step_start(self, *, step: int) -> None:
        now = time.monotonic()
        if self.step and self._step_started_at is not None:
            self.events.append(
                (
                    "elapsed",
                    f"step {self.step} · "
                    f"{_format_elapsed(now - self._step_started_at)}",
                )
            )
        self.step = step
        self._step_started_at = now
        self.status = "thinking"
        self._refresh()

    def on_cost_update(self, *, total_usd: float) -> None:
        self.total_usd = total_usd
        self._refresh()

    def on_thinking(self, *, text: str) -> None:
        if text:
            self._event("reasoning", text)

    def on_text(self, *, text: str) -> None:
        if text:
            self._event("model", text)

    def on_tool_call(self, *, name: str, input: dict[str, Any]) -> None:
        self.status = f"using {name}"
        self._event("tool", f"{name} {_one_line(input)}")

    def on_tool_result(
        self, *, name: str, elapsed_s: float, is_error: bool
    ) -> None:
        label = "error" if is_error else "result"
        self.status = "tool failed" if is_error else "thinking"
        self._event(label, f"{name} · {elapsed_s:.1f}s")

    def on_run_end(
        self, *, final_answer: str | None, confidence: str | None
    ) -> None:
        now = time.monotonic()
        if self.step and self._step_started_at is not None:
            self.events.append(
                (
                    "elapsed",
                    f"step {self.step} · "
                    f"{_format_elapsed(now - self._step_started_at)}",
                )
            )
            self._step_started_at = None
        self.status = "complete" if final_answer else "no answer"
        if confidence:
            self._event("finish", f"confidence {confidence}")
        else:
            self._refresh()


def make_reporter(console: Console, *, effort: str) -> ProgressReporter:
    """Select live output for a TTY and stable lines for redirected output."""

    if console.is_terminal:
        return LiveProgressReporter(console, effort=effort)
    return PlainProgressReporter(console, effort=effort)

