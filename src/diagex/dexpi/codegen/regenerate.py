"""Regenerate ``src/diagex/dexpi/_generated/`` from the vendored DEXPI 2.0 spec.

Usage::

    pip install -e '.[codegen]'
    python -m diagex.dexpi.codegen.regenerate

Requires Python 3.12+ (for ``dexpi.specificator``). The generated runtime code
remains importable on Python 3.11+.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from dexpi.specificator.dsl_reader import DslReader

from diagex.dexpi.codegen.pydantic_emit import emit_all

HERE = Path(__file__).resolve().parent
VENDORED_MODEL = HERE / "vendored" / "model"
DST_DIR = HERE.parent / "_generated"


def main() -> int:
    if not VENDORED_MODEL.exists():
        print(f"error: vendored model dir missing: {VENDORED_MODEL}", file=sys.stderr)
        return 2

    print(f"reading DEXPI DSL from {VENDORED_MODEL}")
    reader = DslReader(VENDORED_MODEL)
    if reader.messages:
        print(f"specificator reported {len(reader.messages)} messages:", file=sys.stderr)
        for m in reader.messages:
            print(f"  {m}", file=sys.stderr)

    print(f"emitting pydantic source to {DST_DIR}")
    written = emit_all(reader, DST_DIR)
    for name, path in written.items():
        print(f"  wrote {name}: {path.stat().st_size} bytes")

    # Format with ruff if available
    try:
        subprocess.run(["ruff", "format", str(DST_DIR)], check=False)
        subprocess.run(["ruff", "check", "--fix", str(DST_DIR), "--quiet"], check=False)
    except FileNotFoundError:
        print("(ruff not on PATH — generated files left unformatted)")

    print("done.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
