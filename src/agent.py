"""
CADI Agent - Fixed sequential pipeline (no external API required).
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.panel import Panel

from .schemas import (
    BiodiversityInput,
    FloodRiskInput,
    GeocodeInput,
    MapInput,
    ParseDocumentInput,
    ReportInput,
    TransitionRiskInput,
)
from .report import generate_report
from .tools import (
    assess_flood_risk,
    assess_transition_risk,
    check_biodiversity,
    generate_map,
    geocode_address,
    parse_document,
)

console = Console()


def run_agent(pdf_path: str, output_dir: str) -> dict[str, Any]:
    """
    Run the CADI pipeline on a deal document.

    Executes tools in fixed sequence:
      parse → geocode → flood risk → biodiversity → transition risk → map → report

    Args:
        pdf_path: Path to the deal PDF
        output_dir: Directory for outputs

    Returns:
        Dictionary with pipeline results
    """
    console.print(Panel.fit("CADI - Climate-Aware Deal Intelligence", style="bold blue"))

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    results: dict[str, Any] = {
        "start_time": datetime.now().isoformat(),
        "steps": [],
    }

    # -------------------------------------------------------------------------
    # Step 1: Parse document
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 1/7 — Parsing deal document...[/cyan]")
    doc = parse_document(ParseDocumentInput(pdf_path=pdf_path))
    console.print(f"  Company: [bold]{doc.company_name}[/bold]")
    console.print(f"  Sector:  {doc.sector}")
    console.print(f"  Assets:  {len(doc.assets)} found")
    results["steps"].append({"step": "parse_document", "company": doc.company_name})

    # -------------------------------------------------------------------------
    # Step 2: Geocode each asset
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 2/7 — Geocoding asset locations...[/cyan]")
    geocoded_assets = []

    for asset in doc.assets:
        geo = geocode_address(GeocodeInput(address=asset.address))
        geocoded = asset.model_copy(update={"latitude": geo.latitude, "longitude": geo.longitude})
        geocoded_assets.append(geocoded)
        console.print(
            f"  {asset.name}: {geo.latitude:.4f}, {geo.longitude:.4f} [{geo.source}]"
        )

    if not geocoded_assets:
        geocoded_assets = doc.assets

    results["steps"].append({"step": "geocode", "assets_geocoded": len(geocoded_assets)})

    # -------------------------------------------------------------------------
    # Step 3: Flood risk per asset
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 3/7 — Assessing flood risk...[/cyan]")
    flood_risks = []

    for asset in geocoded_assets:
        if asset.latitude is None or asset.longitude is None:
            continue
        risk = assess_flood_risk(
            FloodRiskInput(
                latitude=asset.latitude,
                longitude=asset.longitude,
                asset_name=asset.name,
            )
        )
        flood_risks.append(risk)
        console.print(
            f"  {asset.name}: [bold]{risk.risk_level}[/bold] "
            f"(RP100={risk.depths.rp100}m)"
        )

    results["steps"].append({
        "step": "flood_risk",
        "assessments": [r.model_dump() for r in flood_risks],
    })

    # -------------------------------------------------------------------------
    # Step 4: Biodiversity check per asset
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 4/7 — Checking protected area proximity...[/cyan]")
    biodiversity_results = []

    for asset in geocoded_assets:
        if asset.latitude is None or asset.longitude is None:
            continue
        bio = check_biodiversity(
            BiodiversityInput(
                latitude=asset.latitude,
                longitude=asset.longitude,
                asset_name=asset.name,
            )
        )
        biodiversity_results.append(bio)
        flag = "[red]FLAG[/red]" if bio.risk_flag else "[green]OK[/green]"
        console.print(
            f"  {asset.name}: {flag} — {bio.nearest_protected_area} "
            f"({bio.distance_km} km)"
        )

    results["steps"].append({
        "step": "biodiversity",
        "assessments": [b.model_dump() for b in biodiversity_results],
    })

    # -------------------------------------------------------------------------
    # Step 5: Transition risk
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 5/7 — Assessing transition risk...[/cyan]")
    sector = doc.sector or "data centre"
    transition = assess_transition_risk(TransitionRiskInput(sector=sector))
    console.print(
        f"  Sector: {transition.sector} → [bold]{transition.risk_level}[/bold] "
        f"({transition.ngfs_scenario})"
    )

    results["steps"].append({
        "step": "transition_risk",
        "assessment": transition.model_dump(),
    })

    # -------------------------------------------------------------------------
    # Step 6: Generate map
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 6/7 — Generating interactive map...[/cyan]")
    map_path = str(output_path / "map.html")
    flood_dicts = [r.model_dump() for r in flood_risks]
    map_result = generate_map(
        MapInput(
            assets=geocoded_assets,
            flood_risks=flood_dicts,
            flood_data=True,
            output_path=map_path,
        )
    )
    console.print(f"  Map saved → {map_result.map_path}")

    results["steps"].append({"step": "generate_map", "path": map_result.map_path})

    # -------------------------------------------------------------------------
    # Step 7: Generate report
    # -------------------------------------------------------------------------
    console.print("\n[cyan]Step 7/7 — Generating due diligence memo...[/cyan]")

    esg_gaps = _identify_esg_gaps(doc.raw_text)
    red_flags = _identify_red_flags(flood_risks, biodiversity_results, doc.raw_text)

    deal_overview = {
        "company_registration": doc.company_registration,
        "headquarters": doc.headquarters,
        "deal_type": doc.deal_type,
        "valuation_myr": doc.valuation_myr,
        "target_irr": doc.target_irr,
        "financials": doc.financials.model_dump(),
    }

    report = generate_report(
        ReportInput(
            company_name=doc.company_name,
            deal_overview=deal_overview,
            assets=geocoded_assets,
            flood_risks=flood_risks,
            transition_risk=transition,
            biodiversity=biodiversity_results,
            esg_gaps=esg_gaps,
            red_flags=red_flags,
            output_format="html",
            output_path=str(output_path / "memo"),
        )
    )
    console.print(f"  Memo saved → {report.report_path}")

    results["steps"].append({"step": "generate_report", "path": report.report_path})
    results["end_time"] = datetime.now().isoformat()

    console.print(
        Panel.fit(
            f"[green]Done![/green]  Memo: {report.report_path}  |  Map: {map_result.map_path}",
            style="bold green",
        )
    )
    return results


def _identify_esg_gaps(raw_text: str) -> list[str]:
    """Identify ESG disclosure gaps from document text."""
    gaps = []
    text_lower = raw_text.lower()

    if "scope 2" not in text_lower and "scope2" not in text_lower:
        gaps.append("Scope 2 emissions not disclosed")
    if "scope 1" not in text_lower:
        gaps.append("Scope 1 emissions not disclosed")
    if "water" not in text_lower or "cooling" not in text_lower:
        gaps.append("Water consumption / cooling methodology not quantified")
    if "renewable" not in text_lower and "solar" not in text_lower:
        gaps.append("No confirmed renewable energy procurement plan")
    if "esg" not in text_lower and "sustainability" not in text_lower:
        gaps.append("No standalone ESG policy referenced")

    return gaps


def _identify_red_flags(flood_risks, biodiversity_results, raw_text: str) -> list[str]:
    """Compile red flags from risk assessments."""
    flags = []

    for risk in flood_risks:
        if risk.risk_level in ("High", "Critical"):
            flags.append(
                f"{risk.asset_name}: {risk.risk_level} flood risk "
                f"(RP100 depth = {risk.depths.rp100}m)"
            )

    for bio in biodiversity_results:
        if bio.risk_flag:
            flags.append(
                f"{bio.asset_name}: {bio.distance_km} km from "
                f"{bio.nearest_protected_area} ({bio.protected_area_type})"
            )

    text_lower = raw_text.lower()
    if "fossil" in text_lower or "tnb" in text_lower:
        flags.append("Power supply dependent on fossil-fuel-heavy national grid (TNB ~60% fossil)")
    if "under construction" in text_lower or "phase 2" in text_lower:
        flags.append("Phase 2 construction not yet complete — execution risk on capacity expansion")

    return flags


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="CADI Agent")
    parser.add_argument("--input", "-i", required=True, help="Path to deal PDF")
    parser.add_argument("--output", "-o", default="output/", help="Output directory")
    args = parser.parse_args()

    results = run_agent(args.input, args.output)

    output_path = Path(args.output)
    results_file = output_path / "agent_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    console.print(f"\n[dim]Full results → {results_file}[/dim]")


if __name__ == "__main__":
    main()
