"""
Synthetic loan portfolio generator for IFRS 9 staging experiment.

Produces data/test_portfolio.csv with 20 records designed to exercise
the full staging spectrum — clear Stage 1/2/3 and deliberately
ambiguous edge cases that require graduated reasoning.

Usage:
    python data/simulate_portfolio.py
    # → writes data/test_portfolio.csv
"""

from __future__ import annotations

import csv
from pathlib import Path

# ---------------------------------------------------------------------------
# Portfolio definition
# Each record maps directly to IFRS 9 staging signals.
# Fields:
#   loan_id              — unique identifier (TP001 … TP020)
#   dpd                  — days past due (0, 1–29, 30–89, 90+)
#   origination_rating   — internal rating at inception (AAA … CCC)
#   current_rating       — current internal rating
#   watch_list           — account on watch list (true/false)
#   impaired             — bank has recognised impairment (true/false)
#   restructured         — loan has been restructured (true/false)
#   sector               — industry sector
#   collateral_coverage  — collateral value / outstanding exposure (0.0–2.0+)
#   macro_signal         — forward-looking macro overlay (none/watch/elevated/severe)
#   loan_amount_myr_k    — facility amount in RM thousands
#   expected_stage       — human annotation for test validation (1/2/3)
#   case_note            — short description of the ambiguity / rationale
# ---------------------------------------------------------------------------

