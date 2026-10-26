"""
Automated Integration and Unit Tests for Phase 3: Maps & Coordination APIs
Tests Response Teams, Tasks, Shelters, and Resources across:
- End-to-end CRUD operations
- Relational integrity and foreign-key linking
- Capacity & occupancy boundary enforcements
- Team assignment conflict prevention and automatic status recalculations
- Inventory allocation and return movements with transaction safeguards
- Error handling and HTTP status codes (400, 404, 409, 422)
"""

import uuid
import pytest
from fastapi.testclient import TestClient
from backend.app import app
from backend.scripts.seed_dev_data import seed_dev_incidents

client = TestClient(app)

@pytest.fixture(autouse=True)
def seed_data(db_session):
    seed_dev_incidents(db_session, reset=True)

DEV_OPERATOR_HEADERS = {
    "X-Rakshagrid-Dev-Role": "field_commander",
    "X-Rakshagrid-Dev-User": "test-commander-1",
}

DEV_ADMIN_HEADERS = {
    "X-Rakshagrid-Dev-Role": "admin",
    "X-Rakshagrid-Dev-User": "test-admin-1",
}


# ==============================================================================
# Response Teams Tests
# ==============================================================================

def test_list_teams():
    res = client.get("/api/v1/teams", headers=DEV_OPERATOR_HEADERS)
    assert res.status_code == 200
    data = res.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1
    assert any(t["team_callsign"] == "NDRF-12-BRAVO" for t in data["items"])


