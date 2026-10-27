"""
Integration Tests for Phase 4 REST API Endpoints
Tests /api/v1/intelligence and /api/v1/alerts routes, request validation,
Pydantic schemas, and role-based permissions.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)

DEV_ADMIN_HEADERS = {
    "X-RakshaGrid-User-ID": "admin-01",
    "X-RakshaGrid-User-Role": "admin",
}


def test_external_data_weather_api():
    """Verify GET /api/v1/intelligence/external-data/weather."""
    res = client.get("/api/v1/intelligence/external-data/weather?latitude=26.18&longitude=91.74")
    assert res.status_code == 200
    data = res.json()
    assert "weather" in data
    assert "flood" in data
    assert "is_stale" in data


def test_external_data_health_api():
    """Verify GET /api/v1/intelligence/external-data/health."""
    res = client.get("/api/v1/intelligence/external-data/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "operational"


def test_risk_assessment_api():
    """Verify POST /api/v1/intelligence/risk/assess/{incident_id}."""
    create_res = client.post(
        "/api/v1/incidents",
        headers=DEV_ADMIN_HEADERS,
        json={
            "title": "Brahmaputra Flood Breach Test",
            "category": "flood",
            "severity": "critical",
            "status": "response_active",
            "latitude": 26.18,
            "longitude": 91.74,
            "affected_population": 5000,
        },
    )
    assert create_res.status_code == 201
    inc_id = create_res.json()["id"]

    res = client.post(f"/api/v1/intelligence/risk/assess/{inc_id}")
    assert res.status_code == 200
    data = res.json()
    assert data["incident_id"] == inc_id
    assert 0.0 <= data["calculated_risk_score"] <= 100.0
    assert data["risk_level"] in ("Low", "Moderate", "High", "Critical")
    assert len(data["scoring_breakdown"]) > 0


def test_risk_assessments_history_api():
    """Verify GET /api/v1/intelligence/risk/assessments."""
    res = client.get("/api/v1/intelligence/risk/assessments")
    assert res.status_code == 200
    data = res.json()
    assert "assessments" in data


def test_ai_agent_analyze_api():
    """Verify POST /api/v1/intelligence/agent/analyze."""
    res = client.post("/api/v1/intelligence/agent/analyze", json={})
    assert res.status_code == 200
    data = res.json()
    assert "analysis_id" in data
    assert "situation_summary" in data
    assert "priority_incidents_ranked" in data
    assert "recommended_response_plan" in data
    assert data["decision_gate"]["requires_human_approval"] is True


def test_ai_agent_plan_approve_api():
    """Verify POST /api/v1/intelligence/agent/plan/approve with staff permissions."""
    # First get an analysis record
    init_res = client.post("/api/v1/intelligence/agent/analyze", json={})
    aid = init_res.json()["analysis_id"]

    # Approve
    res = client.post(
        "/api/v1/intelligence/agent/plan/approve",
        headers=DEV_ADMIN_HEADERS,
        json={"analysis_id": aid, "approve": True, "notes": "Approved for tactical mobilization"},
    )
    assert res.status_code == 200
    assert res.json()["approval_status"] == "approved"


def test_simulation_run_api():
    """Verify POST /api/v1/intelligence/simulations/run."""
    res = client.post(
        "/api/v1/intelligence/simulations/run",
        json={
            "scenario_type": "heavy_rainfall",
            "scenario_name": "API Cloudburst Test",
            "parameters": {"rainfall_mm": 95.0, "duration_hours": 6},
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["is_simulation"] is True
    assert "simulation_id" in data
    assert "projected_impact" in data


def test_simulations_history_api():
    """Verify GET /api/v1/intelligence/simulations/history."""
    res = client.get("/api/v1/intelligence/simulations/history")
    assert res.status_code == 200
    data = res.json()
    assert "simulations" in data


def test_alerts_evaluate_and_list_api():
    """Verify POST /api/v1/alerts/evaluate and GET /api/v1/alerts."""
    eval_res = client.post("/api/v1/alerts/evaluate", headers=DEV_ADMIN_HEADERS)
    assert eval_res.status_code == 200

    list_res = client.get("/api/v1/alerts")
    assert list_res.status_code == 200
    alerts = list_res.json()
    assert isinstance(alerts, list)


def test_alert_acknowledge_and_resolve_api():
    """Verify alert lifecycle via REST endpoints."""
    # Ensure at least one alert exists
    client.post("/api/v1/alerts/evaluate", headers=DEV_ADMIN_HEADERS)
    alerts = client.get("/api/v1/alerts?status=active").json()
    if alerts:
        aid = alerts[0]["id"]
        # Acknowledge
        ack_res = client.post(f"/api/v1/alerts/{aid}/acknowledge", headers=DEV_ADMIN_HEADERS)
        assert ack_res.status_code == 200
        assert ack_res.json()["broadcast_status"] == "acknowledged"

        # Resolve
        res_res = client.post(
            f"/api/v1/alerts/{aid}/resolve",
            headers=DEV_ADMIN_HEADERS,
            json={"resolution_notes": "All sectors stabilized by field units."},
        )
        assert res_res.status_code == 200
        assert res_res.json()["broadcast_status"] == "resolved"
