"""
CADI Agent - Main orchestration loop using Claude API tool-calling.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path
from typing import Any

from anthropic import Anthropic
from rich.console import Console
from rich.panel import Panel

from .schemas import (
    Asset,
    BiodiversityInput,
    FloodRiskInput,
    GeocodeInput,
    MapInput,
    ParseDocumentInput,
    ReportInput,
    TransitionRiskInput,
)
from .tools import (
    assess_flood_risk,
    assess_transition_risk,
    check_biodiversity,
    generate_map,
    geocode_address,
    parse_document,
)
from .report import generate_report

console = Console()

# System prompt for the agent
SYSTEM_PROMPT = """You are CADI, a Climate-Aware Deal Intelligence agent.

Your role is to analyze private equity deal documents and produce climate-integrated due diligence assessments.

## Workflow

1. Parse the deal PDF to extract company info, assets, and financials
2. For each physical asset:
   - Geocode the address to get coordinates
   - Assess flood risk using JRC data
   - Check proximity to protected areas
3. Assess transition risk for the company's sector
4. Identify ESG gaps and red flags
5. Generate an interactive map
6. Produce a structured due diligence memo

## Tool Selection Logic

- Start with parse_document to understand the deal
- If physical assets found → geocode each, then assess climate risks
- If no physical assets → skip climate layer, focus on transition risk
- Always check for ESG disclosure gaps

## Output

Provide a concise summary of findings after tool execution.

## Important

- All data is fictional for demo purposes
- If a tool fails, note the issue and continue with available information
- Be thorough but efficient - this is a 2-minute demo
"""

# Tool definitions for Claude API
TOOL_DEFINITIONS = [
    {
        "name": "parse_document",
        "description": "Parse a PDF deal document and extract key information",
        "input_schema": {
            "type": "object",
            "properties": {
                "pdf_path": {"type": "string", "description": "Path to PDF file"}
            },
            "required": ["pdf_path"],
        },
    },
    {
        "name": "geocode_address",
        "description": "Convert an address to latitude/longitude coordinates",
        "input_schema": {
            "type": "object",
            "properties": {
                "address": {"type": "string", "description": "Address to geocode"}
            },
            "required": ["address"],
        },
    },
    {
        "name": "assess_flood_risk",
        "description": "Assess flood risk at a location using JRC flood maps",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Latitude coordinate"},
                "longitude": {"type": "number", "description": "Longitude coordinate"},
                "asset_name": {"type": "string", "description": "Name of asset"},
            },
            "required": ["latitude", "longitude", "asset_name"],
        },
    },
    {
        "name": "assess_transition_risk",
        "description": "Assess transition risk for a sector using NGFS scenarios",
        "input_schema": {
            "type": "object",
            "properties": {
                "sector": {"type": "string", "description": "Industry sector"},
                "subsector": {"type": "string", "description": "Subsector (optional)"},
            },
            "required": ["sector"],
        },
    },
    {
        "name": "check_biodiversity",
        "description": "Check proximity to protected areas",
        "input_schema": {
            "type": "object",
            "properties": {
                "latitude": {"type": "number", "description": "Latitude coordinate"},
                "longitude": {"type": "number", "description": "Longitude coordinate"},
                "asset_name": {"type": "string", "description": "Asset name"},
            },
            "required": ["latitude", "longitude", "asset_name"],
        },
    },
    {
        "name": "generate_map",
        "description": "Generate an interactive map with asset markers",
        "input_schema": {
            "type": "object",
            "properties": {
                "assets": {"type": "array", "description": "List of assets with coordinates"},
                "flood_data": {"type": "boolean", "description": "Include flood overlay"},
                "output_path": {"type": "string", "description": "Output HTML path"},
            },
            "required": ["assets"],
        },
    },
    {
        "name": "generate_report",
        "description": "Generate the final due diligence memo",
        "input_schema": {
            "type": "object",
            "properties": {
                "company_name": {"type": "string"},
                "deal_overview": {"type": "object"},
                "assets": {"type": "array"},
                "flood_risks": {"type": "array"},
                "transition_risk": {"type": "object"},
                "esg_gaps": {"type": "array", "items": {"type": "string"}},
                "red_flags": {"type": "array", "items": {"type": "string"}},
            },
            "required": ["company_name"],
        },
    },
]

# Tool implementation mapping
TOOLS: dict[str, callable] = {
    "parse_document": lambda args: parse_document(ParseDocumentInput(**args)).model_dump(),
    "geocode_address": lambda args: geocode_address(GeocodeInput(**args)).model_dump(),
    "assess_flood_risk": lambda args: assess_flood_risk(FloodRiskInput(**args)).model_dump(),
    "assess_transition_risk": lambda args: assess_transition_risk(TransitionRiskInput(**args)).model_dump(),
    "check_biodiversity": lambda args: check_biodiversity(BiodiversityInput(**args)).model_dump(),
    "generate_map": lambda args: generate_map(MapInput(**args)).model_dump(),
    "generate_report": lambda args: generate_report(ReportInput(**args)).model_dump(),
}


def run_agent(pdf_path: str, output_dir: str, dry_run: bool = False) -> dict[str, Any]:
    """
    Run the CADI agent on a deal document.

    Args:
        pdf_path: Path to the deal PDF
        output_dir: Directory for outputs
        dry_run: If True, don't execute tools (for testing)

    Returns:
        Dictionary with agent results
    """
    console.print(Panel.fit("⚔️ CADI - Climate-Aware Deal Intelligence", style="bold blue"))

    client = Anthropic()
    messages: list[dict] = []

    # Initial message with PDF path
    user_message = f"""Analyze this deal document and produce a climate-integrated due diligence assessment.

