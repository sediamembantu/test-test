"""Tests for assess_transition_risk tool."""

from src.schemas import TransitionRiskInput
from src.tools.transition import assess_transition_risk


def test_data_centre_returns_high_risk():
    """Data centre sector maps to High transition risk."""
    input_data = TransitionRiskInput(sector="data centre")
    result = assess_transition_risk(input_data)

    assert result.risk_level == "High"
    assert result.ngfs_scenario == "Net Zero 2050"
    assert len(result.key_risks) > 0


def test_unknown_sector_returns_medium_risk():
    """Unknown sector defaults to Medium with uncertainty note."""
    input_data = TransitionRiskInput(sector="artisanal cheese production")
    result = assess_transition_risk(input_data)

    assert result.risk_level == "Medium"
    assert result.sector == "artisanal cheese production"


def test_sector_matching_is_case_insensitive():
    """Sector lookup is case-insensitive."""
    lower = assess_transition_risk(TransitionRiskInput(sector="data centre"))
    upper = assess_transition_risk(TransitionRiskInput(sector="Data Centre"))
    mixed = assess_transition_risk(TransitionRiskInput(sector="DATA CENTRE"))

    assert lower.risk_level == upper.risk_level == mixed.risk_level


def test_oil_and_gas_returns_critical():
    """Oil & gas sector maps to Critical risk."""
    input_data = TransitionRiskInput(sector="oil & gas")
    result = assess_transition_risk(input_data)

    assert result.risk_level == "Critical"
