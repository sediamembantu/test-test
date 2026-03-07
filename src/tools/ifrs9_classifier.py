"""
IFRS 9 Staging Classifier — Credit Risk Experiment.

Calls Claude API once per loan record and returns a structured
staging decision with written reasoning.

Staging logic encoded in the system prompt:
  Stage 1 — No significant increase in credit risk (SICR) since origination.
             12-month ECL. DPD < 30, stable rating, no watchlist, benign macro.
  Stage 2 — SICR since origination but not yet credit-impaired.
             Lifetime ECL. DPD 30–89, material rating migration, watchlist,
             restructuring, or adverse forward-looking macro signals.
  Stage 3 — Credit-impaired (objective evidence of impairment).
             Lifetime ECL. DPD ≥ 90, bank-recognised impairment, or strong
             qualitative evidence of default (multiple concurrent triggers).

This module is a standalone tool: input → output, no side effects.
No API key → deterministic rule-based fallback is returned.
"""

from __future__ import annotations

import json
import os
from typing import Literal

from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------------------


class LoanRecord(BaseModel):
    """Input: one row from the simulated portfolio CSV."""

    loan_id: str = Field(..., description="Unique loan identifier")
    dpd: int = Field(..., ge=0, description="Days past due")
    origination_rating: str = Field(..., description="Internal rating at origination")
    current_rating: str = Field(..., description="Current internal rating")
    watch_list: bool = Field(..., description="Account on watch list")
    impaired: bool = Field(..., description="Bank has recognised impairment")
    restructured: bool = Field(..., description="Loan has been restructured")
    sector: str = Field(..., description="Industry sector")
    collateral_coverage: float = Field(..., ge=0.0, description="Collateral / exposure ratio")
    macro_signal: Literal["none", "watch", "elevated", "severe"] = Field(
        ..., description="Forward-looking macro overlay"
    )
    loan_amount_myr_k: float = Field(..., gt=0, description="Facility amount RM thousands")


class IFRS9Decision(BaseModel):
    """Output: Claude's staging decision for one loan record."""

    loan_id: str = Field(..., description="Loan identifier (echoed from input)")
    stage: Literal[1, 2, 3] = Field(..., description="IFRS 9 stage (1, 2, or 3)")
    confidence: Literal["High", "Medium", "Low"] = Field(
        ..., description="Model confidence in the staging decision"
    )
    reasoning: str = Field(
        ...,
        description=(
            "Written argument explaining the staging decision. "
            "Must name the specific signals used and acknowledge any ambiguity."
        ),
    )
    key_indicators: list[str] = Field(
        ...,
        description="Bullet-point list of the 2–5 most decisive signals from the record",
    )
    monitoring_flag: bool = Field(
        False,
        description="True if the account warrants elevated monitoring even if Stage 1",
    )


# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """
You are a credit risk analyst applying IFRS 9 Expected Credit Loss (ECL)
staging logic to individual loan records. For each record you must:

1. Assess whether a Significant Increase in Credit Risk (SICR) has occurred
   since origination.
2. Assess whether the account is credit-impaired.
3. Assign the correct IFRS 9 stage (1, 2, or 3).
4. Provide a written argument that names the specific signals you used.
5. Acknowledge ambiguity honestly — do NOT force a clean classification
   when the evidence is genuinely borderline. Explain the tension.

STAGING RULES (apply in order):

Stage 3 — Credit-Impaired (apply first):
  • DPD ≥ 90 days (rebuttable presumption of default)
  • Bank has formally recognised impairment (impaired = true)
  • Strong qualitative evidence: multiple concurrent high-severity signals
    (e.g. DPD 75–89 + CCC rating + watchlist + severe macro + restructured)

Stage 2 — SICR, Not Impaired:
  • DPD 30–89 days
  • Material internal rating migration since origination (≥ 2 notches
    on a AAA-CCC scale where AAA=7, AA=6, A=5, BBB=4, BB=3, B=2, CCC=1)
  • Watch list designation (qualitative SICR indicator)
  • Account has been restructured (IFRS 9 rebuttable SICR presumption;
    requires sustained performance evidence to cure back to Stage 1)
  • macro_signal = "severe" regardless of DPD or rating
  • Combination of moderate signals that together cross the SICR threshold

Stage 1 — No SICR:
  • None of the above applies
  • DPD < 30, stable rating, no watchlist, no restructuring, benign macro
  • Note: even Stage 1 accounts may warrant a monitoring flag if macro_signal
    is "watch" or "elevated" and the sector is cyclically sensitive