PORTFOLIO: list[dict] = [
    # ── Clear Stage 1 ────────────────────────────────────────────────────────
    {
        "loan_id": "TP001",
        "dpd": 0,
        "origination_rating": "AA",
        "current_rating": "AA",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "technology",
        "collateral_coverage": 1.8,
        "macro_signal": "none",
        "loan_amount_myr_k": 5000,
        "expected_stage": 1,
        "case_note": "Strong borrower, no signals, clear Stage 1.",
    },
    {
        "loan_id": "TP002",
        "dpd": 5,
        "origination_rating": "BBB",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "manufacturing",
        "collateral_coverage": 1.4,
        "macro_signal": "none",
        "loan_amount_myr_k": 3200,
        "expected_stage": 1,
        "case_note": "Minor DPD (5 days), stable rating, no flags.",
    },
    {
        "loan_id": "TP003",
        "dpd": 0,
        "origination_rating": "A",
        "current_rating": "A",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "retail",
        "collateral_coverage": 1.6,
        "macro_signal": "none",
        "loan_amount_myr_k": 1800,
        "expected_stage": 1,
        "case_note": "Pristine profile. Benchmark Stage 1 case.",
    },
    # ── Ambiguous Stage 1 / Stage 2 border ───────────────────────────────────
    {
        "loan_id": "TP004",
        "dpd": 29,
        "origination_rating": "BBB",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "commercial_real_estate",
        "collateral_coverage": 1.3,
        "macro_signal": "elevated",
        "loan_amount_myr_k": 8500,
        "expected_stage": 1,
        "case_note": (
            "29 DPD — below 30-day SICR presumption. No rating change. "
            "But sector macro (rising CRE vacancy) introduces elevated "
            "forward-looking risk. Stage 1 but flag for monitoring."
        ),
    },
    {
        "loan_id": "TP005",
        "dpd": 0,
        "origination_rating": "AAA",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "oil_and_gas",
        "collateral_coverage": 1.1,
        "macro_signal": "watch",
        "loan_amount_myr_k": 12000,
        "expected_stage": 2,
        "case_note": (
            "0 DPD but 4-notch rating migration (AAA → BBB). "
            "No watchlist. Is this SICR? Rating migration alone may "
            "qualify under the entity's staging policy."
        ),
    },
    {
        "loan_id": "TP006",
        "dpd": 0,
        "origination_rating": "A",
        "current_rating": "A",
        "watch_list": "true",
        "impaired": "false",
        "restructured": "false",
        "sector": "hospitality",
        "collateral_coverage": 1.0,
        "macro_signal": "watch",
        "loan_amount_myr_k": 4200,
        "expected_stage": 2,
        "case_note": (
            "Watch list entry with 0 DPD and stable rating. "
            "Watch listing is a qualitative SICR indicator. "
            "Strong collateral mitigates loss but not probability of default."
        ),
    },
    {
        "loan_id": "TP007",
        "dpd": 15,
        "origination_rating": "BBB",
        "current_rating": "BB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "commercial_real_estate",
        "collateral_coverage": 1.2,
        "macro_signal": "elevated",
        "loan_amount_myr_k": 6700,
        "expected_stage": 2,
        "case_note": (
            "15 DPD + 1-notch rating drop + elevated macro. "
            "Individual signals are borderline but the combination "
            "likely crosses SICR threshold."
        ),
    },
    # ── Clear Stage 2 ────────────────────────────────────────────────────────
    {
        "loan_id": "TP008",
        "dpd": 45,
        "origination_rating": "BB",
        "current_rating": "B",
        "watch_list": "true",
        "impaired": "false",
        "restructured": "false",
        "sector": "retail",
        "collateral_coverage": 0.9,
        "macro_signal": "elevated",
        "loan_amount_myr_k": 2100,
        "expected_stage": 2,
        "case_note": "45 DPD, rating drop, watchlist, under-collateralised. Clear Stage 2.",
    },
    {
        "loan_id": "TP009",
        "dpd": 60,
        "origination_rating": "BBB",
        "current_rating": "BB",
        "watch_list": "true",
        "impaired": "false",
        "restructured": "false",
        "sector": "manufacturing",
        "collateral_coverage": 1.05,
        "macro_signal": "watch",
        "loan_amount_myr_k": 9300,
        "expected_stage": 2,
        "case_note": "60 DPD. SICR confirmed. Not yet impaired.",
    },
    # ── Restructured — IFRS 9 SICR presumption ───────────────────────────────
    {
        "loan_id": "TP010",
        "dpd": 0,
        "origination_rating": "BB",
        "current_rating": "BB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "true",
        "sector": "hospitality",
        "collateral_coverage": 1.15,
        "macro_signal": "none",
        "loan_amount_myr_k": 3800,
        "expected_stage": 2,
        "case_note": (
            "Restructured loan with 0 DPD post-restructure. "
            "IFRS 9 creates a rebuttable presumption of SICR on restructured "
            "accounts regardless of current DPD."
        ),
    },
    {
        "loan_id": "TP011",
        "dpd": 0,
        "origination_rating": "A",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "true",
        "sector": "technology",
        "collateral_coverage": 1.5,
        "macro_signal": "none",
        "loan_amount_myr_k": 7200,
        "expected_stage": 2,
        "case_note": (
            "Strong collateral + minor rating move, but restructured. "
            "Borrower negotiated extended tenor. SICR presumption applies."
        ),
    },
    # ── Macro-driven SICR ────────────────────────────────────────────────────
    {
        "loan_id": "TP012",
        "dpd": 0,
        "origination_rating": "BBB",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "commercial_real_estate",
        "collateral_coverage": 1.25,
        "macro_signal": "severe",
        "loan_amount_myr_k": 15000,
        "expected_stage": 2,
        "case_note": (
            "0 DPD, stable rating. But severe macro overlay (CRE sector "
            "stress — vacancy >25%, cap rate compression). Forward-looking "
            "information drives SICR even without backward-looking DPD."
        ),
    },
    {
        "loan_id": "TP013",
        "dpd": 10,
        "origination_rating": "BB",
        "current_rating": "BB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "oil_and_gas",
        "collateral_coverage": 0.85,
        "macro_signal": "severe",
        "loan_amount_myr_k": 11000,
        "expected_stage": 2,
        "case_note": (
            "Oil & gas with severe macro (commodity price shock). "
            "Under-collateralised. 10 DPD alone is borderline but macro "
            "severity tips this to Stage 2."
        ),
    },
    # ── Ambiguous Stage 2 / Stage 3 border ───────────────────────────────────
    {
        "loan_id": "TP014",
        "dpd": 88,
        "origination_rating": "BB",
        "current_rating": "CCC",
        "watch_list": "true",
        "impaired": "false",
        "restructured": "false",
        "sector": "retail",
        "collateral_coverage": 0.75,
        "macro_signal": "elevated",
        "loan_amount_myr_k": 1600,
        "expected_stage": 3,
        "case_note": (
            "88 DPD — 2 days below the 90-day default presumption. "
            "CCC rating, watchlist, under-collateralised. "
            "Qualitative evidence strongly suggests credit impairment "
            "even though the 90-day trigger is not yet breached."
        ),
    },
    {
        "loan_id": "TP015",
        "dpd": 75,
        "origination_rating": "BBB",
        "current_rating": "B",
        "watch_list": "true",
        "impaired": "false",
        "restructured": "true",
        "sector": "hospitality",
        "collateral_coverage": 0.6,
        "macro_signal": "severe",
        "loan_amount_myr_k": 4500,
        "expected_stage": 3,
        "case_note": (
            "75 DPD + restructured + CCC-equivalent quality + severe macro. "
            "Multiple objective evidence of impairment points. "
            "Model should recognise Stage 3 despite sub-90 DPD."
        ),
    },
    # ── Clear Stage 3 ────────────────────────────────────────────────────────
    {
        "loan_id": "TP016",
        "dpd": 120,
        "origination_rating": "B",
        "current_rating": "CCC",
        "watch_list": "true",
        "impaired": "true",
        "restructured": "false",
        "sector": "manufacturing",
        "collateral_coverage": 0.5,
        "macro_signal": "severe",
        "loan_amount_myr_k": 6800,
        "expected_stage": 3,
        "case_note": "120 DPD, impaired, CCC. Unambiguous Stage 3.",
    },
    {
        "loan_id": "TP017",
        "dpd": 180,
        "origination_rating": "BB",
        "current_rating": "CCC",
        "watch_list": "true",
        "impaired": "true",
        "restructured": "true",
        "sector": "retail",
        "collateral_coverage": 0.35,
        "macro_signal": "severe",
        "loan_amount_myr_k": 2300,
        "expected_stage": 3,
        "case_note": "180 DPD, impaired, restructured. Benchmark Stage 3.",
    },
    {
        "loan_id": "TP018",
        "dpd": 95,
        "origination_rating": "BB",
        "current_rating": "B",
        "watch_list": "true",
        "impaired": "true",
        "restructured": "false",
        "sector": "oil_and_gas",
        "collateral_coverage": 0.45,
        "macro_signal": "severe",
        "loan_amount_myr_k": 18000,
        "expected_stage": 3,
        "case_note": "95 DPD + impaired. Default threshold crossed.",
    },
    # ── Low-risk with macro watch (Stage 1, monitoring note) ─────────────────
    {
        "loan_id": "TP019",
        "dpd": 0,
        "origination_rating": "A",
        "current_rating": "A",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "false",
        "sector": "technology",
        "collateral_coverage": 2.1,
        "macro_signal": "watch",
        "loan_amount_myr_k": 4100,
        "expected_stage": 1,
        "case_note": (
            "Strong borrower, over-collateralised. Macro signal is only "
            "'watch' (not elevated). Stage 1 with monitoring note on "
            "sector headwinds."
        ),
    },
    # ── Performing post-restructure (Stage 1 cure candidate) ─────────────────
    {
        "loan_id": "TP020",
        "dpd": 0,
        "origination_rating": "BBB",
        "current_rating": "BBB",
        "watch_list": "false",
        "impaired": "false",
        "restructured": "true",
        "sector": "manufacturing",
        "collateral_coverage": 1.45,
        "macro_signal": "none",
        "loan_amount_myr_k": 5600,
        "expected_stage": 2,
        "case_note": (
            "12-month cure period post-restructure. Rating restored to BBB. "
            "0 DPD. Under IFRS 9 a restructured account must demonstrate "
            "sustained performance before cure to Stage 1 is permitted. "
            "Remains Stage 2 until probation period satisfied."
        ),
    },
]

FIELDS = [
    "loan_id",
    "dpd",
    "origination_rating",
    "current_rating",
    "watch_list",
    "impaired",
    "restructured",
    "sector",
    "collateral_coverage",
    "macro_signal",
    "loan_amount_myr_k",
    "expected_stage",
    "case_note",
]


def simulate(output_path: Path | None = None) -> Path:
    """Write synthetic portfolio CSV and return the path."""
    if output_path is None:
        output_path = Path(__file__).parent / "test_portfolio.csv"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    with output_path.open("w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(PORTFOLIO)

    return output_path


if __name__ == "__main__":
    path = simulate()
    print(f"Wrote {len(PORTFOLIO)} records → {path}")
