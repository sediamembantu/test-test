"""
Tests for geocode tool.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.schemas import GeocodeInput
from src.tools.geocode import geocode_address


class TestGeocodeFallback:
    """Test fallback coordinate resolution."""

    def test_kulai_returns_fallback_coords(self):
        """Kulai address should return hardcoded fallback coordinates."""
        result = geocode_address(GeocodeInput(
            address="Lot 1234, Jalan Perindustrian Kulai, 81000 Kulai, Johor"
        ))
        
        assert result.latitude == 1.6580
        assert result.longitude == 103.6000
        assert result.source == "fallback"
        assert result.confidence == 1.0

    def test_cyberjaya_returns_fallback_coords(self):
        """Cyberjaya address should return hardcoded fallback coordinates."""
        result = geocode_address(GeocodeInput(
            address="Block C, Cyberjaya Technology Park, 63000 Cyberjaya, Selangor"
        ))
        
        assert result.latitude == 2.9228
        assert result.longitude == 101.6538
        assert result.source == "fallback"
        assert result.confidence == 1.0

    def test_partial_kulai_match(self):
        """Partial Kulai address should still match."""
        result = geocode_address(GeocodeInput(address="Kulai, Johor"))
        
        assert result.latitude == 1.6580
        assert result.longitude == 103.6000
        assert result.source == "fallback"

    def test_partial_cyberjaya_match(self):
        """Partial Cyberjaya address should still match."""
        result = geocode_address(GeocodeInput(address="Cyberjaya Technology Park"))
        
        assert result.latitude == 2.9228
        assert result.longitude == 101.6538
        assert result.source == "fallback"


class TestGeocodeNetworkFailure:
    """Test behavior when network is unavailable."""

    @patch('src.tools.geocode.requests.get')
    def test_unknown_address_raises_on_network_failure(self, mock_get):
        """Unknown address should raise ValueError when network fails."""
        # Simulate network failure
        mock_get.side_effect = ConnectionError("Network unreachable")
        
        with pytest.raises(ValueError, match="Could not geocode"):
            geocode_address(GeocodeInput(
                address="Unknown Location, Nowhere City, 00000"
            ))

    @patch('src.tools.geocode.requests.get')
    def test_unknown_address_raises_on_timeout(self, mock_get):
        """Unknown address should raise ValueError on timeout."""
        import requests
        mock_get.side_effect = requests.Timeout("Request timed out")
        
        with pytest.raises(ValueError, match="Could not geocode"):
            geocode_address(GeocodeInput(
                address="123 Mystery Street, Unknown Land"
            ))

    @patch('src.tools.geocode.requests.get')
    def test_unknown_address_raises_on_empty_response(self, mock_get):
        """Unknown address should raise ValueError on empty API response."""
        mock_response = MagicMock()
        mock_response.json.return_value = []  # Empty results
        mock_response.raise_for_status = MagicMock()
        mock_get.return_value = mock_response
        
        with pytest.raises(ValueError, match="Could not geocode"):
            geocode_address(GeocodeInput(
                address="Nonexistent Place, Fake Country"
            ))


class TestGeocodeCoordinates:
    """Test coordinate accuracy for known locations."""

    def test_kulai_in_johor_region(self):
        """Kulai coordinates should be in Johor (lon > 102.5)."""
        result = geocode_address(GeocodeInput(address="Kulai"))
        
        # Johor is east of 102.5 longitude
        assert result.longitude > 102.5

    def test_cyberjaya_in_selangor_region(self):
        """Cyberjaya coordinates should be in Selangor (lon < 102.5)."""
        result = geocode_address(GeocodeInput(address="Cyberjaya"))
        
        # Selangor is west of 102.5 longitude
        assert result.longitude < 102.5

    def test_coordinates_in_malaysia_bounds(self):
        """All fallback coordinates should be within Malaysia bounds."""
        # Malaysia approximately: lat 1-7, lon 99-120
        test_addresses = [
            "Kulai, Johor",
            "Cyberjaya, Selangor",
            "Kuala Lumpur",
        ]
        
        for address in test_addresses:
            result = geocode_address(GeocodeInput(address=address))
            
            assert 1.0 <= result.latitude <= 7.0, f"{address} lat out of bounds"
            assert 99.0 <= result.longitude <= 120.0, f"{address} lon out of bounds"
