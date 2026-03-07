"""
IFRS 9 Credit Classification Experiment — End-to-End Runner.

Steps:
  1. Simulate portfolio → data/test_portfolio.csv  (if not already present)
  2. Load records from CSV
  3. Classify each record (Claude API if ANTHROPIC_API_KEY set, else rule fallback)
  4. Print a formatted results table to stdout
  5. Write results → output/credit_classification_results.csv

Usage:
    source .venv/bin/activate
    python scripts/run_credit_experiment.py

    # With Claude API:
    ANTHROPIC_API_KEY=sk-ant-... python scripts/run_credit_experiment.py

    # Use existing portfolio CSV:
    python scripts/run_credit_experiment.py --portfolio data/test_portfolio.csv

    # Suppress reasoning column:
    python scripts/run_credit_experiment.py --no-reasoning
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
from pathlib import Path

# Ensure project root is on the import path when run as a script
sys.path.insert(0, str(Path(__file__).parent.parent))

from data.simulate_portfolio import simulate
from src.tools.ifrs9_classifier import classify_portfolio

# Optional rich for pretty output
try:
    from rich.console import Console
    from rich.table import Table
    from rich import print as rprint

    _RICH = True
    console = Console()
except ImportError:
    _RICH = False
    console = None  # type: ignore[assignment]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_STAGE_COLOUR = {1: "green", 2: "yellow", 3: "red"}
_CONF_COLOUR = {"High": "green", "Medium": "yellow", "Low": "red"}


def _load_portfolio(csv_path: Path) -> list[dict]:
    with csv_path.open(encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def _write_results(decisions: list, source_rows: list[dict], output_path: Path) -> None:
    """Merge input fields + decision fields → output CSV."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    source_by_id = {r["loan_id"]: r for r in source_rows}

    fieldnames = [
        "loan_id",
        "sector",
        "dpd",
        "origination_rating",
        "current_rating",
        "watch_list",
        "restructured",
        "macro_signal",
        "loan_amount_myr_k",
        "expected_stage",
        "stage",
        "confidence",
        "monitoring_flag",
        "key_indicators",
        "reasoning",
        "case_note",
    ]

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for d in decisions:
            src = source_by_id.get(d.loan_id, {})
            row = {
                "loan_id": d.loan_id,
                "sector": src.get("sector", ""),
                "dpd": src.get("dpd", ""),
                "origination_rating": src.get("origination_rating", ""),
                "current_rating": src.get("current_rating", ""),
                "watch_list": src.get("watch_list", ""),
                "restructured": src.get("restructured", ""),
                "macro_signal": src.get("macro_signal", ""),
                "loan_amount_myr_k": src.get("loan_amount_myr_k", ""),
                "expected_stage": src.get("expected_stage", ""),
                "stage": d.stage,
                "confidence": d.confidence,
                "monitoring_flag": d.monitoring_flag,
                "key_indicators": " | ".join(d.key_indicators),
                "reasoning": d.reasoning,
                "case_note": src.get("case_note", ""),
            }
            writer.writerow(row)


def _print_table_rich(decisions: list, source_rows: list[dict], show_reasoning: bool) -> None:
    source_by_id = {r["loan_id"]: r for r in source_rows}

    table = Table(
        title="IFRS 9 Staging Results",
        show_header=True,
        header_style="bold cyan",
        show_lines=True,
    )
    table.add_column("Loan ID", style="bold")
    table.add_column("Sector", max_width=18)
    table.add_column("DPD", justify="right")
    table.add_column("Rating\nOrig→Curr", justify="center")
    table.add_column("Macro", justify="center")
    table.add_column("Exp.", justify="center")
    table.add_column("Stage", justify="center")
    table.add_column("Conf.", justify="center")
    table.add_column("Mon.", justify="center")
    if show_reasoning:
        table.add_column("Reasoning", max_width=55)

    correct = 0
    for d in decisions:
        src = source_by_id.get(d.loan_id, {})
        expected = int(src.get("expected_stage", 0))
        match = "✓" if expected == d.stage else "✗"
        if expected == d.stage:
            correct += 1

        stage_str = f"[{_STAGE_COLOUR[d.stage]}]Stage {d.stage}[/]"
        conf_str = f"[{_CONF_COLOUR[d.confidence]}]{d.confidence}[/]"
        exp_str = f"[{'green' if expected == d.stage else 'red'}]{expected} {match}[/]"
        mon_str = "[yellow]●[/]" if d.monitoring_flag else "·"

        rating_str = f"{src.get('origination_rating','?')}→{src.get('current_rating','?')}"

        row: list = [
            d.loan_id,
            src.get("sector", ""),
            str(src.get("dpd", "")),
            rating_str,
            src.get("macro_signal", ""),
            exp_str,
            stage_str,
            conf_str,
            mon_str,
        ]
        if show_reasoning:
            row.append(d.reasoning[:200] + ("…" if len(d.reasoning) > 200 else ""))

        table.add_row(*row)

    console.print(table)
    console.print(
        f"\n[bold]Accuracy vs expected_stage:[/] {correct}/{len(decisions)} "
        f"= [{'green' if correct == len(decisions) else 'yellow'}]"
        f"{correct/len(decisions)*100:.0f}%[/]\n"
    )


