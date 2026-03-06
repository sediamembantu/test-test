"""
Transition risk assessment using NGFS sector scenarios.
"""

from __future__ import annotations

from ..schemas import TransitionRiskInput, TransitionRiskOutput

# Hardcoded NGFS-aligned transition risk lookup by sector
# Based on NGFS sectoral classifications
NGFS_SECTOR_RISKS = {
    "data centre": {
        "risk_level": "High",
        "key_risks": [
            "High energy intensity",
            "Carbon-intensive power grid dependency",
            "Increasing electricity costs under carbon pricing",
            "Growing regulatory pressure on energy efficiency",
        ],
        "carbon_intensity": "High (typically 400-600 kg CO2/MWh grid-dependent)",
    },
    "digital infrastructure": {
        "risk_level": "High",
        "key_risks": [
            "High energy consumption",
            "E-waste generation",
            "Supply chain carbon footprint",
        ],
        "carbon_intensity": "Medium-High",
    },
    "oil & gas": {
        "risk_level": "Critical",
        "key_risks": [
            "Stranded asset risk",
            "Declining demand under net-zero scenarios",
            "Carbon pricing exposure",
        ],
        "carbon_intensity": "Very High",
    },
    "utilities": {
        "risk_level": "Medium",
        "key_risks": [
            "Transition to renewables required",
            "Coal phase-out risk",
            "Grid modernization costs",
        ],
        "carbon_intensity": "Variable by generation mix",
    },
    "real estate": {
        "risk_level": "Medium",
        "key_risks": [
            "Building energy efficiency requirements",
            "Green building standards",
            "Physical climate risk to properties",
        ],
        "carbon_intensity": "Medium",
    },
    "manufacturing": {
        "risk_level": "High",
        "key_risks": [
            "Industrial decarbonization requirements",
            "Supply chain emissions",
            "Energy cost volatility",
        ],
        "carbon_intensity": "High",
    },
}


def assess_transition_risk(input_data: TransitionRiskInput) -> TransitionRiskOutput:
    """
    Assess transition risk for a given sector using NGFS scenarios.

    Args:
        input_data: TransitionRiskInput with sector

    Returns:
        TransitionRiskOutput with risk level and key factors
    """
    sector = input_data.sector.lower().strip()

    # Try to match sector
    for sector_key, risk_data in NGFS_SECTOR_RISKS.items():
        if sector_key in sector or sector in sector_key:
            return TransitionRiskOutput(
                sector=input_data.sector,
                risk_level=risk_data["risk_level"],
                ngfs_scenario="Net Zero 2050",
                key_risks=risk_data["key_risks"],
                carbon_intensity=risk_data.get("carbon_intensity"),
            )

    # Unknown sector - return conservative estimate
    return TransitionRiskOutput(
        sector=input_data.sector,
        risk_level="Medium",
        ngfs_scenario="Net Zero 2050",
        key_risks=["Sector transition pathway uncertain", "Requires detailed assessment"],
        carbon_intensity=None,
    )
