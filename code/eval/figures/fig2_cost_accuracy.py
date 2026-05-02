"""Figure 2 — cost vs entity-count scatter. Plan §5.3.

Inputs come from ``eval.aggregate.figure2_points``. One marker per fixture;
shape encodes source type (vector / raster / scanned), colour encodes overall
F1 bucket. Log-x on entity count.

Matplotlib is a soft dependency — the eval driver still runs CSV/LaTeX
emission if matplotlib is missing; only this module's writer raises.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# YlGn-sampled palette: monotonic in luminance (low F1 light, high F1 dark)
# so the ramp survives a black-and-white printout, and high F1 lands on
# green to match the conventional "green = good" intuition.
_F1_BUCKETS = (
    (0.0, 0.5, "#ffffcc", "<0.5"),
    (0.5, 0.7, "#c2e699", "0.5–0.7"),
    (0.7, 0.85, "#78c679", "0.7–0.85"),
    (0.85, 1.01, "#238443", "≥0.85"),
)
_SHAPE_BY_SOURCE = {"vector": "o", "raster": "s", "scanned": "^"}
_X_TICKS = (20, 30, 40, 60, 100, 200)


def _bucket_colour(f1: float) -> str:
    for lo, hi, colour, _ in _F1_BUCKETS:
        if lo <= f1 < hi:
            return colour
    return "#999999"


def render_figure2(points: pd.DataFrame, out_path: Path) -> Path:
    """Write ``out_path`` (PDF). ``points`` from ``aggregate.figure2_points``."""
    try:
        import matplotlib
    except ImportError as exc:  # pragma: no cover - environment-dependent
        raise RuntimeError(
            "matplotlib is required to render Figure 2; install with "
            "`pip install matplotlib` or pass --skip-figures to the driver."
        ) from exc
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(4.0, 3.0))

    if points.empty:
        ax.text(0.5, 0.5, "(no Phase 2 points)", ha="center", va="center",
                transform=ax.transAxes)
        fig.savefig(out_path, format="pdf", bbox_inches="tight")
        plt.close(fig)
        return out_path

    xs = [float(r.get("entity_count_truth") or 1) for _, r in points.iterrows()]
    x_max = max(xs) if xs else 1.0
    # Right-align the annotation when the marker sits near the right edge so
    # the fixture label (e.g. "two-tanks") does not run past the axes border.
    right_threshold = x_max * 0.85

    for _, row in points.iterrows():
        marker = _SHAPE_BY_SOURCE.get(str(row.get("source_type", "")), "x")
        colour = _bucket_colour(float(row.get("overall_f1") or 0.0))
        x = float(row.get("entity_count_truth") or 1)
        y = float(row.get("cost_usd") or 0.0)
        ax.scatter(x, y, marker=marker, color=colour, s=36, edgecolor="black",
                   linewidth=0.4)
        if x >= right_threshold:
            ax.annotate(str(row["fixture"]), (x, y), xytext=(-3, 3),
                        textcoords="offset points", fontsize=6, ha="right")
        else:
            ax.annotate(str(row["fixture"]), (x, y), xytext=(3, 3),
                        textcoords="offset points", fontsize=6)

    ax.set_xscale("log")
    ax.set_xlabel("entity count (truth, log scale)")
    ax.set_ylabel("extraction cost (USD)")
    ax.set_title("cost vs. complexity, by source type and F1")

    # Replace matplotlib's default log-scale minor ticks (2×10¹, 3×10¹ …,
    # which overlap at this figure size) with plain integer labels.
    from matplotlib.ticker import FixedLocator, FixedFormatter, NullLocator
    ax.xaxis.set_major_locator(FixedLocator(list(_X_TICKS)))
    ax.xaxis.set_major_formatter(FixedFormatter([str(t) for t in _X_TICKS]))
    ax.xaxis.set_minor_locator(NullLocator())

    # Build a small legend (shape × source, colour swatch by F1 bucket).
    handles = []
    labels = []
    for src, marker in _SHAPE_BY_SOURCE.items():
        handles.append(plt.Line2D([], [], marker=marker, linestyle="none",
                                  color="black", markerfacecolor="white",
                                  markersize=6))
        labels.append(src)
    for _, _, colour, label in _F1_BUCKETS:
        handles.append(plt.Line2D([], [], marker="o", linestyle="none",
                                  color=colour, markersize=6))
        labels.append(f"F1 {label}")
    ax.legend(handles, labels, fontsize=6, loc="upper left",
              frameon=False, ncol=2)

    fig.savefig(out_path, format="pdf", bbox_inches="tight")
    plt.close(fig)
    return out_path
