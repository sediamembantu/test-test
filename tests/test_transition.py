"""
Tests for transition risk assessment tool.
"""

import pytest

from src.schemas import TransitionRiskInput
from src.tools.transition import assess_transition_risk, NGFS_SECTOR_RISKS


class TestTransitionRiskBySector:
    """Test transition risk assessment by sector."""

    def test_data_centre_returns_high_risk(self):
        """Data centre sector should return High transition risk."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        
        assert result.risk_level == "High"
        assert result.sector == "data centre"
        assert result.ngfs_scenario == "Net Zero 2050"

    def test_oil_gas_returns_critical_risk(self):
        """Oil & gas sector should return Critical transition risk."""
        result = assess_transition_risk(TransitionRiskInput(sector="oil & gas"))
        
        assert result.risk_level == "Critical"
        assert "stranded asset" in " ".join(result.key_risks).lower()

    def test_real_estate_returns_medium_risk(self):
        """Real estate sector should return Medium transition risk."""
        result = assess_transition_risk(TransitionRiskInput(sector="real estate"))
        
        assert result.risk_level == "Medium"

    def test_unknown_sector_returns_medium_risk(self):
        """Unknown sector should return Medium risk (conservative default)."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="Made Up Sector XYZ"
        ))
        
        assert result.risk_level == "Medium"
        assert "uncertain" in " ".join(result.key_risks).lower()


class TestCaseInsensitivity:
    """Test case-insensitive sector matching."""

    def test_lowercase_data_centre(self):
        """Lowercase 'data centre' should work."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        assert result.risk_level == "High"

    def test_uppercase_data_centre(self):
        """Uppercase 'DATA CENTRE' should work."""
        result = assess_transition_risk(TransitionRiskInput(sector="DATA CENTRE"))
        assert result.risk_level == "High"

    def test_mixed_case_data_centre(self):
        """Mixed case 'Data Centre' should work."""
        result = assess_transition_risk(TransitionRiskInput(sector="Data Centre"))
        assert result.risk_level == "High"

    def test_title_case_oil_gas(self):
        """Title case 'Oil & Gas' should work."""
        result = assess_transition_risk(TransitionRiskInput(sector="Oil & Gas"))
        assert result.risk_level == "Critical"

    def test_with_extra_whitespace(self):
        """Sector with extra whitespace should work."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="  data centre  "
        ))
        assert result.risk_level == "High"


class TestTransitionRiskOutput:
    """Test TransitionRiskOutput structure."""

    def test_output_has_required_fields(self):
        """Output should have all required fields."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        
        assert hasattr(result, 'sector')
        assert hasattr(result, 'risk_level')
        assert hasattr(result, 'ngfs_scenario')
        assert hasattr(result, 'key_risks')
        assert hasattr(result, 'carbon_intensity')

    def test_key_risks_is_list(self):
        """key_risks should be a list of strings."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        
        assert isinstance(result.key_risks, list)
        assert len(result.key_risks) > 0
        assert all(isinstance(r, str) for r in result.key_risks)

    def test_carbon_intensity_for_known_sectors(self):
        """Known sectors should have carbon intensity info."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        
        assert result.carbon_intensity is not None
        assert "kg" in result.carbon_intensity.lower() or "high" in result.carbon_intensity.lower()

    def test_carbon_intensity_none_for_unknown(self):
        """Unknown sectors should have None carbon intensity."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="Completely Unknown Sector"
        ))
        
        assert result.carbon_intensity is None


class TestSectorMatching:
    """Test sector matching logic."""

    def test_partial_match_data_centre(self):
        """Partial match like 'hyperscale data centre' should work."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="hyperscale data centre operator"
        ))
        assert result.risk_level == "High"

    def test_partial_match_digital_infra(self):
        """Partial match for 'digital infrastructure' should work."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="digital infrastructure"
        ))
        assert result.risk_level == "High"

    def test_sector_with_subsector(self):
        """Subsector should be accepted (even if not used)."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="data centre",
            subsector="colocation"
        ))
        assert result.risk_level == "High"


class TestKnownSectors:
    """Test all predefined sectors in NGFS_SECTOR_RISKS."""

    @pytest.mark.parametrize("sector,expected_risk", [
        ("data centre", "High"),
        ("digital infrastructure", "High"),
        ("oil & gas", "Critical"),
        ("utilities", "Medium"),
        ("real estate", "Medium"),
        ("manufacturing", "High"),
    ])
    def test_known_sector_risk_levels(self, sector, expected_risk):
        """Known sectors should return expected risk levels."""
        result = assess_transition_risk(TransitionRiskInput(sector=sector))
        assert result.risk_level == expected_risk


class TestNGFSScenario:
    """Test NGFS scenario field."""

    def test_default_scenario_is_net_zero_2050(self):
        """Default scenario should be Net Zero 2050."""
        result = assess_transition_risk(TransitionRiskInput(sector="data centre"))
        assert result.ngfs_scenario == "Net Zero 2050"

    def test_unknown_sector_still_has_scenario(self):
        """Unknown sectors should still have a scenario."""
        result = assess_transition_risk(TransitionRiskInput(
            sector="Unknown Sector"
        ))
        assert result.ngfs_scenario == "Net Zero 2050"
