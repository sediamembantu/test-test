"""
Document parsing and entity extraction tools.
"""

from __future__ import annotations

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


def parse_document(input_data: ParseDocumentInput) -> ParseDocumentOutput:
    """
    Parse a PDF document and extract structured deal information.

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
    full_text = ""
    for page in doc:
        full_text += page.get_text()
    doc.close()

    # TODO: Implement intelligent section parsing
    # For now, return raw text - entity extraction will be done by Claude

    return ParseDocumentOutput(
        company_name="[EXTRACT FROM TEXT]",
        raw_text=full_text,
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