def test_team_crud_and_status_transitions():
    unique_callsign = f"UNIT-TEST-{uuid.uuid4().hex[:6].upper()}"
    payload = {
        "team_callsign": unique_callsign,
        "unit_type": "Medical Triage",
        "personnel_count": 8,
        "commander_name": "Capt. Test Officer",
        "contact_channel": "SAT-TEST-99",
        "current_status": "available",
        "base_location": "Northern Staging Camp",
        "current_latitude": 28.6139,
        "current_longitude": 77.2090,
    }

    # 1. Create team
    create_res = client.post("/api/v1/teams", json=payload, headers=DEV_OPERATOR_HEADERS)
    assert create_res.status_code == 201
    team = create_res.json()
    team_id = team["id"]
    assert team["team_callsign"] == unique_callsign
    assert team["current_status"] == "available"

    # 2. Duplicate callsign rejected (409)
    dup_res = client.post("/api/v1/teams", json=payload, headers=DEV_OPERATOR_HEADERS)
    assert dup_res.status_code == 409

    # 3. Get team details
    get_res = client.get(f"/api/v1/teams/{team_id}", headers=DEV_OPERATOR_HEADERS)
    assert get_res.status_code == 200
    assert get_res.json()["commander_name"] == "Capt. Test Officer"

    # 4. Patch team details
    patch_res = client.patch(
        f"/api/v1/teams/{team_id}",
        json={"personnel_count": 12, "current_status": "offline"},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert patch_res.status_code == 200
    assert patch_res.json()["personnel_count"] == 12
    assert patch_res.json()["current_status"] == "offline"

    # 5. Delete team (admin required)
    del_res = client.delete(f"/api/v1/teams/{team_id}", headers=DEV_ADMIN_HEADERS)
    assert del_res.status_code == 200

    # 6. Verify deleted (404)
    del_verify = client.get(f"/api/v1/teams/{team_id}", headers=DEV_OPERATOR_HEADERS)
    assert del_verify.status_code == 404


def test_team_invalid_status_rejection():
    payload = {
        "team_callsign": f"INVALID-STAT-{uuid.uuid4().hex[:4]}",
        "unit_type": "NDRF",
        "personnel_count": 5,
        "commander_name": "Test Officer",
        "contact_channel": "Radio 1",
        "current_status": "flying_in_sky",  # Invalid
        "base_location": "Base 1",
    }
    res = client.post("/api/v1/teams", json=payload, headers=DEV_OPERATOR_HEADERS)
    assert res.status_code == 422


# ==============================================================================
# Response Tasks Tests
# ==============================================================================

def test_task_creation_linking_and_completion_lifecycle():
    # Fetch an existing simulation incident
    inc_res = client.get("/api/v1/incidents?category=flood", headers=DEV_OPERATOR_HEADERS)
    assert inc_res.status_code == 200
    incidents = inc_res.json()["items"]
    assert len(incidents) > 0
    incident_id = incidents[0]["id"]

    # Create a fresh available response team
    team_callsign = f"TASK-TEAM-{uuid.uuid4().hex[:6].upper()}"
    team_res = client.post(
        "/api/v1/teams",
        json={
            "team_callsign": team_callsign,
            "unit_type": "SDRF Flood Rescue",
            "personnel_count": 10,
            "commander_name": "Lt. Rescue",
            "contact_channel": "CH-4",
            "current_status": "available",
            "base_location": "River Staging Depot",
        },
        headers=DEV_OPERATOR_HEADERS,
    )
    assert team_res.status_code == 201
    team_id = team_res.json()["id"]

    # 1. Create a task linked to the incident and assign team
    task_payload = {
        "incident_id": incident_id,
        "title": "Deliver emergency medical crates to Sector 4 island",
        "description": "Cross river via motorboat and deliver sterile field dressings.",
        "priority": "critical",
        "assigned_team_id": team_id,
        "target_latitude": 26.185,
        "target_longitude": 91.748,
    }
    task_res = client.post("/api/v1/tasks", json=task_payload, headers=DEV_OPERATOR_HEADERS)
    assert task_res.status_code == 201
    task = task_res.json()
    task_id = task["id"]
    assert task["status"] == "in_progress"
    assert task["assigned_team_id"] == team_id

    # Verify team status transitioned to 'assigned'
    team_check = client.get(f"/api/v1/teams/{team_id}", headers=DEV_OPERATOR_HEADERS)
    assert team_check.json()["current_status"] == "assigned"
    assert team_check.json()["active_tasks_count"] == 1

    # 2. Cannot delete team while assigned to active task
    del_blocked = client.delete(f"/api/v1/teams/{team_id}", headers=DEV_ADMIN_HEADERS)
    assert del_blocked.status_code == 400
    assert "Cannot delete team" in del_blocked.json()["detail"]

    # 3. Complete task via /complete endpoint
    comp_res = client.post(f"/api/v1/tasks/{task_id}/complete", headers=DEV_OPERATOR_HEADERS)
    assert comp_res.status_code == 200
    completed_task = comp_res.json()
    assert completed_task["status"] == "completed"
    assert completed_task["completed_at"] is not None

    # Verify team automatically became 'available' again
    team_freed = client.get(f"/api/v1/teams/{team_id}", headers=DEV_OPERATOR_HEADERS)
    assert team_freed.json()["current_status"] == "available"
    assert team_freed.json()["active_tasks_count"] == 0

    # Clean up team
    client.delete(f"/api/v1/teams/{team_id}", headers=DEV_ADMIN_HEADERS)


def test_task_invalid_incident_or_team_rejection():
    fake_uuid = str(uuid.uuid4())
    # Nonexistent incident
    res = client.post(
        "/api/v1/tasks",
        json={
            "incident_id": fake_uuid,
            "title": "Test Task",
            "description": "Invalid Incident Check",
        },
        headers=DEV_OPERATOR_HEADERS,
    )
    assert res.status_code == 404
    assert "incident not found" in res.json()["detail"].lower()


# ==============================================================================
# Shelters Tests
# ==============================================================================

def test_shelter_lifecycle_and_occupancy_safeguards():
    # 1. Create shelter
    sh_payload = {
        "name": f"Test Relief Camp {uuid.uuid4().hex[:6]}",
        "shelter_type": "School / Community Hall",
        "capacity": 100,
        "current_occupancy": 80,
        "latitude": 26.200,
        "longitude": 91.750,
        "address": "Sector 9 School Grounds",
        "contact_person": "Principal Sen",
        "contact_phone": "+91-9988776655",
        "status": "open",
    }
    create_res = client.post("/api/v1/shelters", json=sh_payload, headers=DEV_OPERATOR_HEADERS)
    assert create_res.status_code == 201
    shelter = create_res.json()
    shelter_id = shelter["id"]
    assert shelter["remaining_capacity"] == 20
    assert shelter["occupancy_pct"] == 80.0

    # 2. Admit within capacity (admit 15)
    admit_res = client.post(
        f"/api/v1/shelters/{shelter_id}/admit",
        json={"count": 15},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert admit_res.status_code == 200
    assert admit_res.json()["current_occupancy"] == 95
    assert admit_res.json()["remaining_capacity"] == 5

    # 3. Admit exceeding capacity (try admitting 10 when only 5 spaces remain) -> expect 400
    exceed_res = client.post(
        f"/api/v1/shelters/{shelter_id}/admit",
        json={"count": 10},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert exceed_res.status_code == 400
    assert "exceeded" in exceed_res.json()["detail"].lower() or "spaces remaining" in exceed_res.json()["detail"].lower()

    # 4. Fill to capacity (admit 5) -> auto-status 'full'
    fill_res = client.post(
        f"/api/v1/shelters/{shelter_id}/admit",
        json={"count": 5},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert fill_res.status_code == 200
    assert fill_res.json()["current_occupancy"] == 100
    assert fill_res.json()["status"] == "full"

    # 5. Discharge occupants (discharge 30) -> auto-status 'open'
    dis_res = client.post(
        f"/api/v1/shelters/{shelter_id}/discharge",
        json={"count": 30},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert dis_res.status_code == 200
    assert dis_res.json()["current_occupancy"] == 70
    assert dis_res.json()["status"] == "open"
    assert dis_res.json()["remaining_capacity"] == 30

    # 6. Discharge exceeding occupancy -> expect 400
    dis_over = client.post(
        f"/api/v1/shelters/{shelter_id}/discharge",
        json={"count": 80},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert dis_over.status_code == 400

    # 7. Cannot delete shelter while occupants exist
    del_blocked = client.delete(f"/api/v1/shelters/{shelter_id}", headers=DEV_ADMIN_HEADERS)
    assert del_blocked.status_code == 400
    assert "Cannot delete shelter" in del_blocked.json()["detail"]

    # 8. Empty shelter and delete
    client.post(
        f"/api/v1/shelters/{shelter_id}/discharge",
        json={"count": 70},
        headers=DEV_OPERATOR_HEADERS,
    )
    del_ok = client.delete(f"/api/v1/shelters/{shelter_id}", headers=DEV_ADMIN_HEADERS)
    assert del_ok.status_code == 200


def test_shelter_validation_occupancy_exceeds_capacity():
    # Cannot create shelter where occupancy > capacity
    res = client.post(
        "/api/v1/shelters",
        json={
            "name": "Invalid Shelter",
            "shelter_type": "Hall",
            "capacity": 50,
            "current_occupancy": 60,  # Exceeds
            "address": "Address 1",
        },
        headers=DEV_OPERATOR_HEADERS,
    )
    assert res.status_code == 422


# ==============================================================================
# Emergency Resources Tests
# ==============================================================================

def test_resource_stockpile_allocation_and_return():
    res_code = f"RES-TEST-{uuid.uuid4().hex[:6].upper()}"
    # 1. Create resource
    res_payload = {
        "resource_code": res_code,
        "name": "Portable Oxygen Concentrators",
        "category": "Medical",
        "quantity_total": 50.0,
        "quantity_available": 50.0,
        "unit": "units",
        "storage_location": "Central Depot Warehouse",
    }
    create_res = client.post("/api/v1/resources", json=res_payload, headers=DEV_OPERATOR_HEADERS)
    assert create_res.status_code == 201
    resource = create_res.json()
    resource_id = resource["id"]
    assert resource["quantity_available"] == 50.0
    assert resource["allocated_quantity"] == 0.0

    # 2. Allocate exceeding available stock -> expect 400
    over_alloc = client.post(
        f"/api/v1/resources/{resource_id}/allocate",
        json={"quantity": 60.0, "destination_location": "Field Clinic"},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert over_alloc.status_code == 400
    assert "exceeds available stock" in over_alloc.json()["detail"].lower()

    # 3. Valid allocation of 20 units
    alloc_res = client.post(
        f"/api/v1/resources/{resource_id}/allocate",
        json={
            "quantity": 20.0,
            "destination_location": "Guwahati Field Medical Post",
            "transport_mode": "Helicopter Air-Drop",
            "notes": "Emergency triage respiratory distress supply",
        },
        headers=DEV_OPERATOR_HEADERS,
    )
    assert alloc_res.status_code == 200
    updated_res = alloc_res.json()
    assert updated_res["quantity_available"] == 30.0
    assert updated_res["allocated_quantity"] == 20.0
    assert len(updated_res["recent_movements"]) >= 1
    assert updated_res["recent_movements"][0]["status"] == "dispatched"

    # 4. Cannot delete resource while allocated
    del_blocked = client.delete(f"/api/v1/resources/{resource_id}", headers=DEV_ADMIN_HEADERS)
    assert del_blocked.status_code == 400

    # 5. Return 20 units to stockpile
    return_res = client.post(
        f"/api/v1/resources/{resource_id}/return",
        json={"quantity": 20.0, "source_location": "Guwahati Field Medical Post"},
        headers=DEV_OPERATOR_HEADERS,
    )
    assert return_res.status_code == 200
    restored_res = return_res.json()
    assert restored_res["quantity_available"] == 50.0
    assert restored_res["allocated_quantity"] == 0.0
    assert restored_res["recent_movements"][0]["status"] == "returned"

    # 6. Delete resource after stock returned
    del_ok = client.delete(f"/api/v1/resources/{resource_id}", headers=DEV_ADMIN_HEADERS)
    assert del_ok.status_code == 200


def test_resource_filter_low_stock():
    res = client.get("/api/v1/resources?low_stock_only=true", headers=DEV_OPERATOR_HEADERS)
    assert res.status_code == 200
    data = res.json()
    for item in data["items"]:
        assert item["quantity_available"] <= 0.25 * item["quantity_total"] + 1e-4
