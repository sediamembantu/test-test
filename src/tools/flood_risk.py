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
    if not jrc_files:
        # No data available - return placeholder
        return FloodRiskOutput(
            asset_name=input_data.asset_name,
            latitude=lat,
            longitude=lon,
            depths=FloodDepths(),
            risk_level="Medium",  # Conservative default
            notes="JRC flood data not available - manual assessment required",
        )

    # TODO: Implement raster sampling with rasterio
    # Sample each return period raster at lat/lon
    # depths = _sample_rasters(lat, lon)

    # Placeholder return
    return FloodRiskOutput(
        asset_name=input_data.asset_name,
        latitude=lat,
        longitude=lon,
        depths=FloodDepths(
            rp10=0.0,
            rp50=0.5,
            rp100=1.2,
            rp500=2.0,
        ),
        risk_level=_calculate_risk_level(FloodDepths(rp100=1.2)),
        notes="Placeholder data - implement raster sampling",
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
