#!/usr/bin/env python3
"""Measure bootstrap → final retention % per fixture.

For each partial-truth fixture, regenerates the machine bootstrap from
`runs/<stem>/<latest>/graph.json` (pure function — deterministic given the
run), then diffs against the current `eval/datasets/<stem>/annotations.truth.jsonl`.
The numbers are the direct answer to the "graded your own homework"
reviewer objection (plan § 4.2, § V retention reporting).

Identity match = (kind, label) case-insensitive after whitespace trim.
`edited` = retained entity whose bbox moved > `--bbox-tol` (default 5 px)
on any side.

Usage:
    scripts/measure_retention.py                          # print table to stdout
    scripts/measure_retention.py --json out.json          # also write JSON
    scripts/measure_retention.py --bbox-tol 10
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATASETS = ROOT / "eval" / "datasets"

DEFAULT_STEMS = [
    "butane2", "grit-washer1",
    "open100-1", "open100-2", "open100-3", "open100-4",
    "two-tanks",
]


def regenerate_bootstrap(tmp: Path, stems: list[str]) -> None:
    """Run the bootstrap script with DATASETS redirected to ``tmp``."""
    spec = importlib.util.spec_from_file_location(
        "bootstrap_annotations", ROOT / "scripts" / "bootstrap_annotations.py"
    )
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)  # type: ignore[union-attr]
    mod.DATASETS = tmp
    for s in stems:
        (tmp / s).mkdir(parents=True, exist_ok=True)
    orig = sys.argv[:]
    sys.argv = ["bootstrap_annotations.py", "--force", "--stems", *stems]
    try:
        # Suppress the verbose per-fixture print from the bootstrap script.
        from contextlib import redirect_stdout
        import io
        with redirect_stdout(io.StringIO()):
            mod.main()
    finally:
        sys.argv = orig


def load(p: Path) -> list[dict]:
    if not p.is_file():
        return []
    return [json.loads(l) for l in p.read_text().splitlines() if l.strip()]


def identity(row: dict) -> tuple[str, str]:
    return (row["kind"], (row.get("label") or "").strip().upper())


def measure(stems: list[str], bbox_tol: int) -> dict:
    import tempfile

    with tempfile.TemporaryDirectory(prefix="retention-") as td:
        tmp = Path(td)
        regenerate_bootstrap(tmp, stems)

        per_fixture: dict[str, dict] = {}
        for s in stems:
            boot = load(tmp / s / "annotations.truth.jsonl")
            final = load(DATASETS / s / "annotations.truth.jsonl")
            b_by = {identity(r): r for r in boot}
            f_by = {identity(r): r for r in final}
            retained_keys = set(b_by) & set(f_by)
            deleted = set(b_by) - set(f_by)
            added = set(f_by) - set(b_by)
            edited = 0
            for k in retained_keys:
                b = b_by[k]["bbox_global"]
                f = f_by[k]["bbox_global"]
                if any(abs(b[d] - f[d]) > bbox_tol for d in ("x", "y", "w", "h")):
                    edited += 1
            unchanged = len(retained_keys) - edited
            per_fixture[s] = {
                "bootstrap": len(boot),
                "final": len(final),
                "retained": len(retained_keys),
                "bbox_unchanged": unchanged,
                "bbox_edited": edited,
                "added": len(added),
                "deleted": len(deleted),
                "retention_pct": (
                    100.0 * len(retained_keys) / len(boot) if boot else 0.0
                ),
            }

    totals = {
        "bootstrap": sum(r["bootstrap"] for r in per_fixture.values()),
        "final": sum(r["final"] for r in per_fixture.values()),
        "retained": sum(r["retained"] for r in per_fixture.values()),
        "bbox_unchanged": sum(r["bbox_unchanged"] for r in per_fixture.values()),
        "bbox_edited": sum(r["bbox_edited"] for r in per_fixture.values()),
        "added": sum(r["added"] for r in per_fixture.values()),
        "deleted": sum(r["deleted"] for r in per_fixture.values()),
    }
    totals["retention_pct"] = (
        100.0 * totals["retained"] / totals["bootstrap"] if totals["bootstrap"] else 0.0
    )
    return {"per_fixture": per_fixture, "totals": totals, "bbox_tol_px": bbox_tol}


def print_table(report: dict) -> None:
    header = ("fixture", "boot", "final", "retain", "edited", "added", "deleted", "ret%")
    print(f"{header[0]:<14} {header[1]:>5} {header[2]:>6} {header[3]:>7} "
          f"{header[4]:>7} {header[5]:>6} {header[6]:>8}  {header[7]:>6}")
    for stem, r in sorted(report["per_fixture"].items()):
        print(f"{stem:<14} {r['bootstrap']:>5} {r['final']:>6} {r['retained']:>7} "
              f"{r['bbox_edited']:>7} {r['added']:>6} {r['deleted']:>8}  "
              f"{r['retention_pct']:>5.1f}%")
    t = report["totals"]
    print("-" * 72)
    print(f"{'TOTAL':<14} {t['bootstrap']:>5} {t['final']:>6} {t['retained']:>7} "
          f"{t['bbox_edited']:>7} {t['added']:>6} {t['deleted']:>8}  "
          f"{t['retention_pct']:>5.1f}%")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--stems", nargs="*", default=DEFAULT_STEMS)
    ap.add_argument("--bbox-tol", type=int, default=5,
                    help="Pixel threshold for calling a retained entity 'edited' (default 5)")
    ap.add_argument("--json", type=Path, default=None,
                    help="Also write the report as JSON")
    args = ap.parse_args()

    report = measure(args.stems, args.bbox_tol)
    print_table(report)
    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps(report, indent=2))
        print(f"\nWrote {args.json}", file=sys.stderr)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
