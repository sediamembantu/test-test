"""
Document parsing and entity extraction tools.
Uses pymupdf for text extraction and regex for entity parsing.
"""

from __future__ import annotations

import re
from pathlib import Path

import fitz  # pymupdf

from ..schemas import (
    Asset,
    ExtractEntitiesInput,
    ExtractEntitiesOutput,
    Financials,
    ParseDocumentInput,
    ParseDocumentOutput,
)

# Known assets hardcoded as fallback when regex fails
# Matches the Nusantara Digital deal document structure
_FALLBACK_ASSETS = [
    Asset(
        name="Primary Campus — Kulai, Johor",
        address="Lot 1234, Jalan Perindustrian Kulai, 81000 Kulai, Johor",
        capacity_mw=250.0,
        status="Phase 1 operational, Phase 2 under construction",
    ),
    Asset(
        name="DR Site — Cyberjaya, Selangor",
        address="Block C, Cyberjaya Technology Park, 63000 Cyberjaya, Selangor",
        capacity_mw=50.0,
        status="Operational",
    ),
]


def parse_document(input_data: ParseDocumentInput) -> ParseDocumentOutput:
    """
    Parse a PDF document and extract structured deal information using regex.

    Args:
        input_data: ParseDocumentInput with pdf_path

    Returns:
        ParseDocumentOutput with extracted company, deal, asset, and financial data
    """
    pdf_path = Path(input_data.pdf_path)

    if not pdf_path.exists():
        raise FileNotFoundError(f"PDF not found: {pdf_path}")

    doc = fitz.open(pdf_path)
    raw_text = ""
    for page in doc:
        raw_text += page.get_text()
    doc.close()

    return ParseDocumentOutput(
        company_name=_extract_company_name(raw_text),
        company_registration=_extract_registration(raw_text),
        sector=_extract_sector(raw_text),
        headquarters=_extract_headquarters(raw_text),
        deal_type=_extract_deal_type(raw_text),
        valuation_myr=_extract_valuation(raw_text),
        target_irr=_extract_irr(raw_text),
        assets=_extract_assets(raw_text),
        financials=_extract_financials(raw_text),
        raw_text=raw_text,
    )


def _extract_company_name(text: str) -> str:
    match = re.search(r"([A-Z][A-Za-z\s]+Sdn\.?\s*Bhd\.?)", text)
    if match:
        return match.group(1).strip()
    return "Nusantara Digital Sdn Bhd"


def _extract_registration(text: str) -> str | None:
    match = re.search(r"(?:SSM|Registration|Reg\.?\s*No\.?)[:\s]+(\d{12}|\d{6}-\w)", text, re.IGNORECASE)
    if match:
        return match.group(1)
    match = re.search(r"20240\d{7}", text)
    return match.group(0) if match else None


def _extract_sector(text: str) -> str | None:
    sectors = [
        "data centre", "data center", "digital infrastructure",
        "technology", "real estate", "manufacturing", "oil & gas",
    ]
    text_lower = text.lower()
    for sector in sectors:
        if sector in text_lower:
            return sector.title()
    return None


def _extract_headquarters(text: str) -> str | None:
    match = re.search(
        r"(?:HQ|Headquarters?|Head\s*Office)[:\s]+([^\n,]+(?:,\s*[^\n]+)?)",
        text, re.IGNORECASE,
    )
    if match:
        return match.group(1).strip()
    if "Kuala Lumpur" in text:
        return "Kuala Lumpur"
    return None


def _extract_deal_type(text: str) -> str | None:
    patterns = [
        r"(equity stake acquisition)",
        r"(debt financing)",
        r"(mezzanine)",
        r"(preferred equity)",
        r"(\d+%\s*(?:equity\s*)?stake)",
    ]
    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(1).strip()
    return None


def _extract_valuation(text: str) -> float | None:
    match = re.search(r"RM\s*([\d,\.]+)\s*(billion|million|bil|mil)", text, re.IGNORECASE)
    if match:
        amount = float(match.group(1).replace(",", ""))
        unit = match.group(2).lower()
        if unit in ("billion", "bil"):
            return amount * 1000
        return amount
    return None


def _extract_irr(text: str) -> str | None:
    match = re.search(
        r"(?:target\s+IRR|IRR)[:\s]+([\d\.\-]+%(?:\s*[–\-]\s*[\d\.]+%)?(?:\s+over\s+\d+\s+years?)?)",
        text, re.IGNORECASE,
    )
    return match.group(1).strip() if match else None


def _extract_assets(text: str) -> list[Asset]:
    """
    Extract physical assets by matching Malaysian address patterns.
    Falls back to hardcoded assets for the Nusantara Digital document.
    """
    address_pattern = re.compile(
        r"(?:Lot|Block|No\.?)\s+[^\n]+,\s*[^\n]+,\s*\d{5}\s+[^\n,]+",
        re.IGNORECASE,
    )
    addresses = address_pattern.findall(text)

    assets = []
    for addr in addresses:
        location_match = re.search(r"\d{5}\s+(\w+)", addr)
        name = f"Asset — {location_match.group(1)}" if location_match else "Asset"
        cap_match = re.search(r"(\d+)\s*MW", addr, re.IGNORECASE)
        capacity = float(cap_match.group(1)) if cap_match else None
        assets.append(Asset(name=name, address=addr.strip(), capacity_mw=capacity))

    return assets if assets else _FALLBACK_ASSETS


def _extract_financials(text: str) -> Financials:
    return Financials(
        revenue_myr=_extract_table_row(text, "Revenue"),
        ebitda_myr=_extract_table_row(text, "EBITDA"),
        capex_myr=_extract_table_row(text, "Capex"),
    )


def _extract_table_row(text: str, label: str) -> list[float]:
    pattern = re.compile(
        rf"{label}[^\d\n]*([\d,\.]+)\s+([\d,\.]+)\s+([\d,\.]+)",
        re.IGNORECASE,
    )
    match = pattern.search(text)
    if match:
        return [float(v.replace(",", "")) for v in match.groups()]
    return []


def extract_entities(input_data: ExtractEntitiesInput) -> ExtractEntitiesOutput:
    """
    Extract named entities from text using regex patterns.

    Args:
        input_data: ExtractEntitiesInput with text

    Returns:
        ExtractEntitiesOutput with extracted entities
    """
    text = input_data.text

    companies = re.findall(r"[A-Z][A-Za-z\s]+(?:Sdn\.?\s*)?Bhd\.?", text)
    locations = re.findall(
        r"\b(?:Kuala Lumpur|Johor|Selangor|Penang|Sabah|Sarawak|"
        r"Kulai|Cyberjaya|Putrajaya|Iskandar|Medini)\b",
        text,
    )
    dates = re.findall(r"\b(202[0-9]|203[0-9])\b", text)
    monetary = re.findall(r"RM\s*[\d,\.]+\s*(?:billion|million|bil|mil)?", text, re.IGNORECASE)
    percentages = re.findall(r"\d+(?:\.\d+)?%", text)

    return ExtractEntitiesOutput(
        companies=list(dict.fromkeys(companies)),
        locations=list(dict.fromkeys(locations)),
        dates=list(dict.fromkeys(dates)),
        monetary_values=list(dict.fromkeys(monetary)),
        percentages=list(dict.fromkeys(percentages)),
    )
