"""Pack auxiliary image references without changing the source coordinate frame."""

from __future__ import annotations

import base64
import io
import math

from PIL import Image, ImageDraw

from diagex.vision.encode import encode_image_block


def contact_sheet(blocks: list[dict], *, title: str, columns: int = 2) -> list[dict]:
    """Combine text/image pairs into numbered panels, preserving native pixels.

    Only auxiliary references belong here. The primary drawing and its coordinate
    system must remain separate. Single-image inputs retain their original blocks.
    """
    if sum(block.get("type") == "image" for block in blocks) <= 1:
        return blocks
    panels = []
    captions = []
    for block in blocks:
        if block["type"] == "text":
            captions.append(block["text"])
        elif block["type"] == "image":
            with Image.open(io.BytesIO(base64.b64decode(block["source"]["data"]))) as image:
                panels.append((image.convert("RGB"), "\n".join(captions)))
            captions = []
    columns = min(columns, len(panels))
    width = max(image.width for image, _ in panels) + 16
    height = max(image.height for image, _ in panels) + 40
    sheet = Image.new("RGB", (columns * width, math.ceil(len(panels) / columns) * height), "white")
    draw = ImageDraw.Draw(sheet)
    mapping = []
    for index, (image, caption) in enumerate(panels):
        x, y = index % columns * width, index // columns * height
        draw.rectangle((x, y, x + width - 1, y + height - 1), outline="#a0a0a0")
        draw.text((x + 8, y + 6), f"Panel {index + 1}", fill="black")
        sheet.paste(image, (x + 8, y + 30))
        mapping.append(f"Panel {index + 1}: {caption}")
    return [{"type": "text", "text": (
        f"{title}. Numbered auxiliary panels, not a drawing coordinate frame. "
        "Keep all detection coordinates in the original source image.\n" + "\n".join(mapping)
    )}, encode_image_block(sheet)]
