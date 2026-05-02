"""GPT-4.1 single-shot Phase 1 backend (plan §6, item 2).

One Azure OpenAI chat-completions call per query: page overview image +
question + answer-format suffix. No tools, no ReAct loop, no tile drilldown.

Why not the main `LLMClient`? That client wraps the Anthropic SDK and the
Anthropic wire format (tool_use / tool_result with image content blocks,
thinking blocks with signatures, cache_control markers). GPT-4.1 on Azure
uses the OpenAI chat-completions schema which is structurally different.
Rather than retrofit a dual-transport client, the cross-model anchor is
intentionally narrow: Phase 1 only, single-shot, separate code path.

Config: reads `AZURE_OPENAI_GPT41_*` from .env (endpoint / api-key /
deployment / api-version). Falls back to `AZURE_OPENAI_*` if the GPT-4.1
specific vars are absent and the generic deployment name looks like a
GPT model — but the explicit `_GPT41_` form is preferred so this stays
disjoint from the Claude deployment used for baseline + ablations.
"""

from __future__ import annotations

import base64
import io
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from PIL import Image


# ---------------------------------------------------------------------------
# Pricing — Azure OpenAI GPT-4.1 (per 1M tokens). Adjust here when Foundry
# bills move; the harness reads cost_usd off the outcome rather than re-
# computing, so changing these numbers re-projects future runs only.
# ---------------------------------------------------------------------------

GPT41_INPUT_PER_MTOK = 2.00
GPT41_CACHED_INPUT_PER_MTOK = 0.50
GPT41_OUTPUT_PER_MTOK = 8.00


@dataclass
class _GPT41Endpoint:
    endpoint: str
    api_key: str
    deployment: str
    api_version: str

    @classmethod
    def from_env(cls) -> "_GPT41Endpoint":
        endpoint = (
            os.environ.get("AZURE_OPENAI_GPT41_ENDPOINT")
            or os.environ.get("AZURE_OPENAI_ENDPOINT")
        )
        api_key = (
            os.environ.get("AZURE_OPENAI_GPT41_API_KEY")
            or os.environ.get("AZURE_OPENAI_API_KEY")
        )
        deployment = os.environ.get("AZURE_OPENAI_GPT41_DEPLOYMENT_NAME")
        api_version = (
            os.environ.get("AZURE_OPENAI_GPT41_API_VERSION")
            or "2024-12-01-preview"
        )
        missing = [
            n for n, v in (
                ("AZURE_OPENAI_GPT41_ENDPOINT (or AZURE_OPENAI_ENDPOINT)", endpoint),
                ("AZURE_OPENAI_GPT41_API_KEY (or AZURE_OPENAI_API_KEY)", api_key),
                ("AZURE_OPENAI_GPT41_DEPLOYMENT_NAME", deployment),
            )
            if not v
        ]
        if missing:
            raise RuntimeError(
                "GPT-4.1 single-shot backend missing env vars: "
                + ", ".join(missing)
            )
        return cls(
            endpoint=endpoint.rstrip("/"),
            api_key=api_key,
            deployment=deployment,
            api_version=api_version,
        )


# ---------------------------------------------------------------------------
# Image preparation
# ---------------------------------------------------------------------------


def _render_overview_b64(pdf_path: Path, *, max_dim: int = 2048) -> tuple[str, tuple[int, int]]:
    """Render page 1 of the PDF and return (base64-PNG, (w, h))."""
    # Deferred import — pymupdf is heavy; cassette-only runs shouldn't pay it.
    from diagex.config import load_config
    from diagex.vision.loader import iter_pages, load

    cfg = load_config()
    # GPT-4.1's tile-based image cost peaks around ~2048 px long-side; going
    # bigger does not improve OCR much but does inflate image-token billing.
    cfg.tiling.max_page_dim_px = max_dim
    source = load(pdf_path, tiling=cfg.tiling, scan_cfg=cfg.scan)
    page = next(iter_pages(source))
    img: Image.Image = page.image  # type: ignore[assignment]
    if img is None:
        raise RuntimeError(f"could not render overview for {pdf_path}")

    w, h = img.size
    if max(w, h) > max_dim:
        scale = max_dim / max(w, h)
        img = img.resize((max(1, int(w * scale)), max(1, int(h * scale))), Image.BILINEAR)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return base64.standard_b64encode(buf.getvalue()).decode("ascii"), img.size


# ---------------------------------------------------------------------------
# Single API call
# ---------------------------------------------------------------------------


@dataclass
class GPT41Outcome:
    answer: str
    cost_usd: float
    wall_clock_s: float
    input_tokens: int
    output_tokens: int
    cached_input_tokens: int
    image_tokens: int  # Best-effort; OpenAI rolls images into prompt_tokens.
    dry_run: bool = False
    image_wh: tuple[int, int] = (0, 0)


# ---------------------------------------------------------------------------
# Image-token estimator for GPT-4.1 / GPT-4o "high" detail mode.
# ---------------------------------------------------------------------------


