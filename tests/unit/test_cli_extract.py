from pathlib import Path
from types import SimpleNamespace

from typer.testing import CliRunner

from diagex.cli import app
from diagex.config import Config


def test_extract_pid_fresh_is_forwarded_to_engine(
    tmp_path: Path, monkeypatch
) -> None:
    diagram = tmp_path / "drawing.pdf"
    diagram.write_bytes(b"test")
    captured: dict[str, object] = {}

    def fake_run_pid_extract(**kwargs: object) -> object:
        captured.update(kwargs)
        return SimpleNamespace(to_text=lambda: "done")

    monkeypatch.setattr("diagex.cli.load_config", Config)
    monkeypatch.setattr("diagex.extractors.symbol_detection.run_symbol_detection", fake_run_pid_extract)

    result = CliRunner().invoke(
        app,
        ["detect", str(diagram), "--fresh"],
    )

    assert result.exit_code == 0
    assert captured["fresh"] is True


def test_extract_pid_help_describes_fresh_option() -> None:
    result = CliRunner().invoke(app, ["detect", "--help"])
    normalised_help = " ".join(result.stdout.replace("│", " ").split())

    assert result.exit_code == 0
    assert "--fresh" in result.stdout
    assert "Detect symbols" in normalised_help
