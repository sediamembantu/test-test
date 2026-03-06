"""
Biodiversity and protected area proximity check.
"""

from __future__ import annotations

from pathlib import Path

from ..schemas import BiodiversityInput, BiodiversityOutput

# Path to WDPA protected areas data
WDPA_DATA_DIR = Path(__file__).parent.parent.parent / "data" / "wdpa"

# Known protected areas near project locations (fallback)
KNOWN_PROTECTED_AREAS = [
    {
        "name": "Sungai Skudai Wetlands",
        "type": "Wetland / Ramsar candidate",
        "latitude": 1.55,
        "longitude": 103.65,
    },
    {
        "name": "Taman Negara Johor",
        "type": "State Park",
        "latitude": 2.50,
        "longitude": 103.50,
    },
]


def check_biodiversity(input_data: BiodiversityInput) -> BiodiversityOutput:
    """
    Check proximity to protected areas using WDPA data.

    Args:
        input_data: BiodiversityInput with lat, lon, and asset_name

    Returns:
        BiodiversityOutput with protected area proximity
    """
    lat = input_data.latitude
    lon = input_data.longitude

    # Check if WDPA data exists
    wdpa_files = list(WDPA_DATA_DIR.glob("*.gpkg")) + list(WDPA_DATA_DIR.glob("*.shp"))
    if not wdpa_files:
        # Use fallback data
        return _check_fallback(input_data)

    # TODO: Implement actual WDPA proximity check with geopandas
    return _check_fallback(input_data)


def _check_fallback(input_data: BiodiversityInput) -> BiodiversityOutput:
    """
    Fallback check using hardcoded known protected areas.
    """
    lat = input_data.latitude
    lon = input_data.longitude

    nearest = None
    min_distance = float("inf")

    for area in KNOWN_PROTECTED_AREAS:
        dist = _haversine_distance(lat, lon, area["latitude"], area["longitude"])
        if dist < min_distance:
            min_distance = dist
            nearest = area

    if nearest and min_distance < 50:  # Within 50km
        return BiodiversityOutput(
            asset_name=input_data.asset_name,
            nearest_protected_area=nearest["name"],
            distance_km=round(min_distance, 1),
            protected_area_type=nearest["type"],
            risk_flag=min_distance < 10,  # Flag if within 10km
            notes=f"Asset is {min_distance:.1f}km from {nearest['name']}",
        )

    return BiodiversityOutput(
        asset_name=input_data.asset_name,
        nearest_protected_area=None,
        distance_km=None,
        protected_area_type=None,
        risk_flag=False,
        notes="No protected areas within 50km",
    )


def _haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate distance between two points in km using Haversine formula.
    """
    import math

    R = 6371  # Earth radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))

    return R * c
