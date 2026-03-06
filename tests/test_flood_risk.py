"""
Tests for flood risk assessment tool.
"""

import pytest

from src.schemas import FloodRiskInput, FloodDepths
from src.tools.flood_risk import assess_flood_risk, _calculate_risk_level


class TestFloodRiskByLocation:
    """Test location-aware flood risk assessment."""

    def test_kulai_returns_high_risk(self):
        """Kulai coordinates (Johor) should return High flood risk."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=1.658,
            longitude=103.6,
            asset_name="Kulai Campus"
        ))
        
        assert result.risk_level == "High"
        assert result.asset_name == "Kulai Campus"
        assert result.latitude == 1.658
        assert result.longitude == 103.6

    def test_cyberjaya_returns_low_risk(self):
        """Cyberjaya coordinates (Selangor) should return Low flood risk."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=2.9228,
            longitude=101.6538,
            asset_name="Cyberjaya DR Site"
        ))
        
        assert result.risk_level == "Low"
        assert result.asset_name == "Cyberjaya DR Site"
        assert result.latitude == 2.9228
        assert result.longitude == 101.6538

    def test_johor_region_high_risk(self):
        """Any Johor location (lon > 102.5) should return High risk."""
        # Various Johor coordinates
        johor_coords = [
            (1.5, 103.0),
            (2.0, 103.5),
            (1.658, 103.6),  # Kulai
        ]
        
        for lat, lon in johor_coords:
            result = assess_flood_risk(FloodRiskInput(
                latitude=lat,
                longitude=lon,
                asset_name=f"Test {lat},{lon}"
            ))
            assert result.risk_level == "High", f"Expected High for ({lat}, {lon})"

    def test_selangor_region_low_risk(self):
        """Any Selangor/KL location (lon <= 102.5) should return Low risk."""
        # Various Selangor/KL coordinates
        selangor_coords = [
            (3.0, 101.5),
            (2.9228, 101.6538),  # Cyberjaya
            (3.139, 101.6869),  # KL
        ]
        
        for lat, lon in selangor_coords:
            result = assess_flood_risk(FloodRiskInput(
                latitude=lat,
                longitude=lon,
                asset_name=f"Test {lat},{lon}"
            ))
            assert result.risk_level == "Low", f"Expected Low for ({lat}, {lon})"


class TestFloodDepths:
    """Test flood depth values by return period."""

    def test_kulai_depths_are_realistic(self):
        """Kulai flood depths should be realistic for lowland area."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=1.658,
            longitude=103.6,
            asset_name="Kulai"
        ))
        
        # Depths should increase with return period
        assert result.depths.rp10 < result.depths.rp50
        assert result.depths.rp50 < result.depths.rp100
        assert result.depths.rp100 < result.depths.rp500
        
        # 100-year depth should be significant (1.0-2.0m range for High risk)
        assert 1.0 <= result.depths.rp100 <= 2.0

    def test_cyberjaya_depths_are_low(self):
        """Cyberjaya flood depths should be minimal."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=2.9228,
            longitude=101.6538,
            asset_name="Cyberjaya"
        ))
        
        # All depths should be low
        assert result.depths.rp10 < 0.5
        assert result.depths.rp50 < 0.5
        assert result.depths.rp100 < 0.5
        assert result.depths.rp500 < 1.0

    def test_depths_structure(self):
        """Flood depths should have all return periods."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=1.658,
            longitude=103.6,
            asset_name="Test"
        ))
        
        assert hasattr(result.depths, 'rp10')
        assert hasattr(result.depths, 'rp50')
        assert hasattr(result.depths, 'rp100')
        assert hasattr(result.depths, 'rp500')
        assert all(isinstance(d, (int, float)) for d in [
            result.depths.rp10,
            result.depths.rp50,
            result.depths.rp100,
            result.depths.rp500,
        ])


class TestRiskLevelCalculation:
    """Test the _calculate_risk_level helper function."""

    def test_low_risk_threshold(self):
        """rp100 < 0.3 should be Low risk."""
        assert _calculate_risk_level(FloodDepths(rp100=0.0)) == "Low"
        assert _calculate_risk_level(FloodDepths(rp100=0.1)) == "Low"
        assert _calculate_risk_level(FloodDepths(rp100=0.29)) == "Low"

    def test_medium_risk_threshold(self):
        """0.3 <= rp100 < 1.0 should be Medium risk."""
        assert _calculate_risk_level(FloodDepths(rp100=0.3)) == "Medium"
        assert _calculate_risk_level(FloodDepths(rp100=0.5)) == "Medium"
        assert _calculate_risk_level(FloodDepths(rp100=0.99)) == "Medium"

    def test_high_risk_threshold(self):
        """1.0 <= rp100 < 2.0 should be High risk."""
        assert _calculate_risk_level(FloodDepths(rp100=1.0)) == "High"
        assert _calculate_risk_level(FloodDepths(rp100=1.5)) == "High"
        assert _calculate_risk_level(FloodDepths(rp100=1.99)) == "High"

    def test_critical_risk_threshold(self):
        """rp100 >= 2.0 should be Critical risk."""
        assert _calculate_risk_level(FloodDepths(rp100=2.0)) == "Critical"
        assert _calculate_risk_level(FloodDepths(rp100=2.5)) == "Critical"
        assert _calculate_risk_level(FloodDepths(rp100=5.0)) == "Critical"


class TestFloodRiskOutput:
    """Test FloodRiskOutput structure."""

    def test_output_has_required_fields(self):
        """Output should have all required fields."""
        result = assess_flood_risk(FloodRiskInput(
            latitude=1.658,
            longitude=103.6,
            asset_name="Test Asset"
        ))
        
        assert hasattr(result, 'asset_name')
        assert hasattr(result, 'latitude')
        assert hasattr(result, 'longitude')
        assert hasattr(result, 'depths')
        assert hasattr(result, 'risk_level')
        assert hasattr(result, 'notes')

    def test_notes_are_informative(self):
        """Notes should provide context about the assessment."""
        # Kulai should mention Johor/lowland
        kulai = assess_flood_risk(FloodRiskInput(
            latitude=1.658,
            longitude=103.6,
            asset_name="Kulai"
        ))
        assert "Johor" in kulai.notes or "lowland" in kulai.notes.lower()
        
        # Cyberjaya should mention Selangor
        cyber = assess_flood_risk(FloodRiskInput(
            latitude=2.9228,
            longitude=101.6538,
            asset_name="Cyberjaya"
        ))
        assert "Selangor" in cyber.notes or "elevated" in cyber.notes.lower()
