"""
Tests for AgentCraft API Failure Modes and Edge Cases
Validates 404 not found, 422 unprocessable entities, invalid payloads, and boundary errors.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_missing_session_404():
    response = client.get("/api/agent/sessions/non_existent_session_123")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


def test_delete_missing_session_404():
    response = client.delete("/api/agent/sessions/non_existent_session_999")
    assert response.status_code == 404


def test_invalid_step_index_400():
    # Create a session first
    create_resp = client.post("/api/agent/sessions", json={"goal": "Verify invalid step handling"})
    session_id = create_resp.json()["session_id"]
    client.post(f"/api/agent/sessions/{session_id}/plan")

    # Step index out of range
    step_resp = client.post(f"/api/agent/sessions/{session_id}/step", json={"step_index": 999})
    assert step_resp.status_code == 400
    assert "invalid step index" in step_resp.json()["detail"].lower()


def test_plan_missing_session_404():
    response = client.post("/api/agent/sessions/ghost_session/plan")
    assert response.status_code == 404


def test_run_empty_goal_validation_error():
    # goal has min_length=3
    response = client.post("/api/agent/run", json={"goal": "a"})
    assert response.status_code == 422


def test_verify_empty_assertions_validation_error():
    response = client.post("/api/agent/verify", json={"assertions": [], "subject": {}})
    assert response.status_code == 422


def test_invalid_json_payload_422():
    response = client.post(
        "/api/agent/run",
        content="not valid json",
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 422
