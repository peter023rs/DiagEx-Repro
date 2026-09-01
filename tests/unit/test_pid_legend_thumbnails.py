from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from diagex.config import PidConfig
from diagex.extractors.pid_legend import (
    _annotation_to_entry,
    _dedupe,
    _load_cached,
    _thumbnail_b64,
)
from diagex.vision.evidence import PageEvidence, PathEvidence, TextEvidence
from diagex.vision.legend_models import LegendEntry, LegendPack
from diagex.vision.models import Annotation, BBox, DiagramPage


def _page_and_evidence() -> tuple[DiagramPage, PageEvidence]:
    image = Image.new("RGB", (400, 200), "white")
    draw = ImageDraw.Draw(image)
    draw.line((50, 80, 80, 100), fill="black", width=3)
    draw.line((80, 100, 50, 120), fill="black", width=3)
    draw.line((50, 120, 50, 80), fill="black", width=3)
    page = DiagramPage(
        page_index=0,
        image=image,
        width=400,
        height=200,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        source_ref="test#page=0",
    )
    paths = [
        PathEvidence(
            id=f"path-{index}",
            page_index=0,
            points=points,
            bbox=bbox,
            origin="pdf_vector",
            primitive="line",
        )
        for index, (points, bbox) in enumerate(
            (
                ([(50, 80), (80, 100)], BBox(x=50, y=80, w=30, h=20)),
                ([(80, 100), (50, 120)], BBox(x=50, y=100, w=30, h=20)),
                ([(50, 120), (50, 80)], BBox(x=50, y=80, w=1, h=40)),
            )
        )
    ]
    evidence = PageEvidence(
        page_index=0,
        source_ref=page.source_ref,
        width=400,
        height=200,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        role="legend",
        text_spans=[
            TextEvidence(
                id="label",
                text="电磁执行机构",
                bbox=BBox(x=130, y=88, w=110, h=24),
            ),
            TextEvidence(
                id="wrong",
                text="错误文字",
                bbox=BBox(x=280, y=20, w=80, h=24),
            ),
        ],
        paths=paths,
    )
    return page, evidence


def _annotation(*, legend_kind: str = "symbol") -> Annotation:
    wrong = BBox(x=280, y=20, w=80, h=24)
    return Annotation(
        page_index=0,
        kind="equipment",
        source_view="tile",
        bbox_local=wrong,
        bbox_global=wrong,
        label="电磁执行机构",
        attributes={
            "legend_kind": legend_kind,
            "legend_symbol_class": "unclassified_equipment",
        },
        confidence="high",
    )


def test_native_text_and_paths_recover_a_suspicious_model_crop() -> None:
    page, evidence = _page_and_evidence()

    entry = _annotation_to_entry(
        annotation=_annotation(),
        page=page,
        origin=(0, 0),
        cfg_pid=PidConfig(),
        page_evidence=evidence,
    )

    assert entry is not None
    assert entry.image_b64 is not None
    assert entry.crop_method == "native_text_paths"
    assert entry.crop_quality == "recovered"
    assert entry.source_page_index == 0
    assert entry.source_label_bbox == BBox(x=130, y=88, w=110, h=24)
    assert entry.source_bbox is not None
    assert entry.source_bbox.x < 100


def test_abbreviation_does_not_create_a_fake_symbol_thumbnail() -> None:
    page, evidence = _page_and_evidence()

    entry = _annotation_to_entry(
        annotation=_annotation(legend_kind="abbreviation"),
        page=page,
        origin=(0, 0),
        cfg_pid=PidConfig(),
        page_evidence=evidence,
    )

    assert entry is not None
    assert entry.image_b64 is None
    assert entry.crop_quality == "omitted_abbreviation"


def test_duplicate_pixels_for_different_labels_are_omitted() -> None:
    image = Image.new("RGB", (20, 20), "white")
    ImageDraw.Draw(image).line((2, 10, 18, 10), fill="black", width=2)
    encoded = _thumbnail_b64(image, 128)
    entries = [
        LegendEntry(
            label=label,
            symbol_class="line",
            kind="line",
            image_b64=encoded,
            source="legend_extracted",
        )
        for label in ("process line", "signal line")
    ]

    sanitized = _dedupe(entries)

    assert all(entry.image_b64 is None for entry in sanitized)
    assert all(entry.crop_quality == "rejected_duplicate" for entry in sanitized)


def test_old_or_different_extractor_cache_is_not_loaded(tmp_path: Path) -> None:
    path = tmp_path / "legend.cache.json"
    path.write_text(
        LegendPack(
            schema_version="0.1.0",
            source_hash="source",
            extractor_fingerprint="old",
        ).model_dump_json(),
        encoding="utf-8",
    )

    assert _load_cached(path, "source", "current") is None

