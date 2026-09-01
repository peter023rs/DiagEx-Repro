"""Stateless, source-bound visual perception for evidence-v2."""

from __future__ import annotations

import json
import math
import re
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from diagex.llm.client import LLMClient, is_malformed_tool_json_error
from diagex.llm.cost import CostTracker
from diagex.ui.progress import ProgressReporter
from diagex.vision.encode import encode_image_block
from diagex.vision.evidence import PageEvidence, stable_evidence_id, text_spans_intersecting
from diagex.vision.models import BBox, Confidence, Tile
from diagex.vision.views import ViewInfo


class NormalizedBBox(BaseModel):
    x: float
    y: float
    w: float
    h: float

    @model_validator(mode="after")
    def _within_image(self) -> NormalizedBBox:
        values = (self.x, self.y, self.w, self.h)
        if not all(value == value and abs(value) != float("inf") for value in values):
            raise ValueError("normalised bbox values must be finite")
        if self.x < 0 or self.y < 0 or self.w <= 0 or self.h <= 0:
            raise ValueError("normalised bbox must have non-negative origin and positive size")
        if self.x > 1 or self.y > 1 or self.x + self.w > 1.001 or self.y + self.h > 1.001:
            raise ValueError("normalised bbox must fit inside [0,1] image coordinates")
        return self


class PerceivedObject(BaseModel):
    kind: Literal["equipment", "instrument", "opc"]
    bbox: NormalizedBBox
    confidence: Confidence = "medium"
    printed_tag: str | None = None
    canonical_tag: str | None = None
    equipment_class: str | None = None
    valve_type: str | None = None
    actuation: Literal[
        "manual",
        "solenoid",
        "electric_motor",
        "pneumatic",
        "hydraulic",
        "spring",
        "other",
    ] | None = None
    instrument_function: str | None = None
    measured_variable: (
        Literal["pressure", "temperature", "flow", "level", "analysis", "other"] | None
    ) = None
    loop_number: str | None = None
    opc_direction: Literal["in", "out"] | None = None
    service: str | None = None
    drawing_ref: str | None = None
    line_id: str | None = None
    structural_description: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_text_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _accept_legacy_object_shape(cls, value: Any) -> Any:
        """Read old checkpoints/provider output without advertising free-form fields."""
        if not isinstance(value, dict):
            return value
        data = dict(value)
        attributes = dict(data.get("attributes") or {})
        legacy_label = data.pop("label", None)
        legacy_raw = data.pop("raw_text", None)
        data.setdefault("printed_tag", legacy_raw or legacy_label)
        data.setdefault("canonical_tag", legacy_label or legacy_raw)
        aliases = {
            "equipment_class": "equipment_class",
            "valve_type": "valve_type",
            "actuation": "actuation",
            "instrument_function": "instrument_function",
            "measured_variable": "measured_variable",
            "loop_number": "loop_number",
            "direction": "opc_direction",
            "service": "service",
            "drawing_ref": "drawing_ref",
            "target_sheet": "drawing_ref",
            "line_id": "line_id",
            "structural_description": "structural_description",
        }
        for source, target in aliases.items():
            if data.get(target) in (None, "") and attributes.get(source) not in (None, ""):
                data[target] = attributes[source]
        data["attributes"] = attributes
        return data

    @field_validator(
        "printed_tag",
        "canonical_tag",
        "equipment_class",
        "valve_type",
        "actuation",
        "instrument_function",
        "loop_number",
        "service",
        "drawing_ref",
        "line_id",
        "structural_description",
        mode="before",
    )
    @classmethod
    def _normalise_optional_text(cls, value: Any) -> Any:
        if value is None:
            return None
        text = " ".join(str(value).split()).strip()
        return text or None

    @property
    def label(self) -> str:
        return self.canonical_tag or self.printed_tag or ""

    @property
    def raw_text(self) -> str | None:
        return self.printed_tag

    def graph_attributes(self) -> dict[str, Any]:
        values = dict(self.attributes)
        typed = {
            "equipment_class": self.equipment_class,
            "valve_type": self.valve_type,
            "actuation": self.actuation,
            "instrument_function": self.instrument_function,
            "measured_variable": self.measured_variable,
            "loop_number": self.loop_number,
            "direction": self.opc_direction,
            "service": self.service,
            "drawing_ref": self.drawing_ref,
            "line_id": self.line_id,
            "structural_description": self.structural_description,
        }
        values.update({key: value for key, value in typed.items() if value not in (None, "")})
        if self.canonical_tag:
            values["canonical_tag"] = self.canonical_tag
        return values


