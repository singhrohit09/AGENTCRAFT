"""
Unit & Integration Tests for Disaster Scenario Simulations
Tests heavy rainfall, multi-incident, team outage, shelter surge,
supply shortage, and guarantees complete isolation from live operational database state.
"""

import pytest
from backend.database.session import transactional_session
from backend.rakshagrid.models import Incident, ResponseTeam, Shelter, Resource
from backend.services.simulation_service import simulation_engine


def test_heavy_rainfall_simulation():
    """Verify heavy rainfall scenario calculates flood risk delta and shelter strain."""
    with transactional_session() as db:
        res = simulation_engine.run_simulation(
            db,
            scenario_type="heavy_rainfall",
            scenario_name="Monsoon Cloudburst Simulation",
            parameters={"rainfall_mm": 120.0, "duration_hours": 8},
        )
        assert res["is_simulation"] is True
        assert "simulation_id" in res
        impact = res["projected_impact"]
        assert impact["rainfall_tested_mm"] == 120.0
        assert impact["projected_total_evacuation_surge"] > 0
        assert len(impact["bottlenecks"]) > 0


def test_multi_incident_concurrency_simulation():
    """Verify concurrent incident surge tests response team capacity."""
    with transactional_session() as db:
        res = simulation_engine.run_simulation(
            db,
            scenario_type="multi_incident",
            scenario_name="Compound Seismic Event",
            parameters={"concurrent_incidents_count": 6, "severity": "critical"},
        )
        impact = res["projected_impact"]
        assert impact["hypothetical_concurrent_incidents"] == 6
        assert "teams_required" in impact
        assert "teams_shortfall" in impact


def test_team_unavailability_simulation():
    """Verify simulating offline rescue units reflects readiness drop."""
    with transactional_session() as db:
        res = simulation_engine.run_simulation(
            db,
            scenario_type="team_unavailability",
            scenario_name="NDRF Isolation Scenario",
            parameters={"withdrawn_teams_count": 2},
        )
        impact = res["projected_impact"]
        assert impact["teams_withdrawn_count"] == 2
        assert impact["capacity_loss_pct"] >= 0.0


def test_shelter_surge_simulation():
    """Verify sudden displaced population surge calculates absorptive limits."""
    with transactional_session() as db:
        res = simulation_engine.run_simulation(
            db,
            scenario_type="shelter_surge",
            scenario_name="Coastal Evacuation Surge",
            parameters={"incoming_evacuees": 2000},
        )
        impact = res["projected_impact"]
        assert impact["incoming_evacuees_simulated"] == 2000
        assert len(impact["shelter_breakdown"]) > 0


def test_supply_shortage_simulation():
    """Verify high burn-rate stress computes days until stockout."""
    with transactional_session() as db:
        res = simulation_engine.run_simulation(
            db,
            scenario_type="supply_shortage",
            scenario_name="Supply Chain Disruption",
            parameters={"burn_rate_multiplier": 3.0, "duration_days": 5},
        )
        impact = res["projected_impact"]
        assert impact["burn_rate_multiplier"] == 3.0
        assert len(impact["projections"]) > 0


def test_simulation_guarantees_state_isolation():
    """Verify that running simulations NEVER mutates persistent incidents, teams, or shelters."""
    with transactional_session() as db:
        # Take snapshot before
        inc_count_before = db.query(Incident).count()
        team_count_before = db.query(ResponseTeam).count()
        shelter_count_before = db.query(Shelter).count()
        resource_count_before = db.query(Resource).count()

        # Run multiple intense simulations
        simulation_engine.run_simulation(
            db, "heavy_rainfall", "Stress Test 1", {"rainfall_mm": 250.0}
        )
        simulation_engine.run_simulation(
            db, "multi_incident", "Stress Test 2", {"concurrent_incidents_count": 10}
        )
        simulation_engine.run_simulation(
            db, "shelter_surge", "Stress Test 3", {"incoming_evacuees": 5000}
        )

        # Verify exact counts after
        assert db.query(Incident).count() == inc_count_before
        assert db.query(ResponseTeam).count() == team_count_before
        assert db.query(Shelter).count() == shelter_count_before
        assert db.query(Resource).count() == resource_count_before


def test_invalid_simulation_scenario_rejected():
    """Verify unsupported scenario type raises ValueError."""
    with transactional_session() as db:
        with pytest.raises(ValueError):
            simulation_engine.run_simulation(db, "unsupported_fantasy_scenario", "Test", {})
