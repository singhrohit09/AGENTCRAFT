"""
Unit & Integration Tests for Live Tactical Overview Aggregation
Tests database-backed metrics computation, empty-state reporting,
and fallback demonstration telemetry.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.rakshagrid.config import rakshagrid_settings
from backend.rakshagrid.models import Incident, ResponseTeam, Shelter, Alert
from backend.rakshagrid.service import rakshagrid_service


def test_overview_in_demo_mode():
    """Verify overview returns demonstration telemetry with disclaimer when demo mode is active."""
    orig_demo = rakshagrid_settings.RAKSHAGRID_DEMO_MODE
    rakshagrid_settings.RAKSHAGRID_DEMO_MODE = True
    try:
        data = rakshagrid_service.get_overview_data()
        assert data["stats"]["demo_mode_active"] is True
        assert "[FICTIONAL DEMO DATA" in data["disclaimer"]
        assert data["stats"]["active_incidents_count"] >= 1
    finally:
        rakshagrid_settings.RAKSHAGRID_DEMO_MODE = orig_demo


def test_overview_live_empty_database(db_session):
    """Verify overview returns an honest empty state when database is empty and demo mode is off."""
    orig_demo = rakshagrid_settings.RAKSHAGRID_DEMO_MODE
    rakshagrid_settings.RAKSHAGRID_DEMO_MODE = False
    try:
        data = rakshagrid_service.get_overview_data(db=db_session)
        assert data["stats"]["demo_mode_active"] is False
        assert data["stats"]["active_incidents_count"] == 0
        assert data["stats"]["critical_incidents_count"] == 0
        assert data["stats"]["deployed_teams_count"] == 0
        assert data["stats"]["total_shelter_capacity"] == 0
        assert len(data["active_incidents"]) == 0
        assert "Database initialized" in data["disclaimer"]
    finally:
        rakshagrid_settings.RAKSHAGRID_DEMO_MODE = orig_demo


def test_overview_live_populated_database(db_session):
    """Verify overview computes live metrics correctly when database contains records."""
    orig_demo = rakshagrid_settings.RAKSHAGRID_DEMO_MODE
    rakshagrid_settings.RAKSHAGRID_DEMO_MODE = False
    try:
        # Create a test incident
        inc = Incident(
            id=uuid.uuid4(),
            incident_code="LIVE-FL-001",
            title="Active Flash Flood",
            category="flood",
            severity="critical",
            status="response_active",
            latitude=26.15,
            longitude=91.75,
            affected_population=3500,
        )
        db_session.add(inc)

        # Create a test team
        tm = ResponseTeam(
            id=uuid.uuid4(),
            team_callsign="NDRF-ALPHA",
            unit_type="NDRF",
            personnel_count=25,
            commander_name="Maj. Verma",
            contact_channel="VHF-01",
            base_location="Disaster Management HQ",
            current_status="assigned",
        )
        db_session.add(tm)

        # Create a test shelter
        sh = Shelter(
            id=uuid.uuid4(),
            name="Sector 1 High School",
            shelter_type="school",
            capacity=500,
            current_occupancy=250,
            address="Sector 1 Main Road",
            status="open",
        )
        db_session.add(sh)
        db_session.commit()

        data = rakshagrid_service.get_overview_data(db=db_session)
        assert data["stats"]["demo_mode_active"] is False
        assert data["stats"]["active_incidents_count"] == 1
        assert data["stats"]["critical_incidents_count"] == 1
        assert data["stats"]["deployed_teams_count"] == 1
        assert data["stats"]["total_shelter_capacity"] == 500
        assert data["stats"]["total_sheltered_population"] == 250
        assert data["stats"]["overall_shelter_occupancy_pct"] == 50.0
        assert len(data["active_incidents"]) == 1
        assert data["active_incidents"][0]["incident_code"] == "LIVE-FL-001"
        assert "Live Operational State" in data["disclaimer"]
    finally:
        rakshagrid_settings.RAKSHAGRID_DEMO_MODE = orig_demo