IMPORTANT CALIBRATION NOTES:
  • 29 DPD is NOT the same as 30 DPD — the 30-day threshold is a
    rebuttable presumption, not an absolute cliff.
  • Rating migration must be assessed relative to origination, not the
    prior period.
  • Collateral coverage affects loss severity (LGD) but does NOT prevent
    SICR — a well-collateralised loan can still be Stage 2 or 3.
  • Forward-looking macro signals can trigger SICR even with 0 DPD
    when the signal is "severe".
  • Confidence should be "Low" when the decision is genuinely borderline.

OUTPUT FORMAT:
Respond with a single JSON object matching this schema exactly:
{
  "loan_id": "<string>",
  "stage": <1|2|3>,
  "confidence": "<High|Medium|Low>",
  "reasoning": "<multi-sentence explanation>",
  "key_indicators": ["<signal 1>", "<signal 2>", ...],
  "monitoring_flag": <true|false>
}
Do not include any text outside the JSON object.
""".strip()


# ---------------------------------------------------------------------------
# Rating migration helper
# ---------------------------------------------------------------------------

_RATING_NOTCH: dict[str, int] = {
    "AAA": 7,
    "AA": 6,
    "A": 5,
    "BBB": 4,
    "BB": 3,
    "B": 2,
    "CCC": 1,
}


def _rating_drop(origination: str, current: str) -> int:
    """Return number of notches dropped (positive = downgrade)."""
    orig = _RATING_NOTCH.get(origination.upper(), 4)
    curr = _RATING_NOTCH.get(current.upper(), 4)
    return orig - curr


# ---------------------------------------------------------------------------
# Fallback rule-based classifier (no API key required)
# ---------------------------------------------------------------------------


def _rule_based_fallback(loan: LoanRecord) -> IFRS9Decision:
    """
    Deterministic IFRS 9 staging rules used when no API key is present.
    Mirrors the logic in the system prompt so tests are reproducible.
    """
    drop = _rating_drop(loan.origination_rating, loan.current_rating)
    indicators: list[str] = []
    monitoring_flag = False

    # Stage 3
    if loan.impaired or loan.dpd >= 90:
        if loan.impaired:
            indicators.append("Bank-recognised impairment")
        if loan.dpd >= 90:
            indicators.append(f"{loan.dpd} days past due (≥ 90-day default presumption)")
        if drop > 0:
            indicators.append(
                f"Rating migration: {loan.origination_rating} → {loan.current_rating} ({drop} notches)"
            )
        return IFRS9Decision(
            loan_id=loan.loan_id,
            stage=3,
            confidence="High",
            reasoning=(
                f"Objective evidence of credit impairment: "
                f"{'; '.join(indicators)}. Lifetime ECL applies."
            ),
            key_indicators=indicators,
            monitoring_flag=True,
        )

    # Qualitative Stage 3 (multiple concurrent high-severity signals)
    severity_score = (
        int(loan.dpd >= 75)
        + int(_RATING_NOTCH.get(loan.current_rating.upper(), 4) <= 1)  # CCC
        + int(loan.watch_list)
        + int(loan.macro_signal == "severe")
        + int(loan.restructured)
        + int(loan.collateral_coverage < 0.7)
    )
    if severity_score >= 3:
        indicators = [
            f"{loan.dpd} DPD",
            f"Current rating {loan.current_rating}",
            "Watch list" if loan.watch_list else "",
            f"Macro: {loan.macro_signal}",
            "Restructured" if loan.restructured else "",
        ]
        indicators = [i for i in indicators if i]
        return IFRS9Decision(
            loan_id=loan.loan_id,
            stage=3,
            confidence="Medium",
            reasoning=(
                "Multiple concurrent high-severity signals provide qualitative "
                f"evidence of credit impairment despite sub-90 DPD ({loan.dpd} days). "
                f"Severity score {severity_score}/6."
            ),
            key_indicators=indicators,
            monitoring_flag=True,
        )

    # Stage 2
    sicr_triggers: list[str] = []
    if loan.dpd >= 30:
        sicr_triggers.append(f"{loan.dpd} days past due (≥ 30-day SICR threshold)")
    if drop >= 2:
        sicr_triggers.append(
            f"Rating migration {loan.origination_rating} → {loan.current_rating} ({drop} notches)"
        )
    if loan.watch_list:
        sicr_triggers.append("Watch list designation (qualitative SICR indicator)")
    if loan.restructured:
        sicr_triggers.append(
            "Restructured account (IFRS 9 SICR presumption until cure demonstrated)"
        )
    if loan.macro_signal == "severe":
        sicr_triggers.append("Severe macro overlay (forward-looking SICR trigger)")

    if sicr_triggers:
        confidence: Literal["High", "Medium", "Low"] = (
            "High" if len(sicr_triggers) >= 2 else "Medium"
        )
        return IFRS9Decision(
            loan_id=loan.loan_id,
            stage=2,
            confidence=confidence,
            reasoning=(
                f"SICR confirmed: {'; '.join(sicr_triggers)}. "
                "No objective evidence of impairment — lifetime ECL Stage 2."
            ),
            key_indicators=sicr_triggers,
            monitoring_flag=False,
        )

    # Stage 1
    if loan.macro_signal in ("watch", "elevated"):
        monitoring_flag = True
        indicators = [
            f"DPD {loan.dpd} (below 30-day SICR threshold)",
            f"Stable rating {loan.origination_rating} → {loan.current_rating}",
            f"Macro signal: {loan.macro_signal} — monitor for SICR emergence",
        ]
        return IFRS9Decision(
            loan_id=loan.loan_id,
            stage=1,
            confidence="Medium" if loan.macro_signal == "elevated" else "High",
            reasoning=(
                f"No SICR triggers met: DPD {loan.dpd} days (below 30), "
                f"rating stable, no watchlist or restructuring. "
                f"However macro_signal={loan.macro_signal!r} warrants "
                "monitoring — flag set."
            ),
            key_indicators=indicators,
            monitoring_flag=monitoring_flag,
        )

    # Clean Stage 1
    return IFRS9Decision(
        loan_id=loan.loan_id,
        stage=1,
        confidence="High",
        reasoning=(
            f"No SICR signals: DPD {loan.dpd} days, "
            f"rating {loan.origination_rating} → {loan.current_rating} (stable), "
            "no watchlist, not restructured, benign macro."
        ),
        key_indicators=[
            f"DPD {loan.dpd} — well below 30-day threshold",
            f"Rating stable at {loan.current_rating}",
            "No watch list, no restructuring",
            "Macro signal: none",
        ],
        monitoring_flag=False,
    )


# ---------------------------------------------------------------------------
# Main classifier
# ---------------------------------------------------------------------------


def classify_loan(loan: LoanRecord, api_key: str | None = None) -> IFRS9Decision:
    """
    Classify a single loan record under IFRS 9.

    Uses Claude API when api_key is provided (or ANTHROPIC_API_KEY env var
    is set); falls back to deterministic rule engine otherwise.

    Args:
        loan: Validated LoanRecord input.
        api_key: Anthropic API key. Reads ANTHROPIC_API_KEY env var if None.

    Returns:
        IFRS9Decision with stage, confidence, reasoning and key_indicators.
    """
    resolved_key = api_key or os.getenv("ANTHROPIC_API_KEY", "")

    if not resolved_key:
        return _rule_based_fallback(loan)

    try:
        import anthropic  # optional dependency

        client = anthropic.Anthropic(api_key=resolved_key)

        user_message = (
            "Classify the following loan record under IFRS 9:\n\n"
            + json.dumps(loan.model_dump(), indent=2)
        )

        response = client.messages.create(
            model="claude-sonnet-4-6",
            max_tokens=1024,
            system=_SYSTEM_PROMPT,
            messages=[{"role": "user", "content": user_message}],
        )

        raw_text = response.content[0].text.strip()

        # Parse JSON response
        data = json.loads(raw_text)
        return IFRS9Decision(**data)

    except Exception:
        # Any failure (import error, API error, parse error) → fallback
        return _rule_based_fallback(loan)


def classify_portfolio(
    records: list[dict],
    api_key: str | None = None,
) -> list[IFRS9Decision]:
    """
    Classify a list of raw portfolio dicts.

    Args:
        records: List of dicts matching LoanRecord schema (e.g. from CSV).
        api_key: Anthropic API key (optional).

    Returns:
        List of IFRS9Decision in the same order as input.
    """
    results: list[IFRS9Decision] = []
    for raw in records:
        loan = LoanRecord(
            loan_id=raw["loan_id"],
            dpd=int(raw["dpd"]),
            origination_rating=raw["origination_rating"],
            current_rating=raw["current_rating"],
            watch_list=str(raw["watch_list"]).lower() in ("true", "1", "yes"),
            impaired=str(raw["impaired"]).lower() in ("true", "1", "yes"),
            restructured=str(raw["restructured"]).lower() in ("true", "1", "yes"),
            sector=raw["sector"],
            collateral_coverage=float(raw["collateral_coverage"]),
            macro_signal=raw["macro_signal"],
            loan_amount_myr_k=float(raw["loan_amount_myr_k"]),
        )
        results.append(classify_loan(loan, api_key=api_key))
    return results
