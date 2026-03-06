"""
Tests for agent orchestration.

Note: Full agent tests require ANTHROPIC_API_KEY.
These tests focus on tool definitions and orchestration logic.
"""

import pytest
from unittest.mock import patch, MagicMock

from src.agent import TOOL_DEFINITIONS, TOOLS, SYSTEM_PROMPT


class TestToolDefinitions:
    """Test Claude API tool definitions."""

    def test_all_tools_defined(self):
        """All expected tools should be defined."""
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        
        expected = {
            "parse_document",
            "geocode_address",
            "assess_flood_risk",
            "assess_transition_risk",
            "check_biodiversity",
            "generate_map",
            "generate_report",
        }
        
        assert expected == tool_names

    def test_tool_definitions_have_required_fields(self):
        """Each tool definition should have required fields."""
        for tool in TOOL_DEFINITIONS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool
            assert "type" in tool["input_schema"]
            assert "properties" in tool["input_schema"]
            assert "required" in tool["input_schema"]

    def test_parse_document_schema(self):
        """parse_document should require pdf_path."""
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "parse_document")
        
        assert "pdf_path" in tool["input_schema"]["required"]
        assert "pdf_path" in tool["input_schema"]["properties"]

    def test_geocode_address_schema(self):
        """geocode_address should require address."""
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "geocode_address")
        
        assert "address" in tool["input_schema"]["required"]
        assert "address" in tool["input_schema"]["properties"]

    def test_assess_flood_risk_schema(self):
        """assess_flood_risk should require lat, lon, asset_name."""
        tool = next(t for t in TOOL_DEFINITIONS if t["name"] == "assess_flood_risk")
        
        required = set(tool["input_schema"]["required"])
        assert {"latitude", "longitude", "asset_name"} == required


class TestToolMapping:
    """Test tool implementation mapping."""

    def test_all_tools_implemented(self):
        """All defined tools should have implementations."""
        tool_names = {t["name"] for t in TOOL_DEFINITIONS}
        
        for name in tool_names:
            assert name in TOOLS, f"Tool '{name}' not in TOOLS mapping"

    def test_tools_are_callable(self):
        """All tools should be callable."""
        for name, func in TOOLS.items():
            assert callable(func), f"Tool '{name}' is not callable"


class TestSystemPrompt:
    """Test agent system prompt."""

    def test_system_prompt_exists(self):
        """System prompt should be defined."""
        assert SYSTEM_PROMPT is not None
        assert len(SYSTEM_PROMPT) > 100

    def test_system_prompt_mentions_workflow(self):
        """System prompt should mention the workflow."""
        assert "workflow" in SYSTEM_PROMPT.lower()
        assert "parse" in SYSTEM_PROMPT.lower()
        assert "geocode" in SYSTEM_PROMPT.lower()

    def test_system_prompt_mentions_tools(self):
        """System prompt should mention tool usage."""
        # Should reference tools or tool selection
        prompt_lower = SYSTEM_PROMPT.lower()
        assert "tool" in prompt_lower


class TestToolExecution:
    """Test actual tool execution through the mapping."""

    def test_parse_document_execution(self):
        """parse_document tool should work through TOOLS mapping."""
        result = TOOLS["parse_document"]({
            "pdf_path": "data/deal/nusantara_digital.pdf"
        })
        
        assert result["company_name"] == "Nusantara Digital Sdn Bhd"
        assert len(result["assets"]) == 2

    def test_geocode_address_execution(self):
        """geocode_address tool should work through TOOLS mapping."""
        result = TOOLS["geocode_address"]({
            "address": "Kulai, Johor"
        })
        
        assert result["latitude"] == 1.6580
        assert result["longitude"] == 103.6000
        assert result["source"] == "fallback"

    def test_assess_flood_risk_execution(self):
        """assess_flood_risk tool should work through TOOLS mapping."""
        result = TOOLS["assess_flood_risk"]({
            "latitude": 1.658,
            "longitude": 103.6,
            "asset_name": "Test Asset"
        })
        
        assert result["risk_level"] == "High"
        assert result["asset_name"] == "Test Asset"

    def test_assess_transition_risk_execution(self):
        """assess_transition_risk tool should work through TOOLS mapping."""
        result = TOOLS["assess_transition_risk"]({
            "sector": "data centre"
        })
        
        assert result["risk_level"] == "High"
        assert result["sector"] == "data centre"


class TestAgentIntegration:
    """Integration tests for agent components."""

    @pytest.mark.skipif(
        True,  # Skip by default - requires ANTHROPIC_API_KEY
        reason="Requires ANTHROPIC_API_KEY environment variable"
    )
    def test_full_agent_run(self):
        """
        Full agent run test.
        
        To run: set ANTHROPIC_API_KEY and change skipif to False
        """
        from src.agent import run_agent
        
        result = run_agent(
            pdf_path="data/deal/nusantara_digital.pdf",
            output_dir="output/",
            dry_run=False
        )
        
        assert "tool_calls" in result
        assert len(result["tool_calls"]) > 0
