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

from diagex.llm.cost import format_tokens_millions


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

    def on_phase_start(self, *, name: str, total_items: int | None = None) -> None: ...

    def on_phase_item_start(
        self, *, item: int, total_items: int | None = None, label: str = ""
    ) -> None: ...

    def on_phase_item_end(
        self, *, detail: str = "", is_error: bool = False
    ) -> None: ...

    def on_phase_end(self, *, detail: str = "") -> None: ...

    def on_step_start(self, *, step: int) -> None: ...

    def on_token_update(self, *, total_tokens: int) -> None: ...

    def on_stream_delta(self, *, kind: str, text: str) -> None: ...

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

    def on_phase_start(self, *, name: str, total_items: int | None = None) -> None:
        return None

    def on_phase_item_start(
        self, *, item: int, total_items: int | None = None, label: str = ""
    ) -> None:
        return None

    def on_phase_item_end(self, *, detail: str = "", is_error: bool = False) -> None:
        return None

    def on_phase_end(self, *, detail: str = "") -> None:
        return None

    def on_step_start(self, *, step: int) -> None:
        return None

    def on_token_update(self, *, total_tokens: int) -> None:
        return None

    def on_stream_delta(self, *, kind: str, text: str) -> None:
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
        self._phase_name = ""
        self._phase_started_at: float | None = None
        self._phase_item_started_at: float | None = None

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

    def on_phase_start(self, *, name: str, total_items: int | None = None) -> None:
        self._phase_name = name
        self._phase_started_at = time.monotonic()
        total = f" · {total_items} items" if total_items is not None else ""
        self._emit("phase", f"{name}{total}", style="bold cyan")

    def on_phase_item_start(
        self, *, item: int, total_items: int | None = None, label: str = ""
    ) -> None:
        self._phase_item_started_at = time.monotonic()
        counter = f"{item}/{total_items}" if total_items is not None else str(item)
        suffix = f" · {label}" if label else ""
        self._emit(self._phase_name or "progress", counter + suffix, style="cyan")

    def on_phase_item_end(self, *, detail: str = "", is_error: bool = False) -> None:
        elapsed = (
            _format_elapsed(time.monotonic() - self._phase_item_started_at)
            if self._phase_item_started_at is not None
            else "00:00"
        )
        suffix = f" · {detail}" if detail else ""
        self._emit(
            "error" if is_error else "done",
            f"{elapsed}{suffix}",
            style="bold red" if is_error else "green",
        )
        self._phase_item_started_at = None

    def on_phase_end(self, *, detail: str = "") -> None:
        elapsed = (
            _format_elapsed(time.monotonic() - self._phase_started_at)
            if self._phase_started_at is not None
            else "00:00"
        )
        suffix = f" · {detail}" if detail else ""
        self._emit("phase done", f"{elapsed}{suffix}", style="bold green")
        self._phase_item_started_at = None

    def on_step_start(self, *, step: int) -> None:
        now = time.monotonic()
        self._finish_step(now=now)
        self.step = step
        self._step_started_at = now
        self._emit("step", str(step), style="cyan")

    def on_token_update(self, *, total_tokens: int) -> None:
        self._emit(
            "tokens", format_tokens_millions(total_tokens), style="green"
        )

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
        self.total_tokens = 0
        self.status = "preparing"
        self.events: list[tuple[str, str]] = []
        self._live: Live | None = None
        self._run_started_at: float | None = None
        self._step_started_at: float | None = None
        self._mode = "run"
        self._phase_name = ""
        self._phase_item = 0
        self._phase_total: int | None = None
        self._phase_started_at: float | None = None
        self._phase_item_started_at: float | None = None
        self._phase_detail = "preparing"
        self._stream_kind = ""
        self._stream_text = ""

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
            failure = f"failed: {_one_line(exc)}"
            if self._mode == "phase":
                self._phase_detail = failure
            else:
                self.status = failure
            self._event("error", failure, style="bold red")
        if self._live is not None:
            self._live.stop()
            self._live = None

    def _render(self) -> Panel:
        now = time.monotonic()
        if self._mode == "phase":
            item_elapsed = (
                _format_elapsed(now - self._phase_item_started_at)
                if self._phase_item_started_at is not None
                else "00:00"
            )
            phase_elapsed = (
                _format_elapsed(now - self._phase_started_at)
                if self._phase_started_at is not None
                else "00:00"
            )
            counter = (
                f"{self._phase_item}/{self._phase_total}"
                if self._phase_total is not None
                else str(self._phase_item)
            )
            headline = Text(
                f"{self._phase_name}  ·  {self._phase_detail}  ·  "
                f"item {counter} ({item_elapsed})  ·  total {phase_elapsed}",
                style="bold cyan",
            )
            return Panel(headline, title=f"DiagEx · {self.effort}")

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
            f"total {total_elapsed}  ·  "
            f"{format_tokens_millions(self.total_tokens)} tokens",
            style="bold cyan",
        )
        active_lines: list[Text] = []
        if self._stream_text:
            label = "reasoning" if self._stream_kind == "thinking" else "model"
            style = "dim magenta" if self._stream_kind == "thinking" else "magenta"
            active_lines.append(
                Text.assemble(
                    (label, style), "  ", _one_line(self._stream_text, limit=300)
                )
            )
        return Panel(Group(headline, *active_lines), title=f"DiagEx · {self.effort}")

    def _refresh(self) -> None:
        if self._live is not None:
            self._live.refresh()

    def _event(self, label: str, message: str, *, style: str = "") -> None:
        rendered = _one_line(message, limit=240)
        self.events.append((label, rendered))
        timestamp = dt.datetime.now().strftime("%H:%M:%S")
        self.console.print(
            Text.assemble((timestamp, "dim"), "  ", (label, style), "  ", rendered)
        )
        self._refresh()

    def on_run_start(self, *, page_index: int, max_steps: int, effort: str) -> None:
        self._mode = "run"
        self._run_started_at = time.monotonic()
        self.page = page_index
        self.max_steps = max_steps
        self.effort = effort
        self.status = "running"
        self._stream_kind = ""
        self._stream_text = ""
        self._event(
            "start",
            f"page {page_index + 1} · effort {effort} · up to {max_steps} steps",
            style="bold cyan",
        )

    def on_phase_start(self, *, name: str, total_items: int | None = None) -> None:
        self._mode = "phase"
        self._phase_name = name
        self._phase_item = 0
        self._phase_total = total_items
        self._phase_started_at = time.monotonic()
        self._phase_item_started_at = None
        self._phase_detail = "preparing"
        total = f" · {total_items} items" if total_items is not None else ""
        self._event("phase", f"{name}{total}", style="bold cyan")

    def on_phase_item_start(
        self, *, item: int, total_items: int | None = None, label: str = ""
    ) -> None:
        self._phase_item = item
        if total_items is not None:
            self._phase_total = total_items
        self._phase_item_started_at = time.monotonic()
        self._phase_detail = label or "running"
        counter = f"{item}/{self._phase_total}" if self._phase_total else str(item)
        suffix = f" · {label}" if label else ""
        self._event(self._phase_name or "progress", counter + suffix, style="cyan")

    def on_phase_item_end(self, *, detail: str = "", is_error: bool = False) -> None:
        elapsed = (
            _format_elapsed(time.monotonic() - self._phase_item_started_at)
            if self._phase_item_started_at is not None
            else "00:00"
        )
        label = "error" if is_error else "done"
        message = f"item {self._phase_item} · {elapsed}"
        if detail:
            message += f" · {detail}"
        self._phase_detail = "failed" if is_error else "complete"
        self._phase_item_started_at = None
        self._event(
            label,
            message,
            style="bold red" if is_error else "green",
        )

    def on_phase_end(self, *, detail: str = "") -> None:
        elapsed = (
            _format_elapsed(time.monotonic() - self._phase_started_at)
            if self._phase_started_at is not None
            else "00:00"
        )
        self._phase_detail = detail or "complete"
        self._phase_item_started_at = None
        suffix = f" · {detail}" if detail else ""
        self._event("phase done", f"{elapsed}{suffix}", style="bold green")

    def on_step_start(self, *, step: int) -> None:
        now = time.monotonic()
        if self.step and self._step_started_at is not None:
            self._event(
                "elapsed",
                f"step {self.step} · {_format_elapsed(now - self._step_started_at)}",
                style="dim cyan",
            )
        self.step = step
        self._step_started_at = now
        self.status = "thinking"
        self._stream_kind = ""
        self._stream_text = ""
        self._event("step", str(step), style="cyan")

    def on_token_update(self, *, total_tokens: int) -> None:
        self.total_tokens = total_tokens
        self._event(
            "tokens", format_tokens_millions(total_tokens), style="green"
        )

    def on_stream_delta(self, *, kind: str, text: str) -> None:
        if not text:
            return
        self._stream_kind = kind
        self._stream_text = (self._stream_text + text)[-1200:]
        self.status = "reasoning" if kind == "thinking" else "responding"
        self._refresh()

    def on_thinking(self, *, text: str) -> None:
        if text:
            self._stream_kind = ""
            self._stream_text = ""
            self._event("reasoning", text, style="dim magenta")

    def on_text(self, *, text: str) -> None:
        if text:
            self._stream_kind = ""
            self._stream_text = ""
            self._event("model", text, style="magenta")

    def on_tool_call(self, *, name: str, input: dict[str, Any]) -> None:
        self.status = f"using {name}"
        self._stream_kind = ""
        self._stream_text = ""
        self._event("tool", f"{name} {_one_line(input)}", style="bold yellow")

    def on_tool_result(
        self, *, name: str, elapsed_s: float, is_error: bool
    ) -> None:
        label = "error" if is_error else "result"
        self.status = "tool failed" if is_error else "thinking"
        self._event(
            label,
            f"{name} · {elapsed_s:.1f}s",
            style="bold red" if is_error else "green",
        )

    def on_run_end(
        self, *, final_answer: str | None, confidence: str | None
    ) -> None:
        now = time.monotonic()
        if self.step and self._step_started_at is not None:
            self._event(
                "elapsed",
                f"step {self.step} · {_format_elapsed(now - self._step_started_at)}",
                style="dim cyan",
            )
            self._step_started_at = None
        self.status = "complete" if final_answer else "no answer"
        self._stream_kind = ""
        self._stream_text = ""
        if confidence:
            self._event("finish", f"confidence {confidence}", style="bold green")
        else:
            self._refresh()


def make_reporter(console: Console, *, effort: str) -> ProgressReporter:
    """Select live output for a TTY and stable lines for redirected output."""

    if console.is_terminal:
        return LiveProgressReporter(console, effort=effort)
    return PlainProgressReporter(console, effort=effort)