def estimate_image_tokens(width: int, height: int) -> int:
    """Predict OpenAI image-token billing for a vision call at detail=high.

    Per the OpenAI vision pricing rules:
      1. Resize to fit within 2048×2048 (preserve aspect ratio).
      2. Resize so the shortest side is 768 px (preserve aspect ratio).
      3. Count 512×512 tiles needed to cover the image.
      4. Tokens = 85 (base) + 170 × n_tiles.

    Used by `--dry-run` mode to project Phase 1 GPT-4.1 spend without
    actually issuing the calls.
    """
    if width <= 0 or height <= 0:
        return 85
    w, h = float(width), float(height)
    if max(w, h) > 2048:
        scale = 2048.0 / max(w, h)
        w, h = w * scale, h * scale
    short = min(w, h)
    if short > 768:
        scale = 768.0 / short
        w, h = w * scale, h * scale
    import math
    tiles_x = max(1, math.ceil(w / 512.0))
    tiles_y = max(1, math.ceil(h / 512.0))
    return 85 + 170 * tiles_x * tiles_y


_SYSTEM_PROMPT = (
    "You are an industrial-engineering assistant answering one question about "
    "a Process & Instrumentation Diagram (P&ID). You are given a single image "
    "of the full diagram page and one question. Read tags, valves, "
    "instruments, and lines directly from the image. If the diagram does not "
    "show the answer, say so explicitly. Follow the answer-format instruction "
    "at the end of the question literally — no preamble, no markdown."
)


def _build_messages(
    *, question_text: str, image_b64: str,
) -> list[dict[str, Any]]:
    return [
        {
            "role": "user",
            "content": [
                {"type": "text", "text": question_text},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/png;base64,{image_b64}",
                        "detail": "high",
                    },
                },
            ],
        }
    ]


def run_singleshot(
    *,
    pdf_path: Path,
    question_text: str,
    max_output_tokens: int = 1024,
    max_image_dim: int = 2048,
    dry_run: bool = False,
) -> GPT41Outcome:
    """Issue one chat-completions call and return the parsed answer + usage.

    When ``dry_run=True`` no API call is made: the page is rendered, the
    image is sized, and an estimate of input image-tokens + cost is
    returned so a runbook can sanity-check spend before committing.
    """
    image_b64, img_wh = _render_overview_b64(pdf_path, max_dim=max_image_dim)

    if dry_run:
        img_tok = estimate_image_tokens(*img_wh)
        # System prompt + question text together are typically ~150-300 tokens;
        # round to 250 for the estimate. Assumes the answer takes ~80 tokens
        # (40 queries × output budget; most Phase 1 answers are short).
        text_in_est = 250
        out_est = 80
        in_est = img_tok + text_in_est
        cost_est = (
            in_est * GPT41_INPUT_PER_MTOK / 1_000_000
            + out_est * GPT41_OUTPUT_PER_MTOK / 1_000_000
        )
        return GPT41Outcome(
            answer="(dry-run; no API call)",
            cost_usd=cost_est,
            wall_clock_s=0.0,
            input_tokens=in_est,
            output_tokens=out_est,
            cached_input_tokens=0,
            image_tokens=img_tok,
            dry_run=True,
            image_wh=img_wh,
        )

    # Deferred import so cassette-only runs (and pytest collection) don't
    # require the openai SDK to be installed.
    try:
        from openai import AzureOpenAI
    except ImportError as exc:
        raise RuntimeError(
            "GPT-4.1 single-shot needs the `openai` package; "
            "`uv pip install openai>=1.40` (or add to pyproject.toml)."
        ) from exc

    ep = _GPT41Endpoint.from_env()
    client = AzureOpenAI(
        azure_endpoint=ep.endpoint,
        api_key=ep.api_key,
        api_version=ep.api_version,
    )

    messages = [{"role": "system", "content": _SYSTEM_PROMPT}]
    messages.extend(_build_messages(question_text=question_text, image_b64=image_b64))

    t0 = time.perf_counter()
    resp = client.chat.completions.create(
        model=ep.deployment,
        messages=messages,
        max_tokens=max_output_tokens,
        temperature=0.0,
    )
    wall = time.perf_counter() - t0

    answer_text = (resp.choices[0].message.content or "").strip()

    usage = resp.usage
    in_tok = int(getattr(usage, "prompt_tokens", 0) or 0)
    out_tok = int(getattr(usage, "completion_tokens", 0) or 0)
    cached = 0
    details = getattr(usage, "prompt_tokens_details", None)
    if details is not None:
        cached = int(getattr(details, "cached_tokens", 0) or 0)

    billable_input = max(0, in_tok - cached)
    cost = (
        billable_input * GPT41_INPUT_PER_MTOK / 1_000_000
        + cached * GPT41_CACHED_INPUT_PER_MTOK / 1_000_000
        + out_tok * GPT41_OUTPUT_PER_MTOK / 1_000_000
    )

    return GPT41Outcome(
        answer=answer_text,
        cost_usd=cost,
        wall_clock_s=wall,
        input_tokens=in_tok,
        output_tokens=out_tok,
        cached_input_tokens=cached,
        image_tokens=0,
        image_wh=img_wh,
    )