class PerceptionBatch(BaseModel):
    objects: list[PerceivedObject] = Field(default_factory=list)
    observations: list[str] = Field(default_factory=list)
    uncertainties: list[str] = Field(default_factory=list)
    rejected_objects: list[dict[str, Any]] = Field(default_factory=list)

    @field_validator("observations", "uncertainties", mode="before")
    @classmethod
    def _normalise_diagnostic_text(cls, value: Any) -> Any:
        """Accept provider-specific string encoding for diagnostic fields.

        Some Anthropic-compatible OpenRouter models serialise optional
        ``list[str]`` tool parameters as one string.  These fields do not
        affect graph construction, so retaining that string as one diagnostic
        item is safer than rejecting otherwise valid object detections.  The
        engineering objects and their geometry remain strictly validated.
        """
        if value is None:
            return []
        if isinstance(value, list):
            out: list[str] = []
            for item in value:
                if isinstance(item, str):
                    text = item.strip()
                elif isinstance(item, dict) and isinstance(item.get("text"), str):
                    text = item["text"].strip()
                else:
                    text = json.dumps(item, ensure_ascii=False, sort_keys=True)
                if text:
                    out.append(text)
            return out
        if not isinstance(value, str):
            return value

        text = value.strip()
        if not text:
            return []
        try:
            decoded = json.loads(text)
        except (json.JSONDecodeError, TypeError):
            return [text]
        if isinstance(decoded, list):
            return [str(item).strip() for item in decoded if str(item).strip()]
        if isinstance(decoded, str):
            decoded = decoded.strip()
            return [decoded] if decoded else []
        return [text]


class DetectionRecord(BaseModel):
    id: str
    page_index: int
    tile_id: str
    kind: Literal["equipment", "instrument", "opc"]
    label: str
    bbox: BBox
    confidence: Confidence
    raw_text: str | None = None
    attributes: dict[str, Any] = Field(default_factory=dict)
    source_text_ids: list[str] = Field(default_factory=list)


class PerceptionResponseFormatError(ValueError):
    """A successful model response did not contain usable structured output."""

    def __init__(
        self,
        message: str,
        *,
        attempts: int = 1,
        diagnostics: list[dict[str, Any]] | None = None,
    ) -> None:
        super().__init__(message)
        self.attempts = attempts
        self.diagnostics = list(diagnostics or [])


@dataclass
class PerceptionOutcome:
    detections: list[DetectionRecord]
    batch: PerceptionBatch
    attempts: int = 1
    recovery_diagnostics: list[dict[str, Any]] = field(default_factory=list)


_SYSTEM_PROMPT = """\
Extract connectable engineering objects from one fixed P&ID tile. Python owns
navigation and coordinates. Return exactly one submit_pid_objects call.

Coordinate and ownership rules:
1. Every bbox is relative to THIS IMAGE and normalised to [0,1].
2. The JSON includes ownership_core_normalized. The image outside that core is
   context only. Emit an object only when the centre of its tight bbox is in
   the core. This prevents duplicates in overlapping tiles.
3. Nearby native words use the same normalised image frame. They are evidence,
   not entities and not coordinates to copy blindly.

Allowed objects:
- equipment: process equipment and significant inline valves.
- instrument: one real instrument/function symbol. Do not create a second
  instrument for the actuator/bubble of a tagged control valve.
- opc: only an explicit off-page continuation symbol with visible continuation
  evidence. Fill opc_direction, service, drawing_ref, or line_id only when the
  drawing supports them. A service phrase by itself is NOT an OPC.

Composite valve rule:
- An actuator glyph physically attached above a valve body is part of that
  valve, not a separate node. Emit one equipment object around the valve body.
- Set valve_type conservatively and set actuation to manual, solenoid,
  electric_motor, pneumatic, hydraulic, spring, or other only when the local
  symbol and supplied project legend support it.
- A project-legend boxed S attached to a valve is commonly actuation=solenoid;
  do not emit the S box as an instrument when the legend confirms this.

Text fields:
- printed_tag is the exact visible identifier, preserving punctuation/spaces.
- canonical_tag is a conservative normalised identifier. Omit it if unclear.
- Use the named typed fields. Do not put prose observations in object fields.

Positive examples: a pump symbol tagged P-101 is equipment; a PI-203 bubble is
an instrument; a boundary arrow marked TO SHEET 5 is an OPC.
Negative examples: pipe labels, service text, line numbers, drawing borders,
title blocks, notes, dimensions, leader arrows, empty rectangles, and nearby
words without a symbol are not objects.

Use a tight bbox, omit unsupported fields, and lower confidence rather than
guessing. Return {"objects":[]} when the ownership core has no objects.
"""


