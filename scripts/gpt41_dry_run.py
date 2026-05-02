"""Pre-flight budget preview for the GPT-4.1 single-shot Phase 1 leg.

Renders the page-1 overview for every fixture in the manifest, computes
the OpenAI image-token estimate (detail=high tile math), and prints a
per-fixture and total-budget table. No API calls — safe to run repeatedly.

Usage:
    python scripts/gpt41_dry_run.py
    python scripts/gpt41_dry_run.py --only dexpi-reference,butane1
    python scripts/gpt41_dry_run.py --max-image-dim 1536    # cheaper preview
"""

from __future__ import annotations

import sys
from pathlib import Path

import typer
from rich.console import Console
from rich.table import Table

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval._loader import load_manifest  # noqa: E402
from eval.gpt_singleshot import (  # noqa: E402
    GPT41_INPUT_PER_MTOK,
    GPT41_OUTPUT_PER_MTOK,
    estimate_image_tokens,
    _render_overview_b64,
)

app = typer.Typer(add_completion=False, help=__doc__)


@app.command()
def main(
    fixtures: Path = typer.Option(
        Path("eval/datasets"), "--fixtures",
        help="Dataset root containing manifest.yaml.",
    ),
    only: str = typer.Option("", "--only", help="Comma-separated fixture stems."),
    queries_per_fixture: int = typer.Option(
        4, "--queries-per-fixture",
        help="Phase 1 queries per fixture (plan §4.1: 4).",
    ),
    max_image_dim: int = typer.Option(
        2048, "--max-image-dim",
        help="Render max-dim (matches gpt_singleshot default).",
    ),
    text_in_per_query: int = typer.Option(
        250, "--text-in-per-query",
        help="System+question token estimate.",
    ),
    output_per_query: int = typer.Option(
        80, "--output-per-query",
        help="Expected answer length in tokens.",
    ),
) -> None:
    console = Console()
    manifest = load_manifest(fixtures / "manifest.yaml")
    pdf_root = (
        manifest.pdf_root if manifest.pdf_root.is_absolute()
        else fixtures.parent.parent / manifest.pdf_root
    )

    only_set = {s.strip() for s in only.split(",") if s.strip()}
    selected = [
        f for f in manifest.fixtures
        if not only_set or f.stem in only_set
    ]

    table = Table(title=f"GPT-4.1 single-shot dry-run "
                        f"({queries_per_fixture} queries/fixture, "
                        f"max_image_dim={max_image_dim})")
    table.add_column("fixture")
    table.add_column("rendered px", justify="right")
    table.add_column("img tok", justify="right")
    table.add_column("in/query", justify="right")
    table.add_column("$/query", justify="right")
    table.add_column("$/fixture", justify="right")

    grand_cost = 0.0
    grand_in = 0
    grand_img = 0
    for spec in selected:
        pdf_path = pdf_root / spec.pdf
        if not pdf_path.exists():
            console.print(f"[red]missing PDF: {pdf_path}[/red]")
            continue
        _b64, (w, h) = _render_overview_b64(pdf_path, max_dim=max_image_dim)
        img_tok = estimate_image_tokens(w, h)
        in_per_q = img_tok + text_in_per_query
        cost_per_q = (
            in_per_q * GPT41_INPUT_PER_MTOK / 1_000_000
            + output_per_query * GPT41_OUTPUT_PER_MTOK / 1_000_000
        )
        cost_fix = cost_per_q * queries_per_fixture
        grand_cost += cost_fix
        grand_in += in_per_q * queries_per_fixture
        grand_img += img_tok * queries_per_fixture
        table.add_row(
            spec.stem,
            f"{w}×{h}",
            f"{img_tok}",
            f"{in_per_q:,}",
            f"${cost_per_q:.4f}",
            f"${cost_fix:.4f}",
        )

    table.add_section()
    table.add_row(
        f"TOTAL ({len(selected)} fixtures)",
        "",
        f"{grand_img:,}",
        f"{grand_in:,}",
        "",
        f"[bold]${grand_cost:.4f}[/bold]",
    )
    console.print(table)
    console.print(
        f"[dim]Pricing: input ${GPT41_INPUT_PER_MTOK}/Mtok, "
        f"output ${GPT41_OUTPUT_PER_MTOK}/Mtok. Estimate excludes any "
        f"prompt-cache discount.[/dim]"
    )


if __name__ == "__main__":
    app()