Document path: {pdf_path}

Output directory: {output_dir}

Follow the workflow: parse → geocode assets → assess risks → generate map and report.
"""

    messages.append({"role": "user", "content": user_message})

    # Agent loop
    collected_results: dict[str, Any] = {
        "start_time": datetime.now().isoformat(),
        "tool_calls": [],
        "findings": {},
    }

    while True:
        console.print("\n[cyan]→ Calling Claude...[/cyan]")

        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4096,
            system=SYSTEM_PROMPT,
            tools=TOOL_DEFINITIONS,
            messages=messages,
        )

        # Check stop reason
        if response.stop_reason == "end_turn":
            # Agent is done
            console.print("\n[green]✓ Agent complete[/green]")
            break

        # Process tool calls
        assistant_content = []
        tool_results = []

        for block in response.content:
            if block.type == "text":
                console.print(f"\n[white]{block.text}[/white]")
                assistant_content.append({"type": "text", "text": block.text})

            elif block.type == "tool_use":
                tool_name = block.name
                tool_input = block.input
                tool_id = block.id

                console.print(f"\n[yellow]🔧 Tool: {tool_name}[/yellow]")
                console.print(f"[dim]{json.dumps(tool_input, indent=2)}[/dim]")

                assistant_content.append({
                    "type": "tool_use",
                    "id": tool_id,
                    "name": tool_name,
                    "input": tool_input,
                })

                # Execute tool
                if dry_run:
                    result = {"status": "dry_run", "input": tool_input}
                elif tool_name in TOOLS:
                    try:
                        result = TOOLS[tool_name](tool_input)
                    except Exception as e:
                        result = {"error": str(e)}
                else:
                    result = {"error": f"Unknown tool: {tool_name}"}

                console.print(f"[green]← Result:[/green] {json.dumps(result, indent=2, default=str)[:500]}...")

                collected_results["tool_calls"].append({
                    "tool": tool_name,
                    "input": tool_input,
                    "result": result,
                })

                tool_results.append({
                    "type": "tool_result",
                    "tool_use_id": tool_id,
                    "content": json.dumps(result, default=str),
                })

        # Append assistant message and tool results
        messages.append({"role": "assistant", "content": assistant_content})
        if tool_results:
            messages.append({"role": "user", "content": tool_results})

    collected_results["end_time"] = datetime.now().isoformat()
    return collected_results


def run_agent_sse(pdf_path: str, output_dir: str):
    """
    Run the CADI pipeline and yield Server-Sent Events.
    
    Generator function for FastAPI SSE endpoint.
    Yields JSON events with step progress and final results.
    
    Args:
        pdf_path: Path to the deal PDF
        output_dir: Directory for outputs
        
    Yields:
        dict: SSE event data with step, total, message, done fields
    """
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    total_steps = 7
    
    # Step 1: Parse document
    yield {"step": 1, "total": total_steps, "message": "Parsing deal document...", "done": False}
    doc = parse_document(ParseDocumentInput(pdf_path=pdf_path))
    yield {
        "step": 1, 
        "total": total_steps, 
        "message": f"✓ Parsed: {doc.company_name} | Sector: {doc.sector} | Assets: {len(doc.assets)}",
        "done": False
    }
    
    # Step 2: Geocode assets
    yield {"step": 2, "total": total_steps, "message": "Geocoding asset locations...", "done": False}
    geocoded_assets = []
    for asset in doc.assets:
        geo = geocode_address(GeocodeInput(address=asset.address))
        geocoded = asset.model_copy(update={"latitude": geo.latitude, "longitude": geo.longitude})
        geocoded_assets.append(geocoded)
    yield {
        "step": 2,
        "total": total_steps,
        "message": f"✓ Geocoded {len(geocoded_assets)} assets (Kulai, Cyberjaya)",
        "done": False
    }
    
    # Step 3: Flood risk
    yield {"step": 3, "total": total_steps, "message": "Assessing flood risk...", "done": False}
    flood_risks = []
    flood_messages = []
    for asset in geocoded_assets:
        if asset.latitude is None or asset.longitude is None:
            continue
        risk = assess_flood_risk(FloodRiskInput(
            latitude=asset.latitude,
            longitude=asset.longitude,
            asset_name=asset.name,
        ))
        flood_risks.append(risk)
        icon = "⚠️" if risk.risk_level in ["High", "Critical"] else "✓"
        flood_messages.append(f"{asset.name}: {risk.risk_level} {icon}")
    yield {
        "step": 3,
        "total": total_steps,
        "message": f"✓ Flood risk: {', '.join(flood_messages)}",
        "done": False
    }
    
    # Step 4: Biodiversity
    yield {"step": 4, "total": total_steps, "message": "Checking protected area proximity...", "done": False}
    biodiversity_results = []
    bio_messages = []
    for asset in geocoded_assets:
        if asset.latitude is None or asset.longitude is None:
            continue
        bio = check_biodiversity(BiodiversityInput(
            latitude=asset.latitude,
            longitude=asset.longitude,
            asset_name=asset.name,
        ))
        biodiversity_results.append(bio)
        icon = "⚠️" if bio.risk_flag else "✓"
        bio_messages.append(f"{asset.name}: {bio.distance_km}km {icon}")
    yield {
        "step": 4,
        "total": total_steps,
        "message": f"✓ Biodiversity: {', '.join(bio_messages)}",
        "done": False
    }
    
    # Step 5: Transition risk
    yield {"step": 5, "total": total_steps, "message": "Assessing transition risk...", "done": False}
    sector = doc.sector or "data centre"
    transition = assess_transition_risk(TransitionRiskInput(sector=sector))
    icon = "⚠️" if transition.risk_level in ["High", "Critical"] else "✓"
    yield {
        "step": 5,
        "total": total_steps,
        "message": f"✓ Transition risk: {transition.sector} → {transition.risk_level} {icon}",
        "done": False
    }
    
    # Step 6: Generate map
    yield {"step": 6, "total": total_steps, "message": "Generating interactive map...", "done": False}
    map_path = str(output_path / "map.html")
    flood_dicts = [r.model_dump() for r in flood_risks]
    map_result = generate_map(MapInput(
        assets=geocoded_assets,
        flood_risks=flood_dicts,
        flood_data=True,
        output_path=map_path,
    ))
    yield {
        "step": 6,
        "total": total_steps,
        "message": f"✓ Map generated: {len(geocoded_assets)} assets plotted",
        "done": False
    }
    
    # Step 7: Generate report
    yield {"step": 7, "total": total_steps, "message": "Generating due diligence memo...", "done": False}
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
    
    report = generate_report(ReportInput(
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
    ))
    yield {
        "step": 7,
        "total": total_steps,
        "message": f"✓ Memo generated: {len(esg_gaps)} ESG gaps, {len(red_flags)} red flags",
        "done": False
    }
    
    # Read generated files for final response
    map_html = Path(map_result.map_path).read_text()
    memo_html = Path(report.report_path).read_text()
    
    # Final event with results
    yield {
        "step": 7,
        "total": total_steps,
        "message": "✓ Pipeline complete!",
        "done": True,
        "map_html": map_html,
        "memo_html": memo_html,
        "summary": {
            "company_name": doc.company_name,
            "assets": len(geocoded_assets),
            "flood_risks": [r.risk_level for r in flood_risks],
            "transition_risk": transition.risk_level,
            "esg_gaps": esg_gaps,
            "red_flags": red_flags,
        }
    }


def _identify_esg_gaps(raw_text: str) -> list[str]:
    """Identify ESG disclosure gaps from document text."""
    gaps = []
    
    if "scope 2" not in raw_text.lower():
        gaps.append("Scope 2 emissions not disclosed")
    
    if "water usage" in raw_text.lower() and "industry standard" in raw_text.lower():
        gaps.append("Water usage reporting vague ('industry standard')")
    
    if "renewable" in raw_text.lower() and "consideration" in raw_text.lower():
        gaps.append("Renewable energy plan aspirational, not committed")
    
    if not gaps:
        gaps.append("No material ESG gaps identified")
    
    return gaps


def _identify_red_flags(flood_risks, biodiversity_results, raw_text: str) -> list[str]:
    """Identify red flags from analysis results."""
    flags = []
    
    for fr in flood_risks:
        if fr.risk_level in ["High", "Critical"]:
            flags.append(f"{fr.asset_name}: {fr.risk_level} flood risk")
    
    for bio in biodiversity_results:
        if bio.risk_flag:
            flags.append(f"{bio.asset_name}: Near protected area ({bio.distance_km}km)")
    
    return flags


def main():
    """CLI entry point."""
    parser = argparse.ArgumentParser(description="CADI Agent")
    parser.add_argument("--input", "-i", required=True, help="Path to deal PDF")
    parser.add_argument("--output", "-o", default="output/", help="Output directory")
    parser.add_argument("--dry-run", action="store_true", help="Don't execute tools")
    args = parser.parse_args()

    results = run_agent(args.input, args.output, args.dry_run)

    # Save results
    output_path = Path(args.output)
    output_path.mkdir(parents=True, exist_ok=True)

    results_file = output_path / "agent_results.json"
    with open(results_file, "w") as f:
        json.dump(results, f, indent=2, default=str)

    console.print(f"\n[green]Results saved to {results_file}[/green]")


if __name__ == "__main__":
    main()
