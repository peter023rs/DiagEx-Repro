"""Local symbol detection workbench and batch CLI."""

from pathlib import Path
from typing import Annotated

import typer
from rich.console import Console

from diagex.config import load_config

app = typer.Typer(name="diagex", help="P&ID legend and symbol detection.", no_args_is_help=True)
console = Console()


@app.command("detect")
def detect(
    diagram: Annotated[Path, typer.Argument(exists=True, readable=True)],
    out_dir: Annotated[Path | None, typer.Option("--out-dir")] = None,
    fresh: bool = typer.Option(False, "--fresh"),
    effort: str = typer.Option("medium", "--effort"),
    no_legend: bool = typer.Option(False, "--no-legend"),
    symbol_standard: str = typer.Option("isa-5.1", "--symbol-standard", help="isa-5.1, iso-10628, sama, or none."),
):
    """Detect symbols and save immutable machine artifacts."""
    from diagex.extractors.symbol_detection import run_symbol_detection

    if effort not in {"low", "medium", "high", "xhigh"}:
        raise typer.BadParameter("effort must be low, medium, high, or xhigh")
    if symbol_standard not in {"isa-5.1", "iso-10628", "sama", "none"}:
        raise typer.BadParameter("symbol-standard must be isa-5.1, iso-10628, sama, or none")
    config = load_config()
    if out_dir is not None:
        config.runs_dir = out_dir
    try:
        result = run_symbol_detection(
            diagram=diagram,
            symbol_standard=symbol_standard,
            legend_path=None,
            legend_pages=None,
            legend_region=None,
            no_legend=no_legend,
            legend_key=None,
            effort=effort,
            config=config,
            persist=True,
            fresh=fresh,
            console=console,
        )
    except Exception as exc:
        console.print(f"[red]Detection failed:[/red] {exc}")
        raise typer.Exit(1) from exc
    console.print(result.to_text())


@app.command()
def version():
    from diagex import __version__

    console.print(__version__)


@app.command("web")
def web_workbench(
    host: str = typer.Option("127.0.0.1", "--host", help="Local server bind address."),
    port: int = typer.Option(
        8765,
        "--port",
        min=0,
        max=65535,
        help="Local server port; 0 selects a free port.",
    ),
    no_open: bool = typer.Option(
        False,
        "--no-open",
        help="Do not open the browser automatically.",
    ),
) -> None:
    """Configure, detect, and view P&ID symbols in a local browser."""
    from diagex.web.server import Workbench, serve_workbench

    cfg = load_config()
    workbench = Workbench(cfg)
    if host not in {"127.0.0.1", "localhost", "::1"}:
        console.print(
            "[yellow]warning:[/yellow] the workbench has no authentication or TLS; "
            "API keys entered in a remotely accessed page would travel unencrypted"
        )
    console.print(
        f"runs: {Path(cfg.runs_dir).expanduser().resolve()}   "
        "credentials: memory only   (Ctrl+C stops safely)"
    )
    serve_workbench(
        workbench,
        host=host,
        port=port,
        open_browser=not no_open,
        on_ready=lambda url: console.print(f"workbench: [cyan]{url}[/cyan]"),
    )


if __name__ == "__main__":
    app()
