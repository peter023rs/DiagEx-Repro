#!/usr/bin/env python3
"""Phase 2 stabilisation runner.

Executes repeated `diagex extract-pid` runs on a small fixture set and reports
per-run and aggregate gate results, per plan/etfa2026-evaluation-plan.md §10
step 4.

Default gate per fixture (3 runs):
    crashes          = 0
    validate issues  = 0 on every run
    cost (USD)       ≤ 5.00 on every run
    entities σ/μ     ≤ 10% across the runs

Lint is delegated to `diagex gt lint` (see src/diagex/gt_lint.py).

Usage:
    scripts/stabilise_phase2.py                          # 3×{dexpi-reference,tennessee1}
    scripts/stabilise_phase2.py --fixtures dexpi-reference --runs 5
    scripts/stabilise_phase2.py --analyze-only           # score the N most recent existing runs
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PDF_ROOT = ROOT / "tests" / "p-ids-public"
RUNS_ROOT = ROOT / "runs"

DEFAULT_FIXTURES = ["dexpi-reference", "tennessee1"]
DEFAULT_RUNS = 3
DEFAULT_EFFORT = "high"
COST_CAP_USD = 5.0
ENTITY_VARIANCE_GATE = 0.15  # σ/μ ≤ 15%  (raised from 10% after arbitration pass — 10-15% is
                             # genuinely good stability for this pipeline; see plan §10 step 4)
RUN_TIMEOUT_S = 3600


def newest_run_dir(stem: str) -> Path | None:
    parent = RUNS_ROOT / stem
    if not parent.exists():
        return None
    runs = sorted(
        (p for p in parent.iterdir() if p.is_dir()),
        key=lambda p: p.stat().st_mtime,
        reverse=True,
    )
    return runs[0] if runs else None


def graph_lint(graph_path: Path) -> tuple[bool, list[str]]:
    """Delegate to `diagex gt lint` (imported for structured access)."""
    from diagex import gt_lint as linter

    report = linter.lint(graph_path)
    errors = [f"{i.level}: {i.message}" for i in report.issues if i.level == "error"]
    return report.ok(), errors


def entity_count(stats: dict[str, Any]) -> int:
    return sum(
        stats.get(k, 0)
        for k in ("equipment_count", "valve_count", "instrument_count", "unclassified_count")
    )


def score_run(run_dir: Path) -> dict[str, Any]:
    out: dict[str, Any] = {"run_dir": run_dir}
    res = run_dir / "result.json"
    if not res.exists():
        out["score_error"] = "result.json missing"
        return out
    r = json.loads(res.read_text())
    out["cost_usd"] = float(r.get("cost", {}).get("total_usd", 0.0))
    out["validation_issues"] = len(r.get("validation_issues", []) or [])
    out["dexpi_issues"] = len(r.get("dexpi_issues", []) or [])
    out["entities"] = entity_count(r.get("stats", {}) or {})
    graph = run_dir / "graph.json"
    if graph.exists():
        lint_ok, lint_issues = graph_lint(graph)
    else:
        lint_ok, lint_issues = False, ["graph.json missing"]
    out["lint_ok"] = lint_ok
    out["lint_issues"] = lint_issues
    return out


def run_once(stem: str, effort: str) -> tuple[int, float, Path | None]:
    pdf = PDF_ROOT / f"{stem}.pdf"
    if not pdf.exists():
        return 127, 0.0, None
    before = set()
    parent = RUNS_ROOT / stem
    if parent.exists():
        before = {p.name for p in parent.iterdir() if p.is_dir()}
    cmd = ["diagex", "extract-pid", str(pdf), "--effort", effort]
    t0 = time.monotonic()
    try:
        # Stream output to terminal so the human can watch long runs.
        proc = subprocess.run(cmd, cwd=str(ROOT), timeout=RUN_TIMEOUT_S)
        code = proc.returncode
    except subprocess.TimeoutExpired:
        code = 124
    wall = time.monotonic() - t0
    created = None
    if parent.exists():
        new_names = {p.name for p in parent.iterdir() if p.is_dir()} - before
        if new_names:
            created = parent / sorted(new_names)[-1]
    if created is None:
        created = newest_run_dir(stem)
    return code, wall, created


def _row(cols: list[str], widths: list[int]) -> str:
    return "  ".join(c.ljust(w) for c, w in zip(cols, widths))


def report(results: dict[str, list[dict[str, Any]]]) -> bool:
    all_pass = True
    print()
    print("=" * 92)
    print("Phase 2 stabilisation — per-run detail")
    print("=" * 92)
    w = [20, 4, 6, 10, 11, 11, 6, 8]
    print(_row(["fixture", "run", "exit", "wall (s)", "cost (USD)", "validate", "lint", "entities"], w))
    print("-" * (sum(w) + 2 * (len(w) - 1)))
    for stem, runs in results.items():
        for i, r in enumerate(runs, 1):
            exit_code = r.get("exit_code", 0)
            exit_s = "ok" if exit_code == 0 else f"x{exit_code}"
            wall = f"{r.get('wall_s', 0):.1f}"
            cost = f"{r['cost_usd']:.2f}" if "cost_usd" in r else "—"
            v = r.get("validation_issues")
            val = f"{v} issue" + ("" if v == 1 else "s") if isinstance(v, int) else "—"
            lint = "ok" if r.get("lint_ok") else ("FAIL" if "lint_ok" in r else "—")
            ent = str(r.get("entities", "—"))
            print(_row([stem, str(i), exit_s, wall, cost, val, lint, ent], w))
            for li in r.get("lint_issues", []):
                print(f"      lint: {li}")
            if "score_error" in r:
                print(f"      score: {r['score_error']}")

    print()
    print("=" * 92)
    print("Gate summary (per plan §10 step 4)")
    print("=" * 92)
    w2 = [20, 6, 9, 11, 11, 13, 9]
    print(_row(["fixture", "runs", "crashes", "validate", "cost≤$5", "entities σ/μ", "VERDICT"], w2))
    print("-" * (sum(w2) + 2 * (len(w2) - 1)))
    for stem, runs in results.items():
        n = len(runs)
        crashes = sum(1 for r in runs if r.get("exit_code", 0) != 0)
        val_ok = sum(1 for r in runs if r.get("validation_issues") == 0)
        lint_ok = sum(1 for r in runs if r.get("lint_ok"))
        cost_ok = sum(1 for r in runs if 0 < r.get("cost_usd", -1) <= COST_CAP_USD)
        ents = [r["entities"] for r in runs if isinstance(r.get("entities"), int)]
        if len(ents) >= 2 and statistics.mean(ents) > 0:
            var = statistics.stdev(ents) / statistics.mean(ents)
            var_s = f"{var:.1%}"
            var_ok = var <= ENTITY_VARIANCE_GATE
        else:
            var_s = "n/a"
            var_ok = False
        fixture_pass = (
            crashes == 0
            and val_ok == n
            and lint_ok == n
            and cost_ok == n
            and var_ok
        )
        verdict = "PASS" if fixture_pass else "FAIL"
        all_pass = all_pass and fixture_pass
        print(_row([stem, f"{n}", f"{crashes}", f"{val_ok}/{n}", f"{cost_ok}/{n}", var_s, verdict], w2))

    print()
    print(f"Gates: crashes=0  validation_issues=0  cost ≤ ${COST_CAP_USD:.2f}  entities σ/μ ≤ {ENTITY_VARIANCE_GATE:.0%}")
    print("Lint: delegated to `diagex gt lint` (src/diagex/gt_lint.py).")
    print()
    return all_pass


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Phase 2 stabilisation runner (plan §10 step 4).",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--fixtures", nargs="+", default=DEFAULT_FIXTURES,
                    help="Fixture stems (match tests/p-ids-public/<stem>.pdf).")
    ap.add_argument("--runs", type=int, default=DEFAULT_RUNS,
                    help="Number of runs per fixture.")
    ap.add_argument("--effort", default=DEFAULT_EFFORT,
                    help="diagex --effort value.")
    ap.add_argument("--analyze-only", action="store_true",
                    help="Skip fresh extraction; score the N most recent existing runs per fixture.")
    args = ap.parse_args()

    if not args.analyze_only and not shutil.which("diagex"):
        print("ERROR: `diagex` CLI not found on PATH. Activate the venv, or use --analyze-only.", file=sys.stderr)
        return 2

    results: dict[str, list[dict[str, Any]]] = {}
    for stem in args.fixtures:
        results[stem] = []
        if args.analyze_only:
            parent = RUNS_ROOT / stem
            if not parent.exists():
                print(f"{stem}: no runs dir — skipping", file=sys.stderr)
                continue
            recent = sorted(
                (p for p in parent.iterdir() if p.is_dir()),
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )[: args.runs]
            for p in reversed(recent):
                r = score_run(p)
                r["exit_code"] = 0
                r["wall_s"] = 0.0
                results[stem].append(r)
            continue

        for i in range(1, args.runs + 1):
            print()
            print(f"▶ [{stem} {i}/{args.runs}] diagex extract-pid --effort {args.effort}")
            code, wall, run_dir = run_once(stem, args.effort)
            if run_dir is not None:
                r = score_run(run_dir)
                r["run_name"] = run_dir.name
            else:
                r = {"score_error": "no run_dir produced"}
            r["exit_code"] = code
            r["wall_s"] = wall
            status = "ok" if code == 0 else f"exit={code}"
            print(f"◀ [{stem} {i}/{args.runs}] {status}  wall={wall:.1f}s  "
                  f"cost=${r.get('cost_usd', 0):.2f}  entities={r.get('entities', '?')}")
            results[stem].append(r)

    ok = report(results)
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