def _tool_input_schema() -> dict[str, Any]:
    object_schema = PerceivedObject.model_json_schema()
    definitions = object_schema.pop("$defs", {})
    object_schema.get("properties", {}).pop("attributes", None)
    object_schema["additionalProperties"] = False
    schema: dict[str, Any] = {
        "type": "object",
        "properties": {
            "objects": {
                "type": "array",
                "items": object_schema,
                "description": "Objects whose bbox centre is inside the ownership core.",
            }
        },
        "required": ["objects"],
        "additionalProperties": False,
    }
    if definitions:
        schema["$defs"] = definitions
    return schema


_SUBMIT_TOOL = {
    "name": "submit_pid_objects",
    "description": "Submit all connectable P&ID objects visible in this detail view.",
    "input_schema": _tool_input_schema(),
}

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.IGNORECASE)


def perceive_tile(
    *,
    client: LLMClient,
    cost_tracker: CostTracker,
    reporter: ProgressReporter,
    page: PageEvidence,
    tile: Tile,
    view_image: Any,
    view_info: ViewInfo,
    ownership_bbox: BBox,
    legend_summary: list[dict[str, str]] | None,
    step: int,
    page_context: dict[str, Any] | None = None,
    on_attempt: Callable[[], None] | None = None,
) -> PerceptionOutcome:
    nearby = text_spans_intersecting(page, tile.bbox)
    text_payload = [
        {
            "evidence_id": span.id,
            "text": span.text,
            "bbox_normalized": _page_bbox_to_normalized(span.bbox, view_info),
        }
        for span in nearby[:250]
    ]
    prompt = {
        "page_index": page.page_index,
        "page_role": page.role,
        "source_tile": tile.id,
        "ownership_core_normalized": _page_bbox_to_normalized(ownership_bbox, view_info),
        "nearby_native_text": text_payload,
        "legend_entries": list(legend_summary or [])[:80],
        "page_overview_context": dict(page_context or {}),
    }
    prompt_json = json.dumps(prompt, ensure_ascii=False, separators=(",", ":"))
    invalid_responses: list[dict[str, Any]] = []
    for attempt in range(1, 3):
        recovery_instruction = ""
        if attempt == 2:
            recovery_instruction = (
                "\nYour previous response could not be parsed. Do not explain or narrate. "
                "Call submit_pid_objects exactly once, using an empty objects array when needed."
            )
        messages = [
            {
                "role": "user",
                "content": [
                    encode_image_block(view_image),
                    {
                        "type": "text",
                        "text": (
                            "Inspect this high-resolution detail view and submit the structured "
                            "object list."
                            f"{recovery_instruction}\n{prompt_json}"
                        ),
                    },
                ],
            }
        ]
        if on_attempt is not None:
            on_attempt()
        try:
            response = client.messages_create(
                system=_SYSTEM_PROMPT,
                messages=messages,
                tools=[_SUBMIT_TOOL],
                tool_choice={"type": "tool", "name": "submit_pid_objects"},
                max_tokens=6000,
                thinking={"type": "disabled"},
                output_config={"effort": "low"},
                on_stream_delta=lambda kind, text: reporter.on_stream_delta(kind=kind, text=text),
            )
        except ValueError as exc:
            if not is_malformed_tool_json_error(exc):
                raise
            invalid_responses.append(
                {
                    "attempt": attempt,
                    "error": str(exc),
                    "phase": "provider_tool_json_decode",
                    "response": None,
                }
            )
            if attempt == 2:
                raise PerceptionResponseFormatError(
                    "perception tool arguments were malformed after one recovery attempt",
                    attempts=attempt,
                    diagnostics=invalid_responses,
                ) from exc
            continue
        _report_response_content(response, reporter)
        cost_tracker.record(
            response,
            step=step + attempt - 1,
            tile_id=tile.id,
            page_index=page.page_index,
        )
        reporter.on_token_update(total_tokens=cost_tracker.total_tokens())
        try:
            batch = parse_perception_response(response, page=page, view_info=view_info)
        except PerceptionResponseFormatError as exc:
            invalid_responses.append(
                {
                    "attempt": attempt,
                    "error": str(exc),
                    "response": _response_diagnostic(response),
                }
            )
            if attempt == 2:
                raise PerceptionResponseFormatError(
                    "perception response was unstructured after one recovery attempt",
                    attempts=attempt,
                    diagnostics=invalid_responses,
                ) from exc
            continue

        detections = project_batch(
            batch=batch,
            page=page,
            tile=tile,
            view_info=view_info,
            nearby_text_ids={span.id for span in nearby},
            ownership_bbox=ownership_bbox,
        )
        return PerceptionOutcome(
            detections=detections,
            batch=batch,
            attempts=attempt,
            recovery_diagnostics=invalid_responses,
        )

    raise AssertionError("perception recovery loop exited unexpectedly")


