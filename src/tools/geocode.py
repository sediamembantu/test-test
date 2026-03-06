"""
Geocoding tool using Nominatim with hardcoded fallbacks.
"""

from __future__ import annotations

import time

from ..schemas import GeocodeInput, GeocodeOutput

# Hardcoded fallback coordinates for known Malaysian locations
# Ensures demo never fails due to API timeout
FALLBACK_COORDS = {
    "kulai": (1.6580, 103.6000),
    "kulai, johor": (1.6580, 103.6000),
    "lot 1234, jalan perindustrian kulai, 81000 kulai, johor": (1.6580, 103.6000),
    "cyberjaya": (2.9228, 101.6538),
    "cyberjaya, selangor": (2.9228, 101.6538),
    "block c, cyberjaya technology park, 63000 cyberjaya, selangor": (2.9228, 101.6538),
    "kuala lumpur": (3.1390, 101.6869),
    "johor bahru": (1.4927, 103.7414),
}


def geocode_address(input_data: GeocodeInput) -> GeocodeOutput:
    """
    Geocode an address to latitude/longitude coordinates.
    Uses Nominatim API with fallback to hardcoded coordinates.

    Args:
        input_data: GeocodeInput with address

    Returns:
        GeocodeOutput with coordinates and source
    """
    address = input_data.address.strip().lower()

    # Check fallback coordinates first (ensures demo reliability)
    for key, coords in FALLBACK_COORDS.items():
        if key in address:
            return GeocodeOutput(
                address=input_data.address,
                latitude=coords[0],
                longitude=coords[1],
                source="fallback",
                confidence=1.0,
            )

    # Try Nominatim API
    try:
        import requests

        # Rate limit: 1 request per second
        time.sleep(1.1)

        url = "https://nominatim.openstreetmap.org/search"
        params = {
            "q": input_data.address,
            "format": "json",
            "limit": 1,
        }
        headers = {
            "User-Agent": "CADI/0.1.0 (Climate-Aware Deal Intelligence Demo)"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        if data:
            result = data[0]
            return GeocodeOutput(
                address=input_data.address,
                latitude=float(result["lat"]),
                longitude=float(result["lon"]),
                source="nominatim",
                confidence=0.8,  # Default confidence for API results
            )
    except Exception:
        pass  # Fall through to error

    # No match found
    raise ValueError(f"Could not geocode address: {input_data.address}")
