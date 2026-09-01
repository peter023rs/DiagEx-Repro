from __future__ import annotations

from diagex.vision.evidence import PageEvidence, TextEvidence
from diagex.vision.legend_models import LegendPack
from diagex.vision.legend_tables import extract_abbreviation_tables
from diagex.vision.models import BBox


def _span(identifier: str, text: str, x: int, y: int) -> TextEvidence:
    return TextEvidence(id=identifier, text=text, bbox=BBox(x=x, y=y, w=70, h=20))


def _page() -> PageEvidence:
    spans = [_span("heading", "仪表类型缩写", 300, 40)]
    values = (
        ("AE", "分析元件"),
        ("PI", "压力指示"),
        ("*PT", "压力变送器"),
        ("PV", "压力调节阀"),
    )
    for index, (code, meaning) in enumerate(values):
        y = 85 + index * 35
        spans.extend(
            (
                _span(f"code-{index}", code, 220, y),
                _span(f"meaning-{index}", meaning, 310, y),
            )
        )
    # Repeated unrelated text outside the heading-derived table window must
    # not be absorbed merely because it looks like an abbreviation column.
    for index in range(5):
        spans.append(_span(f"noise-{index}", f"N{index}", 900, 85 + index * 35))
    return PageEvidence(
        page_index=2,
        source_ref="drawing#page=3",
        width=1200,
        height=800,
        dpi=300,
        effective_dpi=300,
        is_scanned=False,
        role="legend",
        text_spans=spans,
    )


def test_reconstructs_instrument_abbreviation_rows_from_native_text() -> None:
    inventory = extract_abbreviation_tables([_page()])

    assert inventory.summary["row_count"] == 4
    assert inventory.summary["instrument_type_count"] == 4
    assert {row.canonical_code for row in inventory.rows} == {"AE", "PI", "PT", "PV"}
    pt = next(row for row in inventory.rows if row.canonical_code == "PT")
    assert pt.printed_code == "*PT"
    assert pt.raw_description == "压力变送器"
    assert pt.attributes["instrument_function"] == "transmitter"


def test_project_abbreviation_entries_override_builtins() -> None:
    inventory = extract_abbreviation_tables([_page()])
    builtin = LegendPack.model_validate(
        {
            "entries": [
                {
                    "label": "PI",
                    "description": "pressure indicator",
                    "symbol_class": "indicator",
                    "kind": "instrument",
                }
            ]
        }
    )

    merged = inventory.to_legend_pack(base=builtin).merge(builtin)

    pi = next(entry for entry in merged.entries if entry.label == "PI")
    assert pi.description == "压力指示"
    assert pi.source == "legend_extracted"
    assert pi.attributes["native_text_reconstructed"] == "true"
