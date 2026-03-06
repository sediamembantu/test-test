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
