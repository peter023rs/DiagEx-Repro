"""Re-render Phase-1 tables, figures, and report.md from an existing
``results.csv`` — used after ``rerun_one_query.py`` patches a row, so
downstream artefacts (table2.tex, fig2.pdf, report.md) reflect the new value
without re-invoking the API.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import typer
from rich.console import Console

_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))
if str(_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(_ROOT / "src"))

from eval import aggregate as agg  # noqa: E402
from eval import latex_tables, report_md  # noqa: E402

console = Console()
app = typer.Typer(no_args_is_help=False, add_completion=False)


@app.command()
def main(
    out_dir: Path = typer.Option(
        Path("out/diagex-phase1"), "--out", help="Run output dir.",
    ),
) -> None:
    csv_path = out_dir / "results.csv"
    if not csv_path.exists():
        raise typer.Exit(f"missing {csv_path}")
    invocation_path = out_dir / "invocation.txt"
    invocation = "(rerendered)"
    run_id = "rerendered"
    if invocation_path.exists():
        try:
            inv = json.loads(invocation_path.read_text(encoding="utf-8"))
            invocation = " ".join(inv.get("argv") or [])
            run_id = str(inv.get("run_id") or run_id)
        except json.JSONDecodeError:
            pass

    df = pd.read_csv(csv_path)
    console.print(f"[dim]loaded {len(df)} rows from {csv_path}[/dim]")

    wide = agg.phase1_per_fixture_wide(df)
    per_fixture = agg.phase2_per_fixture(df)
    latex_tables.write_tables(
        out_dir / "tables", table2_wide=wide, table3=per_fixture,
    )
    console.print(f"[green]wrote tables → {out_dir/'tables'}[/green]")

    try:
        from eval.figures.fig2_cost_accuracy import render_figure2
        from eval.figures.fig3_heterogeneity import render_figure3
        render_figure2(agg.figure2_points(df), out_dir / "figures" / "fig2.pdf")
        render_figure3(out_dir / "figures" / "fig3_heterogeneity.pdf")
        console.print(f"[green]wrote figures → {out_dir/'figures'}[/green]")
    except Exception as exc:  # noqa: BLE001
        console.print(f"[yellow]figures skipped: {exc}[/yellow]")

    prev_csv = out_dir / "results.prev.csv"
    df_prev = pd.read_csv(prev_csv) if prev_csv.exists() else None
    report_md.write_report(
        out_dir / "report.md",
        df_curr=df, df_prev=df_prev,
        run_id=run_id, invocation=invocation,
    )
    console.print(f"[green]wrote {out_dir/'report.md'}[/green]")


if __name__ == "__main__":
    app()
