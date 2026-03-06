#!/usr/bin/env python3
"""
Generate fictional Nusantara Digital Sdn Bhd deal document for CADI demo.
Creates a realistic-looking investment memorandum PDF.
"""

from pathlib import Path

from fpdf import FPDF


class DealPDF(FPDF):
    """Custom PDF class for deal document."""

    def header(self):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(100, 100, 100)
        self.cell(0, 10, "CONFIDENTIAL - Investment Memorandum", 0, 1, "R")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "I", 8)
        self.set_text_color(128, 128, 128)
        self.cell(0, 10, f"Nusantara Digital Sdn Bhd - Investment Proposal | Page {self.page_no()}", 0, 0, "C")

    def chapter_title(self, title: str):
        self.set_font("Helvetica", "B", 14)
        self.set_text_color(26, 54, 93)
        self.cell(0, 10, title, 0, 1, "L")
        self.ln(2)

    def section_title(self, title: str):
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(44, 82, 130)
        self.cell(0, 8, title, 0, 1, "L")
        self.ln(1)

    def body_text(self, text: str):
        self.set_font("Helvetica", "", 10)
        self.set_text_color(45, 55, 72)
        self.multi_cell(0, 5, text)
        self.ln(2)

    def key_value(self, key: str, value: str):
        self.set_font("Helvetica", "B", 10)
        self.set_text_color(45, 55, 72)
        self.cell(60, 6, key + ":", 0, 0, "L")
        self.set_font("Helvetica", "", 10)
        self.cell(0, 6, value, 0, 1, "L")


