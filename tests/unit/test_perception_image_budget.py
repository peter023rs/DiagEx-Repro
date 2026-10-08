"""Image bounds apply to both initial inspection and candidate recovery."""

import base64
import io

import pytest
from PIL import Image

from diagex.config import SymbolPerceptionConfig
from diagex.llm.cost import CostTracker
from diagex.ui.progress import NullReporter
from diagex.vision.contact_sheet import contact_sheet
from diagex.vision.encode import encode_image_block
from diagex.vision.models import BBox, Tile
from diagex.vision.perception import perceive_tile
from diagex.vision.symbol_candidates import symbol_candidates
from tests.unit.detection_fixtures import page
from tests.unit.test_legend_context import definition
from tests.unit.test_symbol_perception import circle, view
from tests.unit.test_symbol_response_contract import reply


@pytest.mark.parametrize("workflow", ["fixed", "adaptive"])
def test_reinspection_retains_four_candidates_and_legend_with_four_images(workflow):
    p = page([circle(f"c{i}", 100 + 150 * i, 100) for i in range(4)])
    candidates = symbol_candidates(p)
    box = BBox(x=0, y=0, w=p.width, h=p.height)
    source = Image.new("RGB", (500, 320), "white")
    calls = []

    class Client:
        def messages_create(self, **kwargs):
            content = kwargs["messages"][0]["content"]
            calls.append(content)
            assert sum(block["type"] == "image" for block in content) <= 4
            assert content[0] == encode_image_block(source)
            # Initially missing candidate outcomes force the real recovery path.
            return reply([] if len(calls) == 1 else [
                {"candidate_id": c.id, "decision": "symbol", "kind": "instrument"}
                for c in candidates
            ])

    def region_provider(*args):
        return source, view(box)

    result = perceive_tile(
        client=Client(), cost_tracker=CostTracker(), reporter=NullReporter(),
        page=p, tile=Tile(id="t", page_index=0, bbox=box),
        view_image=source, view_info=view(box), ownership_bbox=box,
        legend_summary=[definition("round_symbol", i) for i in range(12)],
        step=1, candidates=candidates, policy=SymbolPerceptionConfig(workflow=workflow),
        overview_image=source, region_provider=region_provider,
    )
    assert len(calls) == 2
    assert len(result.detections) == 4
    assert {d.attributes["symbol_candidate_id"] for d in result.detections} == {c.id for c in candidates}
    recovery_captions = "\n".join(block["text"] for block in calls[1] if block["type"] == "text")
    assert all(f"detail for {c.id}" in recovery_captions for c in candidates)
    if workflow == "adaptive":
        assert all(f"source region around {c.id}" in recovery_captions for c in candidates)
    assert all(f"round_symbol-{i}" in recovery_captions for i in range(12))


def test_contact_sheet_preserves_every_panel_pixel_and_caption():
    images = [Image.new("RGB", (64, 32), color) for color in ("red", "green", "blue")]
    blocks = []
    for i, image in enumerate(images):
        blocks.extend([{"type": "text", "text": f"reference-{i}"}, encode_image_block(image)])
    result = contact_sheet(blocks, title="References")
    with Image.open(io.BytesIO(base64.b64decode(result[1]["source"]["data"]))) as sheet:
        for i, image in enumerate(images):
            x, y = i % 2 * 80 + 8, i // 2 * 72 + 30
            assert sheet.crop((x, y, x + 64, y + 32)).tobytes() == image.tobytes()
            assert f"Panel {i + 1}: reference-{i}" in result[0]["text"]