def parse_perception_response(
    response: Any,
    *,
    page: PageEvidence | None = None,
    view_info: ViewInfo | None = None,
) -> PerceptionBatch:
    text_parts: list[str] = []
    for block in getattr(response, "content", None) or []:
        block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
        if block_type == "tool_use":
            name = block.get("name") if isinstance(block, dict) else getattr(block, "name", None)
            if name == "submit_pid_objects":
                value = (
                    block.get("input") if isinstance(block, dict) else getattr(block, "input", None)
                )
                return _validate_perception_payload(
                    _normalise_perception_payload(value or {}, page=page, view_info=view_info)
                )
        elif block_type == "text":
            value = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
            if value:
                text_parts.append(str(value))

    raw = "\n".join(text_parts).strip()
    if not raw:
        raise PerceptionResponseFormatError(
            "perception response contained neither tool input nor JSON text"
        )
    raw = _FENCE_RE.sub("", raw).strip()
    try:
        value = json.loads(raw)
    except json.JSONDecodeError:
        start = raw.find("{")
        end = raw.rfind("}")
        if start < 0 or end <= start:
            raise PerceptionResponseFormatError(
                "perception response did not contain a JSON object"
            ) from None
        try:
            value = json.loads(raw[start : end + 1])
        except json.JSONDecodeError as exc:
            raise PerceptionResponseFormatError(
                f"perception response contained invalid JSON: {exc.msg}"
            ) from None
    return _validate_perception_payload(
        _normalise_perception_payload(value, page=page, view_info=view_info)
    )


def _response_diagnostic(response: Any) -> dict[str, Any]:
    """Return a JSON-safe response snapshot without echoing request image data."""
    content: list[Any] = []
    for block in getattr(response, "content", None) or []:
        if isinstance(block, dict):
            content.append(_json_safe(block))
        elif hasattr(block, "model_dump"):
            content.append(_json_safe(block.model_dump(mode="json")))
        else:
            content.append(
                _json_safe(
                    {
                        key: getattr(block, key)
                        for key in (
                            "type",
                            "text",
                            "thinking",
                            "reasoning",
                            "name",
                            "input",
                        )
                        if getattr(block, key, None) is not None
                    }
                )
            )
    return _json_safe(
        {
            "id": getattr(response, "id", None),
            "model": getattr(response, "model", None),
            "stop_reason": getattr(response, "stop_reason", None),
            "content": content,
        }
    )