def generate_deal_pdf(output_path: str = "data/deal/nusantara_digital.pdf"):
    """Generate the Nusantara Digital deal PDF."""

    pdf = DealPDF()
    pdf.set_auto_page_break(auto=True, margin=20)

    # =========================================================================
    # Page 1: Cover Page
    # =========================================================================
    pdf.add_page()
    pdf.ln(40)
    pdf.set_font("Helvetica", "B", 24)
    pdf.set_text_color(26, 54, 93)
    pdf.cell(0, 15, "INVESTMENT MEMORANDUM", 0, 1, "C")

    pdf.ln(10)
    pdf.set_font("Helvetica", "B", 20)
    pdf.set_text_color(44, 82, 130)
    pdf.cell(0, 12, "Nusantara Digital Sdn Bhd", 0, 1, "C")

    pdf.ln(5)
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(100, 100, 100)
    pdf.cell(0, 8, "300MW Data Centre Campus - Malaysia", 0, 1, "C")

    pdf.ln(20)
    pdf.set_font("Helvetica", "", 11)
    pdf.cell(0, 6, "Proposed Equity Investment", 0, 1, "C")
    pdf.cell(0, 6, "RM 840 Million (30% Stake)", 0, 1, "C")

    pdf.ln(30)
    pdf.set_font("Helvetica", "I", 10)
    pdf.set_text_color(128, 128, 128)
    pdf.cell(0, 6, "Prepared by: GP Advisors Sdn Bhd", 0, 1, "C")
    pdf.cell(0, 6, "Date: March 2026", 0, 1, "C")
    pdf.cell(0, 6, "CONFIDENTIAL", 0, 1, "C")

    # =========================================================================
    # Page 2: Executive Summary
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("1. Executive Summary")

    pdf.body_text(
        "Nusantara Digital Sdn Bhd (\"NDSB\" or the \"Company\") is a Malaysia-based data centre "
        "developer and operator, currently developing a 300MW hyperscale data centre campus across "
        "two strategic locations in Malaysia. The Company has secured a 15-year anchor tenant agreement "
        "with CloudAsia, a fictional hyperscaler, providing strong revenue visibility."
    )

    pdf.body_text(
        "This memorandum presents an opportunity to acquire a 30% equity stake in NDSB at a pre-money "
        "valuation of RM 2.8 billion, with a targeted IRR of 12-15% over a 10-year investment horizon."
    )

    pdf.section_title("Investment Highlights")
    pdf.body_text(
        "- Strong anchor tenant: 15-year lease with CloudAsia (hyperscaler)\n"
        "- Strategic locations: Kulai (Johor) and Cyberjaya (Selangor) DC corridors\n"
        "- Phased development: 150MW operational, 150MW under construction\n"
        "- Attractive economics: Target IRR of 12-15%\n"
        "- Growing market: Malaysia positioned as SEA data centre hub"
    )

    pdf.section_title("Key Risks")
    pdf.body_text(
        "- Physical climate risk: Kulai site in flood-prone area\n"
        "- Transition risk: High energy intensity, grid carbon exposure\n"
        "- ESG disclosure gaps: Scope 2 emissions not reported\n"
        "- Concentration risk: Single anchor tenant"
    )

    # =========================================================================
    # Page 3: Company Overview
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("2. Company Overview")

    pdf.section_title("Corporate Profile")
    pdf.key_value("Company Name", "Nusantara Digital Sdn Bhd")
    pdf.key_value("SSM Registration", "202401012345")
    pdf.key_value("Sector", "Data Centre / Digital Infrastructure")
    pdf.key_value("Founded", "2023")
    pdf.key_value("Headquarters", "Kuala Lumpur, Malaysia")
    pdf.key_value("Employees", "85 full-time")

    pdf.ln(5)
    pdf.section_title("Shareholding Structure (Pre-Investment)")
    pdf.body_text(
        "- Nusantara Holdings Sdn Bhd: 60%\n"
        "- TechVenture Capital: 25%\n"
        "- Management Team: 15%"
    )

    pdf.section_title("Management Team")
    pdf.body_text(
        "CEO: Ahmad Razak (formerly VP Operations at YTL Data Centre)\n"
        "CTO: Sarah Lim (formerly Head of Infrastructure at AWS APAC)\n"
        "CFO: David Tan (formerly Director at Goldman Sachs Singapore)"
    )

    # =========================================================================
    # Page 4: Deal Terms
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("3. Deal Terms")

    pdf.section_title("Transaction Summary")
    pdf.key_value("Deal Type", "Primary Equity Investment")
    pdf.key_value("Stake Acquired", "30%")
    pdf.key_value("Pre-money Valuation", "RM 2.8 billion")
    pdf.key_value("Investment Amount", "RM 840 million")
    pdf.key_value("Target IRR", "12-15% over 10 years")
    pdf.key_value("Exit Strategy", "Trade sale / IPO (Year 7-10)")

    pdf.ln(5)
    pdf.section_title("Use of Proceeds")
    pdf.body_text(
        "- Phase 2 construction (Kulai): RM 450 million\n"
        "- DR site expansion (Cyberjaya): RM 200 million\n"
        "- Working capital: RM 100 million\n"
        "- Corporate purposes: RM 90 million"
    )

    pdf.section_title("Anchor Tenant")
    pdf.body_text(
        "CloudAsia (fictional hyperscaler) has signed a 15-year lease agreement for:\n"
        "- 100MW at Kulai campus (Phase 1)\n"
        "- 50MW at Cyberjaya DR site\n"
        "- Option to expand to additional 100MW (Phase 2)"
    )

    # =========================================================================
    # Page 5: Physical Assets
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("4. Physical Assets")

    pdf.section_title("4.1 Primary Campus - Kulai, Johor")
    pdf.key_value("Address", "Lot 1234, Jalan Perindustrian Kulai, 81000 Kulai, Johor")
    pdf.key_value("Total Capacity", "250MW")
    pdf.key_value("Phase 1 Status", "100MW operational (since Q2 2025)")
    pdf.key_value("Phase 2 Status", "150MW under construction (COD Q4 2026)")
    pdf.key_value("Land Area", "25 acres")
    pdf.key_value("Coordinates", "1.6580° N, 103.6000° E")

    pdf.ln(3)
    pdf.body_text(
        "The Kulai campus is located in Johor's emerging data centre corridor, approximately "
        "15km from the Singapore border. The site benefits from proximity to Tuas subsea cable "
        "landing stations and TNB's 500kV transmission network."
    )

    pdf.ln(5)
    pdf.section_title("4.2 DR Site - Cyberjaya, Selangor")
    pdf.key_value("Address", "Block C, Cyberjaya Technology Park, 63000 Cyberjaya, Selangor")
    pdf.key_value("Total Capacity", "50MW")
    pdf.key_value("Status", "Operational (since Q4 2024)")
    pdf.key_value("Land Area", "5 acres")
    pdf.key_value("Coordinates", "2.9228° N, 101.6538° E")

    pdf.ln(3)
    pdf.body_text(
        "The Cyberjaya site serves as a disaster recovery facility and secondary compute location. "
        "Located in Malaysia's established tech hub with excellent fiber connectivity and lower "
        "flood risk compared to the Kulai site."
    )

    # =========================================================================
    # Page 6: Financial Projections
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("5. Financial Projections")

    pdf.section_title("Historical & Projected Financials (RM millions)")

    # Table header
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_fill_color(237, 242, 247)
    pdf.cell(50, 8, "Metric", 1, 0, "L", True)
    pdf.cell(35, 8, "2023 (A)", 1, 0, "C", True)
    pdf.cell(35, 8, "2024 (A)", 1, 0, "C", True)
    pdf.cell(35, 8, "2025 (P)", 1, 0, "C", True)
    pdf.cell(35, 8, "2026 (P)", 1, 1, "C", True)

    # Table rows
    pdf.set_font("Helvetica", "", 9)
    data = [
        ("Revenue", "180", "420", "680", "950"),
        ("EBITDA", "72", "185", "310", "450"),
        ("EBITDA Margin", "40%", "44%", "46%", "47%"),
        ("Capex", "800", "650", "400", "300"),
        ("Net Debt", "650", "480", "280", "50"),
        ("Occupancy Rate", "65%", "78%", "90%", "92%"),
    ]

    for row in data:
        pdf.cell(50, 7, row[0], 1, 0, "L")
        pdf.cell(35, 7, row[1], 1, 0, "C")
        pdf.cell(35, 7, row[2], 1, 0, "C")
        pdf.cell(35, 7, row[3], 1, 0, "C")
        pdf.cell(35, 7, row[4], 1, 1, "C")

    pdf.ln(5)
    pdf.section_title("Key Assumptions")
    pdf.body_text(
        "- Revenue growth driven by Phase 2 ramp-up and CloudAsia expansion\n"
        "- EBITDA margin improvement from operational leverage\n"
        "- Capex declines post-Phase 2 completion\n"
        "- Net debt reduction through operating cash flow"
    )

    # =========================================================================
    # Page 7: ESG Profile
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("6. ESG Profile")

    pdf.section_title("Environmental")
    pdf.key_value("Power Source", "TNB Grid (Malaysia ~60% fossil fuel)")
    pdf.key_value("PUE (Power Usage Effectiveness)", "1.45 (target 1.35 by 2027)")
    pdf.key_value("Scope 1 Emissions", "Minimal (diesel backup only)")
    pdf.key_value("Scope 2 Emissions", "Not disclosed")
    pdf.key_value("Water Usage", "\"Industry standard\" (vague)")
    pdf.key_value("Renewable Energy Plan", "20MW rooftop solar \"under consideration\"")

    pdf.ln(5)
    pdf.section_title("Environmental Considerations")
    pdf.body_text(
        "- High grid carbon intensity (TNB ~450g CO2/kWh) creates transition risk\n"
        "- Scope 2 emissions disclosure gap should be addressed\n"
        "- Water usage for cooling needs clarification (evaporative vs. recirculating)\n"
        "- Renewable energy plan is aspirational, not committed"
    )

    pdf.ln(5)
    pdf.section_title("Proximity to Sensitive Areas")
    pdf.body_text(
        "The Kulai campus is located approximately 12km from Sungai Skudai wetlands, "
        "a potential Ramsar site candidate. Environmental impact assessment (EIA) was "
        "conducted and approved by DOE Johor in 2023."
    )

    pdf.section_title("Social & Governance")
    pdf.body_text(
        "- 85 full-time employees, 70% Malaysian nationals\n"
        "- Board: 5 directors, 1 independent\n"
        "- No material governance concerns identified\n"
        "- DEI initiatives: 40% female workforce, target 50% by 2027"
    )

    # =========================================================================
    # Page 8: Risk Factors
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("7. Risk Factors")

    pdf.section_title("Physical Climate Risk")
    pdf.body_text(
        "The Kulai site is located in a low-lying area with moderate flood exposure. "
        "Historical flooding events in Johor (2006-2007, 2019) affected nearby areas. "
        "The site has been elevated 2 meters above surrounding grade and includes "
        "flood barriers and drainage systems. However, climate change may increase "
        "flood frequency and severity.\n\n"
        "Recommendation: Commission detailed flood risk study using JRC data or local sources."
    )

    pdf.section_title("Transition Risk")
    pdf.body_text(
        "Data centres are energy-intensive assets with significant carbon footprints. "
        "Malaysia's grid is ~60% fossil fuel, creating Scope 2 emissions exposure. "
        "Under carbon pricing scenarios (domestic or supply chain requirements), "
        "operating costs may increase significantly.\n\n"
        "Recommendation: Develop renewable energy procurement strategy."
    )

    pdf.section_title("Tenant Concentration Risk")
    pdf.body_text(
        "CloudAsia represents 100% of current occupancy. While the 15-year lease "
        "provides revenue certainty, loss of this tenant would severely impact "
        "financial performance.\n\n"
        "Recommendation: Diversify tenant base in Phase 2."
    )

    # =========================================================================
    # Page 9: Appendices
    # =========================================================================
    pdf.add_page()
    pdf.chapter_title("8. Appendices")

    pdf.section_title("Appendix A: Location Maps")
    pdf.body_text("Detailed site maps and coordinates available upon request.")

    pdf.section_title("Appendix B: Technical Specifications")
    pdf.body_text(
        "- Tier III design (Uptime Institute certified)\n"
        "- N+1 cooling redundancy\n"
        "- 2N power distribution\n"
        "- Carrier-neutral facility (5 fiber providers on-site)"
    )

    pdf.section_title("Appendix C: Regulatory Approvals")
    pdf.body_text(
        "- MCMC Data Centre License: Approved (2024)\n"
        "- DOE EIA Approval: Approved (2023)\n"
        "- Local Council Development Order: Approved (2023)"
    )

    pdf.section_title("Appendix D: Contact Information")
    pdf.body_text(
        "Investor Relations:\n"
        "David Tan, CFO\n"
        "Email: david.tan@nusantaradigital.my\n"
        "Phone: +60 12 345 6789"
    )

    # =========================================================================
    # Disclaimer
    # =========================================================================
    pdf.ln(20)
    pdf.set_font("Helvetica", "I", 8)
    pdf.set_text_color(128, 128, 128)
    pdf.multi_cell(
        0,
        4,
        "DISCLAIMER: This document is for informational purposes only and does not constitute "
        "an offer to sell or solicitation to buy securities. All projections are based on management "
        "estimates and involve significant uncertainty. Past performance is not indicative of future "
        "results. ALL DATA IN THIS DOCUMENT IS FICTIONAL AND FOR DEMONSTRATION PURPOSES ONLY.",
    )

    # Save PDF
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    pdf.output(str(output))
    print(f"Generated: {output}")
    return str(output)


if __name__ == "__main__":
    generate_deal_pdf()
