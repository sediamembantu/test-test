"""
Pydantic models for tool inputs and outputs.
All tools use these schemas for type-safe I/O.
"""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field


# ============================================================================
# Document Tool Schemas
# ============================================================================


class ParseDocumentInput(BaseModel):
    """Input for parse_document tool."""

    pdf_path: str = Field(..., description="Path to the PDF document")


class Financials(BaseModel):
    """Financial data extracted from document."""

    revenue_myr: list[float] = Field(default_factory=list, description="Revenue in RM millions by year")
    ebitda_myr: list[float] = Field(default_factory=list, description="EBITDA in RM millions by year")
    capex_myr: list[float] = Field(default_factory=list, description="Capex in RM millions by year")


class Asset(BaseModel):
    """Physical asset information."""

    name: str = Field(..., description="Asset name")
    address: str = Field(..., description="Full address")
    capacity_mw: float | None = Field(None, description="Capacity in MW")
    status: str | None = Field(None, description="Operational status")
    latitude: float | None = Field(None, description="Latitude coordinate")
    longitude: float | None = Field(None, description="Longitude coordinate")


class ParseDocumentOutput(BaseModel):
    """Output from parse_document tool."""

    company_name: str = Field(..., description="Company name")
    company_registration: str | None = Field(None, description="SSM registration number")
    sector: str | None = Field(None, description="Industry sector")
    founded_year: int | None = Field(None, description="Year founded")
    headquarters: str | None = Field(None, description="HQ location")

    deal_type: str | None = Field(None, description="Type of deal")
    valuation_myr: float | None = Field(None, description="Deal valuation in RM")
    target_irr: str | None = Field(None, description="Target IRR")

    assets: list[Asset] = Field(default_factory=list, description="Physical assets")
    financials: Financials = Field(default_factory=Financials, description="Financial data")

    raw_text: str = Field(..., description="Full extracted text")


class ExtractEntitiesInput(BaseModel):
    """Input for extract_entities tool."""

    text: str = Field(..., description="Text to extract entities from")


class ExtractEntitiesOutput(BaseModel):
    """Output from extract_entities tool."""

    companies: list[str] = Field(default_factory=list, description="Company names")
    locations: list[str] = Field(default_factory=list, description="Location names")
    dates: list[str] = Field(default_factory=list, description="Dates mentioned")
    monetary_values: list[str] = Field(default_factory=list, description="Monetary amounts")
    percentages: list[str] = Field(default_factory=list, description="Percentage values")


# ============================================================================
# Geocode Tool Schemas
# ============================================================================


class GeocodeInput(BaseModel):
    """Input for geocode_address tool."""

    address: str = Field(..., description="Address to geocode")


class GeocodeOutput(BaseModel):
    """Output from geocode_address tool."""

    address: str = Field(..., description="Original address")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    source: Literal["nominatim", "fallback"] = Field(
        ..., description="Source of coordinates"
    )
    confidence: float = Field(
        1.0, ge=0.0, le=1.0, description="Confidence score (0-1)"
    )


# ============================================================================
# Flood Risk Tool Schemas
# ============================================================================


class FloodRiskInput(BaseModel):
    """Input for assess_flood_risk tool."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    asset_name: str = Field(..., description="Name of asset for reporting")


class FloodDepths(BaseModel):
    """Flood depths by return period in meters."""

    rp10: float = Field(0.0, description="10-year return period depth (m)")
    rp50: float = Field(0.0, description="50-year return period depth (m)")
    rp100: float = Field(0.0, description="100-year return period depth (m)")
    rp500: float = Field(0.0, description="500-year return period depth (m)")


class FloodRiskOutput(BaseModel):
    """Output from assess_flood_risk tool."""

    asset_name: str = Field(..., description="Asset name")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    depths: FloodDepths = Field(..., description="Flood depths by return period")
    risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        ..., description="Overall risk category"
    )
    notes: str = Field("", description="Additional notes")


# ============================================================================
# Transition Risk Tool Schemas
# ============================================================================


class TransitionRiskInput(BaseModel):
    """Input for assess_transition_risk tool."""

    sector: str = Field(..., description="Industry sector")
    subsector: str | None = Field(None, description="Subsector if applicable")


class TransitionRiskOutput(BaseModel):
    """Output from assess_transition_risk tool."""

    sector: str = Field(..., description="Sector assessed")
    risk_level: Literal["Low", "Medium", "High", "Critical"] = Field(
        ..., description="Transition risk level"
    )
    ngfs_scenario: str = Field(..., description="NGFS scenario used")
    key_risks: list[str] = Field(
        default_factory=list, description="Key transition risk factors"
    )
    carbon_intensity: str | None = Field(None, description="Sector carbon intensity")


# ============================================================================
# Biodiversity Tool Schemas
# ============================================================================


class BiodiversityInput(BaseModel):
    """Input for check_biodiversity tool."""

    latitude: float = Field(..., description="Latitude coordinate")
    longitude: float = Field(..., description="Longitude coordinate")
    asset_name: str = Field(..., description="Asset name")


class BiodiversityOutput(BaseModel):
    """Output from check_biodiversity tool."""

    asset_name: str = Field(..., description="Asset name")
    nearest_protected_area: str | None = Field(
        None, description="Name of nearest protected area"
    )
    distance_km: float | None = Field(None, description="Distance to nearest protected area")
    protected_area_type: str | None = Field(
        None, description="Type of protected area (national park, wetland, etc.)"
    )
    risk_flag: bool = Field(False, description="Whether asset is near sensitive area")
    notes: str = Field("", description="Additional notes")


# ============================================================================
# Mapping Tool Schemas
# ============================================================================


class MapInput(BaseModel):
    """Input for generate_map tool."""

    assets: list[Asset] = Field(..., description="Assets to plot")
    flood_data: bool = Field(True, description="Include flood risk overlay")
    output_path: str = Field("output/map.html", description="Output HTML path")


class MapOutput(BaseModel):
    """Output from generate_map tool."""

    map_path: str = Field(..., description="Path to generated HTML map")
    asset_count: int = Field(..., description="Number of assets plotted")
    bounds: tuple[float, float, float, float] = Field(
        ..., description="Map bounds (min_lat, min_lon, max_lat, max_lon)"
    )


# ============================================================================
# Report Tool Schemas
# ============================================================================


class ReportInput(BaseModel):
    """Input for generate_report tool."""

    company_name: str = Field(..., description="Company name")
    deal_overview: dict = Field(..., description="Deal summary data")
    assets: list[Asset] = Field(..., description="Asset information")
    flood_risks: list[FloodRiskOutput] = Field(
        default_factory=list, description="Flood risk assessments"
    )
    transition_risk: TransitionRiskOutput | None = Field(
        None, description="Transition risk assessment"
    )
    biodiversity: list[BiodiversityOutput] = Field(
        default_factory=list, description="Biodiversity assessments"
    )
    esg_gaps: list[str] = Field(default_factory=list, description="Identified ESG gaps")
    red_flags: list[str] = Field(default_factory=list, description="Red flags identified")
    output_format: Literal["html", "docx", "markdown"] = Field(
        "html", description="Output format"
    )
    output_path: str = Field("output/memo", description="Output path (without extension)")


class ReportOutput(BaseModel):
    """Output from generate_report tool."""

    report_path: str = Field(..., description="Path to generated report")
    format: str = Field(..., description="Report format")
    generated_at: str = Field(..., description="Generation timestamp")
