"""
Unit Tests for Phase 4 Disaster Intelligence Agent Tools
Validates schema descriptors, parameter validation, database queries,
and typed ToolResult encapsulation for all 8 disaster tools.
"""

import pytest
from ai.tools import ToolRegistry, ToolResult
from ai.tools.disaster_tools import (
    GetIncidentDetailsTool,
    GetIncidentRiskTool,
    GetWeatherObservationsTool,
    GetAvailableTeamsTool,
    GetActiveTasksTool,
    GetShelterCapacityTool,
    GetResourceInventoryTool,
    ProposeResponsePlanTool,
)


class TestDisasterTools:
    """Test suite covering the 8 Phase 4 Disaster Intelligence tools."""

    @pytest.fixture(autouse=True)
    def setup_registry(self):
        self.registry = ToolRegistry(allow_network=False)

    def test_all_phase4_tools_registered(self):
        """Verify all 8 disaster intelligence tools are present in registry."""
        expected_tools = [
            "get_incident_details",
            "get_incident_risk",
            "get_weather_observations",
            "get_available_teams",
            "get_active_tasks",
            "get_shelter_capacity",
            "get_resource_inventory",
            "propose_response_plan",
        ]
        registered = [t["name"] for t in self.registry.list_tools()]
        for exp in expected_tools:
            assert exp in registered, f"Missing tool '{exp}' in ToolRegistry."

    def test_get_incident_details_missing_param_validation(self):
        """Verify missing required parameter triggers validation failure."""
        tool = GetIncidentDetailsTool()
        result: ToolResult = tool.run()
        assert not result.success
        assert "Missing required parameter" in result.error

    def test_get_incident_details_nonexistent_incident(self):
        """Verify querying unknown incident returns clean error ToolResult."""
        tool = GetIncidentDetailsTool()
        result: ToolResult = tool.run(incident_id="NON-EXISTENT-UUID-12345")
        assert not result.success
        assert "not found" in result.error.lower()

    def test_get_incident_details_existing_simulation_record(self):
        """Verify querying existing simulated incident returns structured fields."""
        tool = GetIncidentDetailsTool()
        result: ToolResult = tool.run(incident_id="SIM-2026-FL-0001")
        assert result.success
        assert result.output["incident_code"] == "SIM-2026-FL-0001"
        assert result.output["category"] == "flood"
        assert "latitude" in result.output

    def test_get_incident_risk_tool(self):
        """Verify risk tool computes normalized score and breakdown."""
        tool = GetIncidentRiskTool()
        result: ToolResult = tool.run(incident_id="SIM-2026-FL-0001")
        assert result.success
        assert 0.0 <= result.output["calculated_risk_score"] <= 100.0
        assert result.output["risk_level"] in ("Low", "Moderate", "High", "Critical")

    def test_get_weather_observations_tool(self):
        """Verify weather tool returns telemetry and freshness."""
        tool = GetWeatherObservationsTool()
        result: ToolResult = tool.run(latitude=26.18, longitude=91.74)
        assert result.success
        assert "weather" in result.output
        assert "flood" in result.output

    def test_get_available_teams_tool(self):
        """Verify response teams query returns team list."""
        tool = GetAvailableTeamsTool()
        result: ToolResult = tool.run(status="all")
        assert result.success
        assert "teams" in result.output
        assert result.output["count"] >= 0

    def test_get_active_tasks_tool(self):
        """Verify task tool returns active tasks."""
        tool = GetActiveTasksTool()
        result: ToolResult = tool.run()
        assert result.success
        assert "tasks" in result.output

    def test_get_shelter_capacity_tool(self):
        """Verify shelter capacity tool evaluates occupancy and remaining space."""
        tool = GetShelterCapacityTool()
        result: ToolResult = tool.run(status="all")
        assert result.success
        assert "total_capacity" in result.output
        assert "overall_occupancy_pct" in result.output

    def test_get_resource_inventory_tool(self):
        """Verify resource inventory tool detects stockpile counts."""
        tool = GetResourceInventoryTool()
        result: ToolResult = tool.run()
        assert result.success
        assert "inventory" in result.output
        assert "shortages_count" in result.output

    def test_propose_response_plan_decision_gate(self):
        """Verify response plan proposal enforces human-in-the-loop decision gate."""
        tool = ProposeResponsePlanTool()
        result: ToolResult = tool.run(
            incident_id="SIM-2026-FL-0001",
            rationale="Immediate containment required for river flood breach",
            recommended_teams=["NDRF-Bravo"],
            recommended_tasks=[{"title": "Sandbagging sector 4", "priority": "high"}],
        )
        assert result.success
        out = result.output
        assert out["is_recommendation"] is True
        assert out["requires_human_approval"] is True
        assert out["approval_status"] == "pending"
        assert "OPERATIONAL DECISION GATE" in out["consequential_action_disclaimer"]
