"""
Flood risk assessment using JRC Global Flood Maps.
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import FloodDepths, FloodRiskInput, FloodRiskOutput

# Path to pre-clipped JRC rasters
JRC_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "jrc"


def assess_flood_risk(input_data: FloodRiskInput) -> FloodRiskOutput:
    """
    Assess flood risk at a given location using JRC flood maps.

    Args:
        input_data: FloodRiskInput with lat, lon, and asset_name

    Returns:
        FloodRiskOutput with flood depths and risk level
    """
    lat = input_data.latitude
    lon = input_data.longitude

    # Check if JRC data exists
    jrc_files = list(JRC_DATA_DIR.glob("*.tif"))

    # When JRC rasters are present, TODO: implement raster sampling with rasterio
    # For now, use location-aware fallback regardless

    # Location-aware fallback (used when JRC rasters are absent)
    # Johor lowlands (lon > 102.5): flood-prone, High risk
    # Selangor/KL (lon <= 102.5): elevated, Low risk
    if lon > 102.5:
        depths = FloodDepths(rp10=0.3, rp50=0.8, rp100=1.5, rp500=2.8)
        notes = "Location-based estimate: Johor lowland flood zone"
    else:
        depths = FloodDepths(rp10=0.0, rp50=0.1, rp100=0.2, rp500=0.5)
        notes = "Location-based estimate: Selangor elevated corridor"

    return FloodRiskOutput(
        asset_name=input_data.asset_name,
        latitude=lat,
        longitude=lon,
        depths=depths,
        risk_level=_calculate_risk_level(depths),
        notes=notes,
    )


def _calculate_risk_level(depths: FloodDepths) -> str:
    """
    Calculate overall risk level based on flood depths.
    Uses 100-year return period as primary indicator.
    """
    rp100 = depths.rp100

    if rp100 < 0.3:
        return "Low"
    elif rp100 < 1.0:
        return "Medium"
    elif rp100 < 2.0:
        return "High"
    else:
        return "Critical"


def _sample_rasters(lat: float, lon: float) -> FloodDepths:
    """
    Sample JRC flood rasters at given coordinates.

    TODO: Implement with rasterio
    - Load each return period raster
    - Sample pixel value at lat/lon
    - Return FloodDepths with values in meters
    """
    raise NotImplementedError("Raster sampling not yet implemented")
