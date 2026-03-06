"""Tests for assess_flood_risk tool."""

from src.schemas import FloodRiskInput
from src.tools.flood_risk import assess_flood_risk


def test_kulai_returns_medium_risk():
    """Kulai coords return a valid risk level (no JRC data present)."""
    input_data = FloodRiskInput(
        latitude=1.658,
        longitude=103.6,
        asset_name="Kulai Data Centre",
    )
    result = assess_flood_risk(input_data)

    assert result.asset_name == "Kulai Data Centre"
    assert result.risk_level in ("Low", "Medium", "High", "Critical")
    assert result.latitude == 1.658
    assert result.longitude == 103.6


def test_cyberjaya_returns_valid_risk():
    """Cyberjaya coords return a valid risk level (no JRC data present)."""
    input_data = FloodRiskInput(
        latitude=2.9228,
        longitude=101.6538,
        asset_name="Cyberjaya DC",
    )
    result = assess_flood_risk(input_data)

    assert result.asset_name == "Cyberjaya DC"
    assert result.risk_level in ("Low", "Medium", "High", "Critical")


def test_output_has_all_depth_fields():
    """FloodRiskOutput always includes all four return-period depths."""
    input_data = FloodRiskInput(
        latitude=3.139,
        longitude=101.6869,
        asset_name="Test Asset",
    )
    result = assess_flood_risk(input_data)

    assert hasattr(result.depths, "rp10")
    assert hasattr(result.depths, "rp50")
    assert hasattr(result.depths, "rp100")
    assert hasattr(result.depths, "rp500")
