#!/usr/bin/env python3
"""
CADI Pipeline Test - Run tools end-to-end without Claude API.
Tests the full pipeline using hardcoded orchestration.
"""

from pathlib import Path

from rich.console import Console
from rich.panel import Panel

from src.schemas import (
    FloodRiskInput,
    GeocodeInput,
    MapInput,
    ParseDocumentInput,
    TransitionRiskInput,
    BiodiversityInput,
    ReportInput,
)
from src.tools import (
    assess_flood_risk,
    assess_transition_risk,
    check_biodiversity,
    generate_map,
    geocode_address,
    parse_document,
)
from src.report import generate_report

console = Console()


def run_pipeline(pdf_path: str, output_dir: str):
    """Run the full CADI pipeline without Claude API."""

    console.print(Panel.fit("CADI Pipeline Test (No API)", style="bold blue"))

    # Step 1: Parse document
    console.print("\n[cyan]Step 1: Parsing document...[/cyan]")
    doc = parse_document(ParseDocumentInput(pdf_path=pdf_path))
    console.print(f"  [green]OK[/green] Company: {doc.company_name}")
    console.print(f"  [green]OK[/green] Sector: {doc.sector}")
    console.print(f"  [green]OK[/green] Assets: {len(doc.assets)}")

    # Step 2: Geocode assets
    console.print("\n[cyan]Step 2: Geocoding assets...[/cyan]")
    for asset in doc.assets:
        geo = geocode_address(GeocodeInput(address=asset.address))
        asset.latitude = geo.latitude
        asset.longitude = geo.longitude
        console.print(f"  [green]OK[/green] {asset.name}: ({geo.latitude:.4f}, {geo.longitude:.4f})")

    # Step 3: Assess flood risk
    console.print("\n[cyan]Step 3: Assessing flood risk...[/cyan]")
    flood_results = []
    for asset in doc.assets:
        flood = assess_flood_risk(FloodRiskInput(
            latitude=asset.latitude,
            longitude=asset.longitude,
            asset_name=asset.name,
        ))
        flood_results.append(flood)
        console.print(f"  [green]OK[/green] {asset.name}: {flood.risk_level} (rp100={flood.depths.rp100}m)")

    # Step 4: Assess transition risk
    console.print("\n[cyan]Step 4: Assessing transition risk...[/cyan]")
    transition = assess_transition_risk(TransitionRiskInput(sector=doc.sector or "data centre"))
    console.print(f"  [green]OK[/green] Sector: {transition.sector}")
    console.print(f"  [green]OK[/green] Risk Level: {transition.risk_level}")

    # Step 5: Check biodiversity
    console.print("\n[cyan]Step 5: Checking biodiversity...[/cyan]")
    bio_results = []
    for asset in doc.assets:
        bio = check_biodiversity(BiodiversityInput(
            latitude=asset.latitude,
            longitude=asset.longitude,
            asset_name=asset.name,
        ))
        bio_results.append(bio)
        flag = "WARN" if bio.risk_flag else "OK"
        console.print(f"  [green]OK[/green] {asset.name}: {bio.nearest_protected_area} ({bio.distance_km}km) [{flag}]")

    # Step 6: Generate map
    console.print("\n[cyan]Step 6: Generating map...[/cyan]")
    Path(output_dir).mkdir(parents=True, exist_ok=True)
    map_result = generate_map(MapInput(
        assets=[a for a in doc.assets],
        flood_risks=[f.model_dump() for f in flood_results],
        output_path=f"{output_dir}/map.html",
    ))
    console.print(f"  [green]OK[/green] Map saved: {map_result.map_path}")

    # Step 7: Generate report
    console.print("\n[cyan]Step 7: Generating report...[/cyan]")

    # Identify ESG gaps
    esg_gaps = [
        "Scope 2 emissions not disclosed",
        "Water usage reporting vague ('industry standard')",
        "Renewable energy plan aspirational, not committed",
    ]

    # Identify red flags
    red_flags = []
    for fr in flood_results:
        if fr.risk_level in ["High", "Critical"]:
            red_flags.append(f"{fr.asset_name}: {fr.risk_level} flood risk")
    if transition.risk_level == "High":
        red_flags.append("High transition risk sector")

    report = generate_report(ReportInput(
        company_name=doc.company_name,
        deal_overview={
            "Valuation": f"RM {doc.valuation_myr}M" if doc.valuation_myr else "N/A",
            "Deal Type": doc.deal_type or "N/A",
            "Target IRR": doc.target_irr or "N/A",
        },
        assets=[a for a in doc.assets],
        flood_risks=flood_results,
        transition_risk=transition,
        biodiversity=bio_results,
        esg_gaps=esg_gaps,
        red_flags=red_flags,
        output_format="html",
        output_path=f"{output_dir}/memo",
    ))
    console.print(f"  [green]OK[/green] Report saved: {report.report_path}")

    # Summary
    console.print()
    console.print(Panel.fit(
        f"[bold green]Pipeline Complete[/bold green]\n\n"
        f"Company: {doc.company_name}\n"
        f"Assets: {len(doc.assets)}\n"
        f"Flood Risks: {', '.join(fr.risk_level for fr in flood_results)}\n"
        f"Transition Risk: {transition.risk_level}\n"
        f"ESG Gaps: {len(esg_gaps)}\n"
        f"Red Flags: {len(red_flags)}\n\n"
        f"Outputs:\n"
        f"  - {map_result.map_path}\n"
        f"  - {report.report_path}",
        title="Summary",
    ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CADI Pipeline Test")
    parser.add_argument("--input", "-i", default="data/deal/nusantara_digital.pdf", help="Path to PDF")
    parser.add_argument("--output", "-o", default="output/", help="Output directory")
    args = parser.parse_args()

    run_pipeline(args.input, args.output)