def _json_safe(value: Any) -> Any:
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "model_dump"):
        return _json_safe(value.model_dump(mode="json"))
    return repr(value)


def _validate_perception_payload(value: Any) -> PerceptionBatch:
    """Validate objects independently so one malformed sibling is recoverable."""
    if not isinstance(value, dict):
        return PerceptionBatch.model_validate(value)
    raw_objects = value.get("objects", [])
    if not isinstance(raw_objects, list):
        return PerceptionBatch.model_validate(value)

    accepted: list[PerceivedObject] = []
    rejected: list[dict[str, Any]] = []
    for index, item in enumerate(raw_objects):
        try:
            accepted.append(PerceivedObject.model_validate(item))
        except Exception as exc:  # noqa: BLE001 - retain valid siblings from one call
            rejected.append({"index": index, "error": str(exc)})
    if raw_objects and not accepted:
        raise ValueError(
            f"all {len(raw_objects)} perception object(s) were invalid: " + rejected[0]["error"]
        )

    diagnostics = dict(value)
    diagnostics["objects"] = accepted
    diagnostics["rejected_objects"] = rejected
    return PerceptionBatch.model_validate(diagnostics)


def _normalise_perception_payload(
    value: Any,
    *,
    page: PageEvidence | None,
    view_info: ViewInfo | None,
) -> Any:
    if not isinstance(value, dict):
        return value
    payload = dict(value)
    objects = payload.get("objects", [])
    if isinstance(objects, str):
        decoded = _decode_json_array(objects)
        if decoded is not None:
            objects = decoded
            payload["objects"] = objects
    if not isinstance(objects, list) or page is None or view_info is None:
        return payload

    normalised_objects: list[Any] = []
    for item in objects:
        if not isinstance(item, dict) or not isinstance(item.get("bbox"), dict):
            normalised_objects.append(item)
            continue
        obj = dict(item)
        bbox, recovery = _recover_bbox_payload(obj["bbox"], page=page, view_info=view_info)
        obj["bbox"] = bbox
        if recovery != "normalized":
            attributes = dict(obj.get("attributes") or {})
            attributes.setdefault("coordinate_recovery", recovery)
            obj["attributes"] = attributes
        normalised_objects.append(obj)
    payload["objects"] = normalised_objects
    return payload


def _decode_json_array(value: str) -> list[Any] | None:
    text = _FENCE_RE.sub("", value.strip()).strip()
    candidates = [text]
    start = text.find("[")
    end = text.rfind("]")
    if start >= 0 and end > start:
        candidates.append(text[start : end + 1])
    for candidate in candidates:
        try:
            decoded = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(decoded, list):
            return decoded
    return None


def _recover_bbox_payload(
    value: dict[str, Any],
    *,
    page: PageEvidence,
    view_info: ViewInfo,
) -> tuple[dict[str, float], str]:
    try:
        x, y, w, h = (float(value[key]) for key in ("x", "y", "w", "h"))
    except (KeyError, TypeError, ValueError):
        return value, "normalized"
    if not all(math.isfinite(part) for part in (x, y, w, h)) or w <= 0 or h <= 0:
        return value, "normalized"

    clipped = _clip_small_overflow(x=x, y=y, w=w, h=h, width=1.0, height=1.0)
    if clipped is not None:
        recovery = "normalized" if clipped == (x, y, w, h) else "normalized_clipped"
        return _bbox_dict(clipped), recovery

    page_candidate = _clip_small_overflow(
        x=x, y=y, w=w, h=h, width=float(page.width), height=float(page.height)
    )
    if page_candidate is not None and not _mostly_inside(
        page_candidate, _bbox_tuple(view_info.page_bbox)
    ):
        page_candidate = None

    view_candidate = _clip_small_overflow(
        x=x,
        y=y,
        w=w,
        h=h,
        width=float(view_info.view_size[0]),
        height=float(view_info.view_size[1]),
    )
    local_as_page = (
        _local_pixels_to_page(view_candidate, view_info=view_info)
        if view_candidate is not None
        else None
    )
    if local_as_page is not None and not _mostly_inside(
        local_as_page, _bbox_tuple(view_info.page_bbox)
    ):
        view_candidate = None
        local_as_page = None

    if page_candidate is not None and view_candidate is not None:
        if local_as_page is None or not _boxes_nearly_equal(page_candidate, local_as_page):
            raise ValueError(
                "bbox coordinates are ambiguous between page-global and tile-local pixels"
            )
        return _page_pixels_to_normalized(page_candidate, view_info), "page_pixels"
    if page_candidate is not None:
        return _page_pixels_to_normalized(page_candidate, view_info), "page_pixels"
    if view_candidate is not None:
        return _view_pixels_to_normalized(view_candidate, view_info), "tile_pixels"
    return value, "normalized"


