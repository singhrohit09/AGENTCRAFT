"""
Comprehensive Automated Tests for RakshaGrid Phase 2 Incident Management API
Covers validation rules, transactional persistence, status transition state machine,
chronological history audits, authorization controls, and pagination boundaries.
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.app import app
from backend.database.session import Base, get_db
from backend.rakshagrid.auth import UserRole
from backend.rakshagrid.models import Incident, IncidentUpdate
from backend.tests.conftest import test_engine, TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# 1. Incident Creation & Transactional History Tests
# ------------------------------------------------------------------------------

def test_create_incident_success():
    """Verify happy-path incident creation and automatic creation history logging."""
    payload = {
        "title": "Severe Flash Flood in Sector 4",
        "description": "Rising river waters breached temporary bund.",
        "category": "flood",
        "severity": "critical",
        "status": "reported",
        "latitude": 26.185,
        "longitude": 91.748,
        "location_description": "Guwahati Sector 4",
        "affected_population": 45000,
        "source_type": "operator_report",
        "verification_status": "under_review",
    }
    headers = {"X-Operator-Id": "operator-alice", "X-Operator-Role": "operator"}
    res = client.post("/api/v1/incidents", json=payload, headers=headers)
    assert res.status_code == 201
    data = res.json()
    assert data["title"] == payload["title"]
    assert data["category"] == "flood"
    assert data["severity"] == "critical"
    assert data["status"] == "reported"
    assert data["created_by"] == "operator-alice"
    assert data["incident_code"].startswith("RG-")
    assert "id" in data

    incident_id = data["id"]

    # Verify history timeline record was created in the same transaction
    timeline_res = client.get(f"/api/v1/incidents/{incident_id}/updates")
    assert timeline_res.status_code == 200
    timeline = timeline_res.json()
    assert timeline["total"] == 1
    update = timeline["items"][0]
    assert update["update_type"] == "creation"
    assert update["actor_id"] == "operator-alice"
    assert update["new_status"] == "reported"


def test_create_incident_normalization():
    """Verify that human synonyms (e.g. 'severe weather', 'cyclone', 'minor') normalize correctly."""
    payload = {
        "title": "Coastal Cyclone Watch",
        "category": "cyclone",      # Normalizes to 'severe_weather'
        "severity": "minor",        # Normalizes to 'low'
        "status": "active",         # Normalizes to 'response_active'
    }
    res = client.post("/api/v1/incidents", json=payload)
    assert res.status_code == 201
    data = res.json()
    assert data["category"] == "severe_weather"
    assert data["severity"] == "low"
    assert data["status"] == "response_active"


# ------------------------------------------------------------------------------
# 2. Validation Boundary Tests
# ------------------------------------------------------------------------------

def test_invalid_latitude_rejected():
    """Latitude > 90 or < -90 must be rejected with 422."""
    res = client.post("/api/v1/incidents", json={"title": "Invalid Lat", "latitude": 95.5})
    assert res.status_code == 422


def test_invalid_longitude_rejected():
    """Longitude > 180 or < -180 must be rejected with 422."""
    res = client.post("/api/v1/incidents", json={"title": "Invalid Lon", "longitude": -195.0})
    assert res.status_code == 422


def test_negative_population_rejected():
    """Negative affected population estimate must be rejected with 422."""
    res = client.post("/api/v1/incidents", json={"title": "Negative Pop", "affected_population": -10})
    assert res.status_code == 422


def test_title_too_short_rejected():
    """Incident title < 3 characters must be rejected with 422."""
    res = client.post("/api/v1/incidents", json={"title": "X"})
    assert res.status_code == 422


def test_invalid_uuid_rejected():
    """Malformed UUID path parameter must return 422 unprocessable entity."""
    res = client.get("/api/v1/incidents/not-a-valid-uuid")
    assert res.status_code == 422


def test_missing_incident_returns_404():
    """Querying an unknown valid UUID must return 404."""
    random_uuid = str(uuid.uuid4())
    res = client.get(f"/api/v1/incidents/{random_uuid}")
    assert res.status_code == 404


def test_pagination_max_limit_enforced():
    """Requesting page_size > 100 must be rejected with 422."""
    res = client.get("/api/v1/incidents?page_size=150")
    assert res.status_code == 422
    assert "100" in str(res.json()["detail"])


def test_database_persistence_and_transaction_rollback(monkeypatch):
    """Verify that if an error occurs during timeline history logging, the incident creation rolls back."""
    from backend.rakshagrid.incident_service import incident_service

    # Verify normal persistence first
    res = client.post("/api/v1/incidents", json={"title": "Persistent Hazard"})
    assert res.status_code == 201
    created_id = res.json()["id"]

    # Verify it can be fetched directly from database session
    db = TestingSessionLocal()
    persisted = db.query(Incident).filter(Incident.id == uuid.UUID(created_id)).first()
    assert persisted is not None
    assert persisted.title == "Persistent Hazard"
    db.close()

    # Now simulate a failure during history logging
    from sqlalchemy.orm import Session
    original_add = Session.add

    def mock_add_with_failure(self, instance, *args, **kwargs):
        if isinstance(instance, IncidentUpdate):
            raise RuntimeError("Simulated Disk Full Failure on Timeline Log")
        return original_add(self, instance, *args, **kwargs)

    monkeypatch.setattr(Session, "add", mock_add_with_failure)

    # Attempt creation -> must fail and rollback
    fail_res = client.post("/api/v1/incidents", json={"title": "Should Rollback"})
    assert fail_res.status_code == 500
    assert "Database transaction aborted" in fail_res.json()["detail"]

    # Verify that the incident was NOT committed to the database
    db2 = TestingSessionLocal()
    uncommitted = db2.query(Incident).filter(Incident.title == "Should Rollback").first()
    assert uncommitted is None, "Transaction did not roll back; uncommitted record found in database!"
    db2.close()


# ------------------------------------------------------------------------------
# 3. Patching, Status Transitions & Timeline History
# ------------------------------------------------------------------------------

def test_incident_patch_and_status_transition():
    """Verify valid status progression and history recording."""
    # 1. Create incident in 'reported' status
    create_res = client.post("/api/v1/incidents", json={
        "title": "Bridge Structural Crack",
        "category": "other",
        "severity": "medium",
        "status": "reported",
    })
    inc_id = create_res.json()["id"]

    # 2. Transition from 'reported' to 'under_assessment'
    patch_res = client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "under_assessment", "change_reason": "Structural engineers on site"},
        headers={"X-Operator-Id": "cmdr-bob", "X-Operator-Role": "commander"},
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["status"] == "under_assessment"

    # 3. Verify history now contains 2 updates
    timeline_res = client.get(f"/api/v1/incidents/{inc_id}/updates")
    assert timeline_res.status_code == 200
    updates = timeline_res.json()["items"]
    assert len(updates) == 2
    assert updates[1]["update_type"] == "status_change"
    assert updates[1]["previous_status"] == "reported"
    assert updates[1]["new_status"] == "under_assessment"
    assert "Structural engineers on site" in updates[1]["message"]


def test_invalid_status_transition_rejected():
    """Transitioning directly from 'reported' to 'resolved' (skipping assessment) is rejected with 400."""
    create_res = client.post("/api/v1/incidents", json={
        "title": "Landslide Highway",
        "status": "reported",
    })
    inc_id = create_res.json()["id"]

    # Attempt illegal transition to 'resolved'
    bad_patch = client.patch(
        f"/api/v1/incidents/{inc_id}",
        json={"status": "resolved"},
        headers={"X-Operator-Id": "operator-alice", "X-Operator-Role": "operator"},
    )
    assert bad_patch.status_code == 400
    assert "Invalid status transition" in bad_patch.json()["detail"]


def test_add_situation_report_update():
    """Verify manual creation of verified situation update on an incident timeline."""
    create_res = client.post("/api/v1/incidents", json={"title": "Wildfire Observation"})
    inc_id = create_res.json()["id"]

    update_payload = {
        "message": "Canopy spread arrested along western flank. 3 smoke-chasers deployed.",
        "update_type": "situation_report",
        "metadata_payload": {"wind_speed_kmh": 14, "contained_pct": 65},
    }
    update_res = client.post(
        f"/api/v1/incidents/{inc_id}/updates",
        json=update_payload,
        headers={"X-Operator-Id": "ranger-dan", "X-Operator-Role": "operator"},
    )
    assert update_res.status_code == 201
    data = update_res.json()
    assert data["actor_id"] == "ranger-dan"
    assert data["message"] == update_payload["message"]
    assert data["metadata_payload"]["contained_pct"] == 65


# ------------------------------------------------------------------------------
# 4. Search, Filtering & Pagination
# ------------------------------------------------------------------------------

def test_list_incidents_with_search_and_filtering():
    """Verify filtering by category, severity, status, and full text search."""
    # Seed 3 distinct incidents
    client.post("/api/v1/incidents", json={"title": "Assam Flood Alert", "category": "flood", "severity": "critical", "status": "response_active"})
    client.post("/api/v1/incidents", json={"title": "Himalaya Landslide NH-58", "category": "landslide", "severity": "high", "status": "confirmed"})
    client.post("/api/v1/incidents", json={"title": "Coastal Cyclone Watch", "category": "severe_weather", "severity": "medium", "status": "reported"})

    # 1. Filter by category=flood
    flood_res = client.get("/api/v1/incidents?category=flood")
    assert flood_res.status_code == 200
    assert flood_res.json()["total"] == 1
    assert flood_res.json()["items"][0]["category"] == "flood"

    # 2. Search keyword "NH-58"
    search_res = client.get("/api/v1/incidents?search=NH-58")
    assert search_res.status_code == 200
    assert search_res.json()["total"] == 1
    assert "Landslide" in search_res.json()["items"][0]["title"]

    # 3. Filter by severity=critical
    crit_res = client.get("/api/v1/incidents?severity=critical")
    assert crit_res.status_code == 200
    assert crit_res.json()["total"] == 1


# ------------------------------------------------------------------------------
# 5. Role-Based Authorization Tests
# ------------------------------------------------------------------------------

def test_admin_deletion_versus_unauthorized():
    """Verify that incident deletion is strictly restricted to administrator role."""
    create_res = client.post("/api/v1/incidents", json={"title": "Drill Exercise"})
    inc_id = create_res.json()["id"]

    # Non-admin attempt (operator role) must return 403 Forbidden
    op_headers = {"X-Operator-Id": "operator-1", "X-Operator-Role": "operator"}
    bad_del = client.delete(f"/api/v1/incidents/{inc_id}", headers=op_headers)
    assert bad_del.status_code == 403

    # Admin attempt archives successfully
    admin_headers = {"X-Operator-Id": "admin-super", "X-Operator-Role": "admin"}
    ok_del = client.delete(f"/api/v1/incidents/{inc_id}", headers=admin_headers)
    assert ok_del.status_code == 200
    assert ok_del.json()["status"] == "closed"


# ------------------------------------------------------------------------------
# 6. Deterministic Dev Seeder Test
# ------------------------------------------------------------------------------

def test_deterministic_dev_seeder():
    """Verify that development seeder runs idempotently and tags incidents as simulation."""
    res = client.post("/api/v1/incidents/seed?reset=true")
    assert res.status_code == 200
    data = res.json()
    assert data["inserted"] == 5

    # Run again without reset -> all 5 must be skipped (idempotent)
    second_res = client.post("/api/v1/incidents/seed")
    assert second_res.status_code == 200
    assert second_res.json()["inserted"] == 0
    assert second_res.json()["skipped"] == 5

    # Query incidents to verify simulation source_type tag
    sim_incidents = client.get("/api/v1/incidents?search=SIMULATION")
    assert sim_incidents.status_code == 200
    assert sim_incidents.json()["total"] == 5
    for item in sim_incidents.json()["items"]:
        assert item["source_type"] == "simulation"


# ------------------------------------------------------------------------------
# 7. Regression & Validation Hardening Tests
# ------------------------------------------------------------------------------

def test_situation_update_with_update_message_alias():
    """Verify that situation updates accepting 'update_message' payload succeed and return update_message."""
    create_res = client.post("/api/v1/incidents", json={"title": "Sitrep Alias Incident"})
    inc_id = create_res.json()["id"]

    res = client.post(
        f"/api/v1/incidents/{inc_id}/updates",
        json={"update_message": "Evacuation corridor cleared by SDRF unit.", "update_type": "situation_report"},
    )
    assert res.status_code == 201
    data = res.json()
    assert data["message"] == "Evacuation corridor cleared by SDRF unit."
    assert data["update_message"] == "Evacuation corridor cleared by SDRF unit."


def test_admin_deletion_with_rakshagrid_dev_headers():
    """Verify that X-Rakshagrid-Dev-Role and X-Rakshagrid-Dev-User authorize admin incident archival."""
    create_res = client.post("/api/v1/incidents", json={"title": "Header Auth Test"})
    inc_id = create_res.json()["id"]

    headers = {
        "X-Rakshagrid-Dev-Role": "admin",
        "X-Rakshagrid-Dev-User": "admin-chief-01",
    }
    del_res = client.delete(f"/api/v1/incidents/{inc_id}", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["status"] == "closed"


def test_permanent_deletion_removes_record():
    """Verify permanent deletion removes record from database completely."""
    create_res = client.post("/api/v1/incidents", json={"title": "Temporary Test Incident"})
    inc_id = create_res.json()["id"]

    headers = {"X-Operator-Id": "admin-super", "X-Operator-Role": "admin"}
    del_res = client.delete(f"/api/v1/incidents/{inc_id}?permanent=true", headers=headers)
    assert del_res.status_code == 200
    assert del_res.json()["action"] == "deleted"

    # Confirm it is 404 now
    get_res = client.get(f"/api/v1/incidents/{inc_id}")
    assert get_res.status_code == 404


def test_empty_or_whitespace_title_rejected():
    """Empty string or whitespace-only title must be rejected with 422."""
    res1 = client.post("/api/v1/incidents", json={"title": ""})
    assert res1.status_code == 422

    res2 = client.post("/api/v1/incidents", json={"title": "   "})
    assert res2.status_code == 422

