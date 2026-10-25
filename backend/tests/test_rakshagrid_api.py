"""
Unit & Integration Tests for RakshaGrid Disaster Intelligence Subsystem
Tests API endpoints, Pydantic response schemas, SQLAlchemy model definitions,
and environment setting validators.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.rakshagrid.config import RakshaGridSettings
from backend.rakshagrid.models import (
    Incident,
    IncidentUpdate,
    Alert,
    ResponseTeam,
    ResponseTask,
    Shelter,
    Resource,
    ResourceMovement,
    EnvironmentalObservation,
    RiskAssessment,
    AuditLog,
)
from backend.database.session import Base

client = TestClient(app)


def test_root_endpoint_includes_rakshagrid():
    """Verify that root endpoint exposes RakshaGrid health and metadata."""
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "AgentCraft"
    assert data["subsystem"] == "RakshaGrid"
    assert data["rakshagrid_health"] == "/api/rakshagrid/health"
    assert data["rakshagrid_overview"] == "/api/rakshagrid/overview"


def test_rakshagrid_health_endpoint():
    """Verify that /api/rakshagrid/health returns operational diagnostics."""
    res = client.get("/api/rakshagrid/health")
    assert res.status_code == 200
    data = res.json()
    assert data["project"] == "RakshaGrid"
    assert data["subtitle"] == "Disaster Intelligence and Response"
    assert "status" in data
    assert "version" in data
    assert "uptime_seconds" in data
    assert "subsystems" in data
    assert "database" in data["subsystems"]
    assert "incident_engine" in data["subsystems"]
    assert "alert_broadcaster" in data["subsystems"]
    assert "geospatial_indexer" in data["subsystems"]
    assert data["subsystems"]["incident_engine"]["status"] == "operational"


def test_rakshagrid_database_status_endpoint():
    """Verify /api/rakshagrid/database/status reports configuration and model metrics."""
    res = client.get("/api/rakshagrid/database/status")
    assert res.status_code == 200
    data = res.json()
    assert "configured" in data
    assert "host" in data
    assert "port" in data
    assert "database" in data
    assert "status" in data
    assert data["active_migration_version"] == "0001_initial"
    assert data["models_registered_count"] == 11


def test_rakshagrid_overview_endpoint():
    """Verify tactical overview contains stats, incidents, alerts, and demo disclaimers."""
    res = client.get("/api/rakshagrid/overview")
    assert res.status_code == 200
    data = res.json()
    assert "stats" in data
    assert "active_incidents" in data
    assert "high_priority_alerts" in data
    assert "recent_activity" in data
    assert "disclaimer" in data
    assert "[FICTIONAL DEMO DATA" in data["disclaimer"]

    stats = data["stats"]
    assert stats["defcon_level"] in (1, 2, 3, 4, 5)
    assert stats["active_incidents_count"] >= 1
    assert stats["deployed_teams_count"] >= 1
    assert stats["total_shelter_capacity"] > 0


def test_rakshagrid_list_incidents_filtering():
    """Verify incidents listing and criteria filtering."""
    # Unfiltered
    res = client.get("/api/rakshagrid/incidents")
    assert res.status_code == 200
    incidents = res.json()
    assert len(incidents) >= 4

    # Filter by disaster_type=flood
    flood_res = client.get("/api/rakshagrid/incidents?disaster_type=flood")
    assert flood_res.status_code == 200
    floods = flood_res.json()
    assert len(floods) >= 1
    assert all(i["disaster_type"] == "flood" for i in floods)

    # Filter by severity=critical
    crit_res = client.get("/api/rakshagrid/incidents?severity=critical")
    assert crit_res.status_code == 200
    crits = crit_res.json()
    assert len(crits) >= 1
    assert all(i["severity"] == "critical" for i in crits)


def test_rakshagrid_alerts_endpoint():
    """Verify emergency alerts retrieval and filtering."""
    res = client.get("/api/rakshagrid/alerts")
    assert res.status_code == 200
    alerts = res.json()
    assert len(alerts) >= 1
    first = alerts[0]
    assert "alert_code" in first
    assert "headline" in first
    assert "severity" in first
    assert "instructions" in first
    assert first["is_demo"] is True


def test_rakshagrid_teams_endpoint():
    """Verify response teams endpoint."""
    res = client.get("/api/rakshagrid/teams")
    assert res.status_code == 200
    teams = res.json()
    assert len(teams) >= 3
    assert any(t["unit_type"] == "ndrf" for t in teams)

    # Status filter
    deployed_res = client.get("/api/rakshagrid/teams?status=deployed")
    assert deployed_res.status_code == 200
    deployed = deployed_res.json()
    assert len(deployed) >= 1
    assert all(t["current_status"] == "deployed" for t in deployed)


def test_rakshagrid_shelters_endpoint():
    """Verify shelters capacity endpoint."""
    res = client.get("/api/rakshagrid/shelters")
    assert res.status_code == 200
    shelters = res.json()
    assert len(shelters) >= 2
    for s in shelters:
        assert s["capacity"] > 0
        assert s["occupancy_percent"] >= 0.0


def test_rakshagrid_public_config_endpoint():
    """Verify public config exposes sanitized parameters without secrets."""
    res = client.get("/api/rakshagrid/config")
    assert res.status_code == 200
    cfg = res.json()
    assert cfg["app_name"] == "RakshaGrid"
    assert "password" not in str(cfg).lower()
    assert cfg["demo_mode"] is True


def test_rakshagrid_settings_validation():
    """Verify Pydantic environment variable validation rules."""
    # Valid instance
    settings = RakshaGridSettings(RAKSHAGRID_ENV="production", RAKSHAGRID_ALERT_THRESHOLD="CRITICAL")
    assert settings.RAKSHAGRID_ENV == "production"
    assert settings.RAKSHAGRID_ALERT_THRESHOLD == "CRITICAL"

    # Invalid environment
    with pytest.raises(ValueError):
        RakshaGridSettings(RAKSHAGRID_ENV="invalid_environment")

    # Invalid threshold
    with pytest.raises(ValueError):
        RakshaGridSettings(RAKSHAGRID_ALERT_THRESHOLD="INVALID_THRESHOLD")


def test_sqlalchemy_models_registration():
    """Verify that all 11 required disaster response entities are registered in SQLAlchemy Base."""
    expected_tables = {
        "incidents",
        "incident_updates",
        "alerts",
        "response_teams",
        "response_tasks",
        "shelters",
        "resources",
        "resource_movements",
        "environmental_observations",
        "risk_assessments",
        "audit_logs",
    }
    actual_tables = set(Base.metadata.tables.keys())
    assert expected_tables.issubset(actual_tables), f"Missing tables: {expected_tables - actual_tables}"
