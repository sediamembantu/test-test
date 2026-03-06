"""Tests for geocode_address tool."""

from unittest.mock import patch

import pytest

from src.schemas import GeocodeInput
from src.tools.geocode import geocode_address


def test_kulai_address_returns_fallback_coords():
    """Known Kulai address hits fallback without calling Nominatim."""
    input_data = GeocodeInput(
        address="Lot 1234, Jalan Perindustrian Kulai, 81000 Kulai, Johor"
    )
    with patch("requests.get") as mock_get:
        result = geocode_address(input_data)
        mock_get.assert_not_called()

    assert result.latitude == pytest.approx(1.6580)
    assert result.longitude == pytest.approx(103.6000)
    assert result.source == "fallback"


def test_cyberjaya_address_returns_fallback_coords():
    """Known Cyberjaya address hits fallback without calling Nominatim."""
    input_data = GeocodeInput(
        address="Block C, Cyberjaya Technology Park, 63000 Cyberjaya, Selangor"
    )
    with patch("requests.get") as mock_get:
        result = geocode_address(input_data)
        mock_get.assert_not_called()

    assert result.latitude == pytest.approx(2.9228)
    assert result.longitude == pytest.approx(101.6538)
    assert result.source == "fallback"


def test_unknown_address_raises_on_network_failure():
    """Unknown address with network failure raises ValueError."""
    input_data = GeocodeInput(address="123 Nonexistent Street, Nowhere")

    with patch("requests.get", side_effect=ConnectionError("Network unavailable")):
        with pytest.raises(ValueError, match="Could not geocode address"):
            geocode_address(input_data)
