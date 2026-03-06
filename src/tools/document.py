"""
Document parsing and entity extraction tools.
"""

from __future__ import annotations

import json
from pathlib import Path

import fitz  # pymupdf
from anthropic import Anthropic

from ..schemas import (
    Asset,
    ExtractEntitiesInput,
    ExtractEntitiesOutput,
    Financials,
    ParseDocumentInput,
    ParseDocumentOutput,
)

# Module-level client - reads ANTHROPIC_API_KEY from env
_client = Anthropic()


def _extract_with_llm(raw_text: str) -> dict:
    """Call Claude Haiku to extract structured deal data from raw text."""
    response = _client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=1024,
        system=(
            "You are a financial document parser. "
            "Extract the requested fields and return ONLY valid JSON. "
            "No markdown, no explanation, just the JSON object."
        ),
        messages=[
            {
                "role": "user",
                "content": (
                    "Extract from this deal document:\n\n"
                    f"{raw_text[:6000]}\n\n"
                    "Return JSON with exactly these keys:\n"
                    '{"company_name": str, "company_registration": str, '
                    '"sector": str, "headquarters": str, "deal_type": str, '
                    '"valuation_myr": float, "target_irr": str, '
                    '"assets": [{"name": str, "address": str, '
                    '"capacity_mw": float, "status": str}], '
                    '"financials": {"revenue_myr": [float], '
                    '"ebitda_myr": [float], "capex_myr": [float]}}'
                ),
            }
        ],
    )
    return json.loads(response.content[0].text)


def parse_document(input_data: ParseDocumentInput) -> ParseDocumentOutput:
    """
    Parse a PDF document and extract structured deal information.
    Uses Claude Haiku for intelligent extraction.

    Args:
        input_data: ParseDocumentInput with pdf_path

    Returns:
        ParseDocumentOutput with extracted company, deal, asset, and financial data
    """
    pdf_path = Path(input_data.pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    # Extract all text from PDF
    doc = fitz.open(pdf_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    doc.close()

    # Try LLM extraction, fall back to placeholders on failure
    try:
        extracted = _extract_with_llm(raw_text)

        assets = [
            Asset(
                name=a["name"],
                address=a["address"],
                capacity_mw=a.get("capacity_mw"),
                status=a.get("status"),
            )
            for a in extracted.get("assets", [])
        ]

        financials = Financials(
            revenue_myr=extracted.get("financials", {}).get("revenue_myr", []),
            ebitda_myr=extracted.get("financials", {}).get("ebitda_myr", []),
            capex_myr=extracted.get("financials", {}).get("capex_myr", []),
        )

        return ParseDocumentOutput(
            company_name=extracted.get("company_name", "Unknown"),
            company_registration=extracted.get("company_registration"),
            sector=extracted.get("sector"),
            headquarters=extracted.get("headquarters"),
            deal_type=extracted.get("deal_type"),
            valuation_myr=extracted.get("valuation_myr"),
            target_irr=extracted.get("target_irr"),
            assets=assets,
            financials=financials,
            raw_text=raw_text,
        )
    except Exception:
        # Fallback to placeholders so demo never crashes
        return ParseDocumentOutput(
            company_name="[EXTRACT FROM TEXT]",
            raw_text=raw_text,
            assets=[],
            financials=Financials(),
        )


def extract_entities(input_data: ExtractEntitiesInput) -> ExtractEntitiesOutput:
    """
    Extract named entities from text.
    This is a lightweight wrapper - Claude does the heavy lifting via prompting.

    Args:
        input_data: ExtractEntitiesInput with text

    Returns:
        ExtractEntitiesOutput with extracted entities
    """
    # This function is primarily called via Claude tool-use
    # Claude extracts entities directly; this is a placeholder for programmatic use
    return ExtractEntitiesOutput(
        companies=[],
        locations=[],
        dates=[],
        monetary_values=[],
        percentages=[],
    )