def _clip_small_overflow(
    *,
    x: float,
    y: float,
    w: float,
    h: float,
    width: float,
    height: float,
) -> tuple[float, float, float, float] | None:
    left = max(0.0, x)
    top = max(0.0, y)
    right = min(width, x + w)
    bottom = min(height, y + h)
    if right <= left or bottom <= top:
        return None
    retained = ((right - left) * (bottom - top)) / (w * h)
    tolerance_x = max(width * 0.05, 1e-9)
    tolerance_y = max(height * 0.05, 1e-9)
    if (
        retained < 0.8
        or x < -tolerance_x
        or y < -tolerance_y
        or x + w > width + tolerance_x
        or y + h > height + tolerance_y
    ):
        return None
    return left, top, right - left, bottom - top


def _mostly_inside(
    candidate: tuple[float, float, float, float],
    container: tuple[float, float, float, float],
) -> bool:
    x, y, w, h = candidate
    cx, cy, cw, ch = container
    left = max(x, cx)
    top = max(y, cy)
    right = min(x + w, cx + cw)
    bottom = min(y + h, cy + ch)
    if right <= left or bottom <= top:
        return False
    return ((right - left) * (bottom - top)) / (w * h) >= 0.8


def _bbox_tuple(bbox: BBox) -> tuple[float, float, float, float]:
    return float(bbox.x), float(bbox.y), float(bbox.w), float(bbox.h)


def _local_pixels_to_page(
    bbox: tuple[float, float, float, float], *, view_info: ViewInfo
) -> tuple[float, float, float, float]:
    x, y, w, h = bbox
    sx = view_info.scale_x or 1.0
    sy = view_info.scale_y or 1.0
    return (
        view_info.origin[0] + x / sx,
        view_info.origin[1] + y / sy,
        w / sx,
        h / sy,
    )


def _page_pixels_to_normalized(
    bbox: tuple[float, float, float, float], view_info: ViewInfo
) -> dict[str, float]:
    x, y, w, h = bbox
    sx = view_info.scale_x or 1.0
    sy = view_info.scale_y or 1.0
    return _bbox_dict(
        (
            (x - view_info.origin[0]) * sx / view_info.view_size[0],
            (y - view_info.origin[1]) * sy / view_info.view_size[1],
            w * sx / view_info.view_size[0],
            h * sy / view_info.view_size[1],
        )
    )


def _page_bbox_to_normalized(bbox: BBox, view_info: ViewInfo) -> dict[str, float]:
    """Express page-space evidence in the model image's only coordinate frame."""
    raw = _page_pixels_to_normalized(_bbox_tuple(bbox), view_info)
    left = max(0.0, min(1.0, raw["x"]))
    top = max(0.0, min(1.0, raw["y"]))
    right = max(left, min(1.0, raw["x"] + raw["w"]))
    bottom = max(top, min(1.0, raw["y"] + raw["h"]))
    return {"x": left, "y": top, "w": right - left, "h": bottom - top}


def _view_pixels_to_normalized(
    bbox: tuple[float, float, float, float], view_info: ViewInfo
) -> dict[str, float]:
    x, y, w, h = bbox
    return _bbox_dict(
        (
            x / view_info.view_size[0],
            y / view_info.view_size[1],
            w / view_info.view_size[0],
            h / view_info.view_size[1],
        )
    )


