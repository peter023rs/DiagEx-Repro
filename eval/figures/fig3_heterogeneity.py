"""Figure 3 — corpus heterogeneity illustration.

Three side-by-side crops drawn from different fixtures in the diagex
corpus, illustrating the visual variety DiagEx must handle: vector vs. raster
drawings, three different authoring pipelines, and three different process
domains. Crop windows live in ``eval/figures/fig3_crops.json`` so the figure
can be retargeted without touching the renderer.

Source images are the pre-rendered authoring PNGs under
``tools/via/images/<fixture>.png``; coordinates are interpreted directly in
that PNG's pixel frame.
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_ROOT = Path(__file__).resolve().parents[2]
_DEFAULT_SIDECAR = _ROOT / "eval" / "figures" / "fig3_crops.json"


@dataclass
class _Panel:
    fixture: str
    image_png: str
    title: str
    x: int
    y: int
    w: int
    h: int


def _load_panels(sidecar: Path) -> list[_Panel]:
    cfg = json.loads(sidecar.read_text(encoding="utf-8"))
    return [
        _Panel(**{k: p[k] for k in ("fixture", "image_png", "title", "x", "y", "w", "h")})
        for p in cfg["panels"]
    ]


def render_figure3_placeholder(out_path: Path, *, note: str = "") -> Path:
    """Write a placeholder PDF announcing the figure is not yet authored."""
    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("matplotlib required for Figure 3 placeholder") from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(7.0, 2.4))
    ax.axis("off")
    msg = "Figure 3 placeholder — corpus heterogeneity illustration"
    if note:
        msg += f"\n{note}"
    ax.text(0.5, 0.5, msg, ha="center", va="center", fontsize=8, wrap=True)
    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return out_path


def render_figure3(out_path: Path, *, sidecar: Path = _DEFAULT_SIDECAR,
                   **_kwargs: Any) -> Path:
    """Render the corpus-heterogeneity figure to ``out_path`` (PDF)."""
    if not sidecar.exists():
        return render_figure3_placeholder(out_path, note=f"sidecar missing: {sidecar}")

    panels = _load_panels(sidecar)
    for p in panels:
        if not (_ROOT / p.image_png).exists():
            return render_figure3_placeholder(
                out_path, note=f"missing input: {p.image_png}",
            )

    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover
        raise RuntimeError("matplotlib required for Figure 3") from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    Image.MAX_IMAGE_PIXELS = None  # butane1.png is ~100 Mpx; opt out of the bomb guard

    # Size each panel so its display width in inches matches its crop's pixel width
    # at the chosen savefig DPI; this keeps every source pixel in the embedded PDF
    # raster instead of letting matplotlib resample a 3000 px crop down to ~700 px.
    save_dpi = 600
    panel_h_in = 3.2  # axes height in inches; panel widths follow the crop aspect
    panel_widths_in = [(panel_h_in * panel.w / panel.h) for panel in panels]
    fig_w = sum(panel_widths_in) + 0.4 * (len(panels) - 1) + 0.6
    fig_h = panel_h_in + 0.6  # extra room for titles

    fig, axes = plt.subplots(
        1, len(panels), figsize=(fig_w, fig_h),
        gridspec_kw={"width_ratios": panel_widths_in},
    )
    if len(panels) == 1:
        axes = [axes]

    for ax, panel in zip(axes, panels):
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            img = Image.open(_ROOT / panel.image_png)
        crop = img.crop((panel.x, panel.y, panel.x + panel.w, panel.y + panel.h))
        ax.imshow(crop, interpolation="nearest", resample=False)
        ax.set_xticks([])
        ax.set_yticks([])
        ax.set_title(panel.title, fontsize=14)

    fig.tight_layout(pad=0.4)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, format="pdf", bbox_inches="tight", dpi=save_dpi)
    plt.close(fig)
    return out_path


def main() -> None:
    """``python -m eval.figures.fig3_heterogeneity`` writes the figure next to fig2."""
    out = _ROOT / "out" / "diagex-phase2" / "figures" / "fig3_heterogeneity.pdf"
    render_figure3(out)
    print(f"wrote {out.relative_to(_ROOT)}")


if __name__ == "__main__":
    main()