def _print_table_plain(decisions: list, source_rows: list[dict], show_reasoning: bool) -> None:
    source_by_id = {r["loan_id"]: r for r in source_rows}
    header = f"{'ID':<8} {'DPD':>4} {'Rating':<10} {'Macro':<10} {'Exp':>4} {'Stage':>5} {'Conf':<8}"
    print(header)
    print("-" * len(header))

    correct = 0
    for d in decisions:
        src = source_by_id.get(d.loan_id, {})
        expected = int(src.get("expected_stage", 0))
        if expected == d.stage:
            correct += 1
        match = "✓" if expected == d.stage else "✗"
        rating = f"{src.get('origination_rating','?')}→{src.get('current_rating','?')}"
        print(
            f"{d.loan_id:<8} {src.get('dpd',''):>4} {rating:<10} "
            f"{src.get('macro_signal',''):<10} {expected:>4}{match} "
            f"{d.stage:>5} {d.confidence:<8}"
        )
        if show_reasoning:
            print(f"  ↳ {d.reasoning[:140]}")

    print(f"\nAccuracy: {correct}/{len(decisions)} = {correct/len(decisions)*100:.0f}%")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run IFRS 9 credit classification experiment"
    )
    parser.add_argument(
        "--portfolio",
        type=Path,
        default=None,
        help="Path to portfolio CSV (default: simulate fresh data/test_portfolio.csv)",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("output/credit_classification_results.csv"),
        help="Output CSV path",
    )
    parser.add_argument(
        "--no-reasoning",
        action="store_true",
        help="Suppress reasoning column in table output",
    )
    parser.add_argument(
        "--api-key",
        default=None,
        help="Anthropic API key (overrides ANTHROPIC_API_KEY env var)",
    )
    args = parser.parse_args()

    # Step 1 — Portfolio
    if args.portfolio and args.portfolio.exists():
        portfolio_path = args.portfolio
        print(f"Loading existing portfolio: {portfolio_path}")
    else:
        portfolio_path = simulate()
        print(f"Simulated {portfolio_path} ({portfolio_path.stat().st_size} bytes)")

    rows = _load_portfolio(portfolio_path)
    print(f"Ingested {len(rows)} valid record(s) from {portfolio_path}\n")

    # Step 2 — Classify
    import os
    api_key = args.api_key or os.getenv("ANTHROPIC_API_KEY", "")
    mode = "Claude API" if api_key else "rule-based fallback (no API key)"
    print(f"Classifying {len(rows)} record(s) via {mode}...")

    t0 = time.time()
    decisions = classify_portfolio(rows, api_key=api_key or None)
    elapsed = time.time() - t0
    print(f"Done in {elapsed:.1f}s\n")

    # Step 3 — Display
    show_reasoning = not args.no_reasoning
    if _RICH:
        _print_table_rich(decisions, rows, show_reasoning)
    else:
        _print_table_plain(decisions, rows, show_reasoning)

    # Step 4 — Save
    _write_results(decisions, rows, args.output)
    print(f"Results written → {args.output}")

    # Step 5 — JSON summary (for debugging)
    summary_path = args.output.with_suffix(".json")
    with summary_path.open("w", encoding="utf-8") as fh:
        json.dump(
            [d.model_dump() for d in decisions],
            fh,
            indent=2,
        )
    print(f"JSON summary   → {summary_path}")


if __name__ == "__main__":
    main()
