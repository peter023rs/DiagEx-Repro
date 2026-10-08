"""Small synthetic vector geometry shared by detection tests."""

from diagex.vision.evidence import PageEvidence, PathEvidence
from diagex.vision.models import BBox


def path(name, points, primitive="line", **kwargs):
    xs, ys = zip(*points, strict=True)
    return PathEvidence(
        id=name,
        page_index=0,
        points=points,
        bbox=BBox(x=min(xs), y=min(ys), w=max(1, max(xs) - min(xs)), h=max(1, max(ys) - min(ys))),
        origin="pdf_vector",
        primitive=primitive,
        **kwargs,
    )


def page(paths, *, nodes=()):
    # Topology fixtures include actual native endpoint glyphs. A box by itself
    # deliberately no longer certifies connectivity; new tests cover that case.
    paths = list(paths)
    for n in nodes:
        if n.attributes.get("equipment_class"):
            continue
        b = n.bbox_global
        paths.append(
            path(
                "glyph-" + n.id,
                [(b.x, b.y), (b.x2, b.y), (b.x2, b.y2), (b.x, b.y2), (b.x, b.y)],
                "rect",
                closed=True,
            )
        )
    return PageEvidence(
        page_index=0,
        source_ref="synthetic-vector",
        width=1000,
        height=800,
        dpi=100,
        effective_dpi=100,
        is_scanned=False,
        paths=paths,
    )


def body():
    # Deliberately fragmented, with head chords and long nozzle strokes.
    return [
        path("left-wall", [(400, 200), (400, 500)]),
        path("right-wall", [(600, 200), (600, 500)]),
        path("top", [(400, 200), (400, 133), (600, 133), (600, 200)], "curve"),
        path("bottom", [(600, 500), (600, 567), (400, 567), (400, 500)], "curve"),
        path("chord", [(400, 200), (600, 200)]),
    ]


def rectangle(name, x, y, w, h):
    return path(name, [(x, y), (x + w, y), (x + w, y + h), (x, y + h), (x, y)], "rect", closed=True)


def public_candidates(stem: str) -> list[dict]:
    import math
    from pathlib import Path

    import fitz

    from diagex.vision.evidence import extract_page_evidence
    from diagex.vision.models import DiagramPage
    from diagex.vision.symbol_candidates import symbol_candidates

    pdf = Path(__file__).resolve().parents[1] / "p-ids-public" / f"{stem}.pdf"
    cs = []
    with fitz.open(pdf) as doc:
        for i, p in enumerate(doc):
            dpi = min(300.0, 6000 * 72 / max(p.rect.width, p.rect.height))
            page = DiagramPage(
                page_index=i,
                width=math.ceil(p.rect.width * dpi / 72),
                height=math.ceil(p.rect.height * dpi / 72),
                dpi=dpi,
                effective_dpi=dpi,
                is_scanned=False,
                source_ref=f"{stem}#page={i + 1}",
            )
            evidence = extract_page_evidence(page=page, source_path=pdf, pdf_page=p)
            cs.extend(c.model_dump(mode="json") for c in symbol_candidates(evidence))
    return cs