def _boxes_nearly_equal(
    left: tuple[float, float, float, float],
    right: tuple[float, float, float, float],
) -> bool:
    return all(abs(a - b) <= 1.0 for a, b in zip(left, right, strict=True))


def _bbox_dict(value: tuple[float, float, float, float]) -> dict[str, float]:
    return dict(zip(("x", "y", "w", "h"), value, strict=True))


def _report_response_content(response: Any, reporter: ProgressReporter) -> None:
    for block in getattr(response, "content", None) or []:
        block_type = block.get("type") if isinstance(block, dict) else getattr(block, "type", None)
        if block_type == "thinking":
            value = (
                block.get("thinking")
                if isinstance(block, dict)
                else getattr(block, "thinking", None)
            )
            if value:
                reporter.on_thinking(text=str(value))
        elif block_type == "text":
            value = block.get("text") if isinstance(block, dict) else getattr(block, "text", None)
            if value:
                reporter.on_text(text=str(value))


def project_batch(
    *,
    batch: PerceptionBatch,
    page: PageEvidence,
    tile: Tile,
    view_info: ViewInfo,
    nearby_text_ids: set[str],
    ownership_bbox: BBox | None = None,
) -> list[DetectionRecord]:
    out: list[DetectionRecord] = []
    for index, obj in enumerate(batch.objects):
        bbox = _project_normalized_bbox(obj.bbox, page=page, view_info=view_info)
        if ownership_bbox is not None and not _bbox_center_is_owned(bbox, ownership_bbox, page):
            continue
        source_text_ids = sorted(set(obj.source_text_ids).intersection(nearby_text_ids))
        label = " ".join(obj.label.split()).strip()
        raw_text = " ".join((obj.raw_text or "").split()).strip() or None
        attributes = obj.graph_attributes()
        attributes["source_tile"] = tile.id
        attributes["model_confidence"] = obj.confidence
        if source_text_ids:
            attributes["source_text_ids"] = source_text_ids
        detection_id = stable_evidence_id(
            "det",
            page.page_index,
            tile.id,
            index,
            obj.kind,
            label,
            bbox.model_dump_json(),
        )
        out.append(
            DetectionRecord(
                id=detection_id,
                page_index=page.page_index,
                tile_id=tile.id,
                kind=obj.kind,
                label=label,
                bbox=bbox,
                confidence=obj.confidence,
                raw_text=raw_text,
                attributes=attributes,
                source_text_ids=source_text_ids,
            )
        )
    return out


def _bbox_center_is_owned(bbox: BBox, core: BBox, page: PageEvidence) -> bool:
    center_x = bbox.x + bbox.w / 2
    center_y = bbox.y + bbox.h / 2
    right_owned = center_x < core.x2 or core.x2 >= page.width
    bottom_owned = center_y < core.y2 or core.y2 >= page.height
    return center_x >= core.x and center_y >= core.y and right_owned and bottom_owned


def _project_normalized_bbox(
    bbox: NormalizedBBox,
    *,
    page: PageEvidence,
    view_info: ViewInfo,
) -> BBox:
    local_x0 = bbox.x * view_info.view_size[0]
    local_y0 = bbox.y * view_info.view_size[1]
    local_x1 = (bbox.x + bbox.w) * view_info.view_size[0]
    local_y1 = (bbox.y + bbox.h) * view_info.view_size[1]
    sx = view_info.scale_x or 1.0
    sy = view_info.scale_y or 1.0
    x0 = view_info.origin[0] + local_x0 / sx
    y0 = view_info.origin[1] + local_y0 / sy
    x1 = view_info.origin[0] + local_x1 / sx
    y1 = view_info.origin[1] + local_y1 / sy
    left = max(0, min(page.width - 1, int(round(min(x0, x1)))))
    top = max(0, min(page.height - 1, int(round(min(y0, y1)))))
    right = max(left + 1, min(page.width, int(round(max(x0, x1)))))
    bottom = max(top + 1, min(page.height, int(round(max(y0, y1)))))
    return BBox(x=left, y=top, w=right - left, h=bottom - top)
