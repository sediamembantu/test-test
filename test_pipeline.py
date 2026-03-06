#!/usr/bin/env python3
"""
CADI Pipeline Test - Run tools end-to-end without Claude API.
Tests the full pipeline using hardcoded orchestration.
"""

import time
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

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
    
    start_time = time.time()

    console.print(Panel.fit("CADI Pipeline Test (No API)", style="bold blue"))
    
    steps = [
        ("Parsing document", "Extracting company info, assets, financials..."),
        ("Geocoding assets", "Converting addresses to coordinates..."),
        ("Assessing flood risk", "Querying JRC flood maps..."),
        ("Assessing transition risk", "Looking up NGFS sector data..."),
        ("Checking biodiversity", "Querying WDPA protected areas..."),
        ("Generating map", "Creating interactive Folium map..."),
        ("Generating report", "Building due diligence memo..."),
    ]

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TaskProgressColumn(),
        console=console,
    ) as progress:
        
        task = progress.add_task("[cyan]Overall Progress", total=len(steps))

        # Step 1: Parse document
        progress.update(task, description=steps[0][0])
        console.print(f"\n[bold cyan]Step 1: {steps[0][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[0][1]}[/dim]")
        doc = parse_document(ParseDocumentInput(pdf_path=pdf_path))
        console.print(f"  [green]OK[/green] Company: {doc.company_name}")
        console.print(f"  [green]OK[/green] Sector: {doc.sector}")
        console.print(f"  [green]OK[/green] Assets: {len(doc.assets)}")
        progress.advance(task)

        # Step 2: Geocode assets
        progress.update(task, description=steps[1][0])
        console.print(f"\n[bold cyan]Step 2: {steps[1][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[1][1]}[/dim]")
        for asset in doc.assets:
            geo = geocode_address(GeocodeInput(address=asset.address))
            asset.latitude = geo.latitude
            asset.longitude = geo.longitude
            console.print(f"  [green]OK[/green] {asset.name}: ({geo.latitude:.4f}, {geo.longitude:.4f})")
        progress.advance(task)

        # Step 3: Assess flood risk
        progress.update(task, description=steps[2][0])
        console.print(f"\n[bold cyan]Step 3: {steps[2][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[2][1]}[/dim]")
        flood_results = []
        for asset in doc.assets:
            flood = assess_flood_risk(FloodRiskInput(
                latitude=asset.latitude,
                longitude=asset.longitude,
                asset_name=asset.name,
            ))
            flood_results.append(flood)
            console.print(f"  [green]OK[/green] {asset.name}: {flood.risk_level} (rp100={flood.depths.rp100}m)")
        progress.advance(task)

        # Step 4: Assess transition risk
        progress.update(task, description=steps[3][0])
        console.print(f"\n[bold cyan]Step 4: {steps[3][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[3][1]}[/dim]")
        transition = assess_transition_risk(TransitionRiskInput(sector=doc.sector or "data centre"))
        console.print(f"  [green]OK[/green] Sector: {transition.sector}")
        console.print(f"  [green]OK[/green] Risk Level: {transition.risk_level}")
        progress.advance(task)

        # Step 5: Check biodiversity
        progress.update(task, description=steps[4][0])
        console.print(f"\n[bold cyan]Step 5: {steps[4][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[4][1]}[/dim]")
        bio_results = []
        for asset in doc.assets:
            bio = check_biodiversity(BiodiversityInput(
                latitude=asset.latitude,
                longitude=asset.longitude,
                asset_name=asset.name,
            ))
            bio_results.append(bio)
            flag = "[yellow]WARN[/yellow]" if bio.risk_flag else "[green]OK[/green]"
            console.print(f"  [green]OK[/green] {asset.name}: {bio.nearest_protected_area} ({bio.distance_km}km) [{flag}]")
        progress.advance(task)

        # Step 6: Generate map
        progress.update(task, description=steps[5][0])
        console.print(f"\n[bold cyan]Step 6: {steps[5][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[5][1]}[/dim]")
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        map_result = generate_map(MapInput(
            assets=[a for a in doc.assets],
            flood_risks=[f.model_dump() for f in flood_results],
            output_path=f"{output_dir}/map.html",
        ))
        console.print(f"  [green]OK[/green] Map saved: {map_result.map_path}")
        progress.advance(task)

        # Step 7: Generate report
        progress.update(task, description=steps[6][0])
        console.print(f"\n[bold cyan]Step 7: {steps[6][0]}...[/bold cyan]")
        console.print(f"[dim]{steps[6][1]}[/dim]")

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
        progress.advance(task)

    # Summary
    elapsed = time.time() - start_time
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
        f"  - {report.report_path}\n\n"
        f"[dim]Elapsed: {elapsed:.2f}s[/dim]",
        title="Summary",
    ))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CADI Pipeline Test")
    parser.add_argument("--input", "-i", default="data/deal/nusantara_digital.pdf", help="Path to PDF")
    parser.add_argument("--output", "-o", default="output/", help="Output directory")
    args = parser.parse_args()

    run_pipeline(args.input, args.output)
