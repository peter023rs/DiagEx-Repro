"""Hand-written ReAct loop over the Anthropic tool-use interface.

Spec §6.1 (loop shape), §6.2 (tools), §6.3 (budgets), §7.1 (transcript layout).

Deliberately ~200-400 LOC of plain Python rather than LangGraph/LangChain — keeps the
cost story, caching story, and debuggability of each step first-class.
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass
from typing import Any

from diagex.agent.state import AgentState
from diagex.agent.tools import TOOL_SCHEMAS, ToolResult, dispatch
from diagex.config import EFFORT_PROFILES, EffortLevel, RuntimeBudgets
from diagex.llm.client import LLMClient
from diagex.llm.cost import CostTracker
from diagex.ui.progress import NullReporter, ProgressReporter
from diagex.vision.views import ViewProvider


@dataclass
class RunConfig:
    effort: EffortLevel = "high"
    max_steps: int | None = None          # None → use EFFORT_PROFILES[effort].max_steps
    max_tokens: int | None = None         # per-step max_tokens; None → effort profile
    require_tile_coverage: bool = False
    minimum_tile_coverage: float = 1.0
    no_progress_step_limit: int | None = None


class ReactRuntime:
    """Runs a single Phase 1 query against a single DiagramPage.

    Multi-page queries drive this runtime once per page from the extractor layer.
    """

    def __init__(
        self,
        *,
        client: LLMClient,
        system_blocks: list[dict[str, Any]],
        cost_tracker: CostTracker,
        budgets: RuntimeBudgets,
        reporter: ProgressReporter | None = None,
    ) -> None:
        self.client = client
        self.system_blocks = system_blocks
        self.cost = cost_tracker
        self.budgets = budgets
        self.reporter: ProgressReporter = reporter or NullReporter()
        # Phase 2+ can install an alternate tool list (e.g. Phase 1 set + lookup_symbol).
        # None -> fall back to TOOL_SCHEMAS. Keeps Phase 1 behaviour unchanged.
        self.tools_override: list[dict[str, Any]] | None = None

    def run(
        self,
        *,
        state: AgentState,
        view_provider: ViewProvider,
        run_cfg: RunConfig,
    ) -> AgentState:
        profile = EFFORT_PROFILES[run_cfg.effort]
        max_steps = run_cfg.max_steps if run_cfg.max_steps is not None else profile.max_steps
        max_tokens = (
            run_cfg.max_tokens
            if run_cfg.max_tokens is not None
            else profile.max_output_tokens
        )
        state.required_tile_ids = (
            {str(tile.id) for tile in view_provider.tiles}
            if run_cfg.require_tile_coverage
            else set()
        )
        state.minimum_tile_coverage = max(
            0.0, min(1.0, run_cfg.minimum_tile_coverage)
        )
        # Opus 4.7 shape: adaptive thinking + output_config.effort; no budget_tokens.
        # `display: summarized` opts back in to non-empty thinking bodies so live
        # feedback can surface the model's reasoning (default is "omitted" on 4.7).
        thinking = (
            {"type": "adaptive", "display": "summarized"}
            if profile.adaptive_thinking
            else {"type": "disabled"}
        )
        output_config = {"effort": profile.api_effort}

        self.reporter.on_run_start(
            page_index=state.page.page_index,
            max_steps=max_steps,
            effort=run_cfg.effort,
        )
        self.reporter.on_token_update(total_tokens=self.cost.total_tokens())

        messages: list[dict[str, Any]] = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": (
                            f"Page index: {state.page.page_index}. "
                            f"Page size: {state.page.width}x{state.page.height} px at "
                            f"{state.page.effective_dpi:.0f} DPI"
                            + (" (scanned)." if state.page.is_scanned else " (vector).")
                            + f"\n\nQuestion: {state.question}\n\n"
                            "Begin by calling get_overview, then drill into tiles or regions as needed."
                        ),
                    }
                ],
            }
        ]

        seen_successful_actions: set[tuple[str, str]] = set()
        no_progress_steps = 0

        while not state.done and state.steps < max_steps:
            state.steps += 1
            step_made_progress = False
            self.reporter.on_step_start(step=state.steps)
            t0 = time.time()
            resp = self.client.messages_create(
                system=self.system_blocks,
                messages=messages,
                tools=self.tools_override if self.tools_override is not None else TOOL_SCHEMAS,
                max_tokens=max_tokens,
                thinking=thinking,
                output_config=output_config,
                on_stream_delta=lambda kind, text: self.reporter.on_stream_delta(
                    kind=kind, text=text
                ),
            )
            self.cost.record(resp, step=state.steps, page_index=state.page.page_index)
            self.reporter.on_token_update(total_tokens=self.cost.total_tokens())
            state.push_transcript("llm_response", {
                "step": state.steps,
                "stop_reason": getattr(resp, "stop_reason", None),
                "elapsed_s": round(time.time() - t0, 2),
            })

            # Record the assistant's turn verbatim so subsequent calls see the full chain.
            assistant_content = _response_content_to_blocks(resp)
            messages.append({"role": "assistant", "content": assistant_content})

            tool_uses = [b for b in assistant_content if b.get("type") == "tool_use"]
            text_blocks = [b for b in assistant_content if b.get("type") == "text"]
            thinking_blocks = [b for b in assistant_content if b.get("type") == "thinking"]

            for th in thinking_blocks:
                body = th.get("thinking", "")
                if body:
                    self.reporter.on_thinking(text=body)

            for tb in text_blocks:
                txt = tb.get("text", "")
                state.push_transcript("thought", {"text": txt})
                if txt:
                    self.reporter.on_text(text=txt)

            if not tool_uses:
                # No tool call; if the model ended naturally, we're done.
                if getattr(resp, "stop_reason", None) == "end_turn":
                    # Harvest a final text answer if `finish` was never called.
                    if state.final_answer is None and text_blocks:
                        state.final_answer = "\n".join(t["text"] for t in text_blocks)
                        state.final_confidence = state.final_confidence or "medium"
                    state.done = True
                    if run_cfg.require_tile_coverage:
                        state.completion_status = "partial"
                        state.completion_reason = "model ended without calling finish"
                        state.final_confidence = "low"
                    else:
                        state.completion_status = "complete"
                        state.completion_reason = "end_turn"
                break

            tool_result_blocks: list[dict[str, Any]] = []
            for tu in tool_uses:
                state.push_transcript("tool_use", {
                    "id": tu.get("id"),
                    "name": tu.get("name"),
                    "input": tu.get("input"),
                })
                self.reporter.on_tool_call(
                    name=tu.get("name") or "",
                    input=tu.get("input") or {},
                )
                t_tool = time.time()
                result: ToolResult = dispatch(
                    name=tu["name"],
                    raw_input=tu.get("input", {}),
                    state=state,
                    view_provider=view_provider,
                )
                if not result.is_error:
                    action_key = (
                        str(tu.get("name") or ""),
                        json.dumps(
                            tu.get("input") or {},
                            sort_keys=True,
                            ensure_ascii=False,
                            default=str,
                        ),
                    )
                    if action_key not in seen_successful_actions:
                        seen_successful_actions.add(action_key)
                        step_made_progress = True
                self.reporter.on_tool_result(
                    name=tu.get("name") or "",
                    elapsed_s=time.time() - t_tool,
                    is_error=result.is_error,
                )
                state.push_transcript("tool_result", {
                    "id": tu.get("id"),
                    "is_error": result.is_error,
                    # Log only text; images already live on disk + would balloon the transcript.
                    "content_text": [c.get("text", "") for c in result.content if c.get("type") == "text"],
                })
                tool_result_blocks.append({
                    "type": "tool_result",
                    "tool_use_id": tu["id"],
                    "content": result.content,
                    "is_error": result.is_error,
                })

            messages.append({"role": "user", "content": tool_result_blocks})

            if state.done:
                break

            if run_cfg.no_progress_step_limit is not None:
                no_progress_steps = 0 if step_made_progress else no_progress_steps + 1
                if no_progress_steps >= run_cfg.no_progress_step_limit:
                    state.push_transcript(
                        "no_progress_stop",
                        {
                            "steps_without_progress": no_progress_steps,
                            "limit": run_cfg.no_progress_step_limit,
                        },
                    )
                    _mark_partial(
                        state,
                        "no progress for "
                        f"{no_progress_steps} consecutive model steps",
                    )
                    break

        if not state.done:
            if state.steps >= max_steps:
                state.push_transcript(
                    "step_limit", {"steps": state.steps, "max_steps": max_steps}
                )
                _mark_partial(state, f"step limit reached ({state.steps}/{max_steps})")
            else:
                _mark_partial(state, "model stopped without completing the run")

        self.reporter.on_run_end(
            status=state.completion_status,
            final_answer=state.final_answer,
            confidence=state.final_confidence,
            detail=state.completion_reason or "",
        )
        return state


def _mark_partial(state: AgentState, reason: str) -> None:
    state.done = True
    state.completion_status = "partial"
    state.completion_reason = reason
    state.final_confidence = "low"
    if state.final_answer is None:
        state.final_answer = f"partial extraction: {reason}."


def _response_content_to_blocks(resp: Any) -> list[dict[str, Any]]:
    """Turn an Anthropic Messages response into a JSON-serialisable list of blocks.

    Handles the SDK's object-style `.content` (list of typed blocks); falls back to
    a plain dict if the response came from a non-SDK transport.
    """
    content = getattr(resp, "content", None)
    if content is None:
        return []
    blocks: list[dict[str, Any]] = []
    for b in content:
        t = getattr(b, "type", None) if not isinstance(b, dict) else b.get("type")
        if t == "text":
            text = getattr(b, "text", None) if not isinstance(b, dict) else b.get("text")
            blocks.append({"type": "text", "text": text or ""})
        elif t == "tool_use":
            blocks.append({
                "type": "tool_use",
                "id": getattr(b, "id", None) if not isinstance(b, dict) else b.get("id"),
                "name": getattr(b, "name", None) if not isinstance(b, dict) else b.get("name"),
                "input": getattr(b, "input", None) if not isinstance(b, dict) else b.get("input"),
            })
        elif t == "thinking":
            # Thinking blocks carry a cryptographic `signature` that MUST be echoed back
            # verbatim on subsequent requests, or the API returns 400.
            if isinstance(b, dict):
                blocks.append({
                    "type": "thinking",
                    "thinking": b.get("thinking", ""),
                    "signature": b.get("signature", ""),
                })
            else:
                blocks.append({
                    "type": "thinking",
                    "thinking": getattr(b, "thinking", "") or "",
                    "signature": getattr(b, "signature", "") or "",
                })
        elif t == "redacted_thinking":
            # Fully-redacted thinking blocks have `data` instead of `thinking`/`signature`.
            if isinstance(b, dict):
                blocks.append({"type": "redacted_thinking", "data": b.get("data", "")})
            else:
                blocks.append({"type": "redacted_thinking", "data": getattr(b, "data", "") or ""})
        # Other block types: pass through as-is if dict; skip otherwise.
        elif isinstance(b, dict):
            blocks.append(b)
    return blocks
