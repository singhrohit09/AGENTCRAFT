"""
Tests for AgentCraft Backend REST API Endpoints
Validates health, autonomous execution, sessions, step execution, tools, verification, and benchmarks.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app import app

client = TestClient(app)


def test_root_endpoint():
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert data["project"] == "AgentCraft"
    assert data["status"] == "online"


def test_health_check_endpoint():
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["registered_tools_count"] >= 5
    assert "uptime_seconds" in data


def test_list_tools_endpoint():
    response = client.get("/api/agent/tools")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tools"] >= 5
    tool_names = [t["name"] for t in data["tools"]]
    assert "code_runner" in tool_names
    assert "file_manager" in tool_names
    assert "verifier" in tool_names


def test_run_autonomous_goal_api():
    payload = {
        "goal": "Compute mathematical fibonacci sequence and verify output",
        "initial_memory": {"seed": 42},
    }
    response = client.post("/api/agent/run", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["status"] == "completed"
    assert len(data["plan"]) >= 3
    assert len(data["execution_trace"]) >= 3
    assert data["metrics"]["completed_steps"] >= 3


def test_interactive_session_workflow():
    # 1. Create Session
    create_resp = client.post("/api/agent/sessions", json={"goal": "Analyze dataset of agents and detect outliers"})
    assert create_resp.status_code == 201
    session_id = create_resp.json()["session_id"]

    # 2. Generate Plan
    plan_resp = client.post(f"/api/agent/sessions/{session_id}/plan")
    assert plan_resp.status_code == 200
    total_steps = plan_resp.json()["total_steps"]
    assert total_steps >= 4

    # 3. Step execution
    step_resp = client.post(f"/api/agent/sessions/{session_id}/step", json={"step_index": 0})
    assert step_resp.status_code == 200
    step_data = step_resp.json()["step"]
    assert step_data["status"] == "succeeded"

    # 4. Inspect Session State
    inspect_resp = client.get(f"/api/agent/sessions/{session_id}")
    assert inspect_resp.status_code == 200
    state_data = inspect_resp.json()
    assert state_data["session_id"] == session_id
    assert len(state_data["execution_trace"]) == 1

    # 5. List Sessions
    list_resp = client.get("/api/agent/sessions")
    assert list_resp.status_code == 200
    assert any(s["session_id"] == session_id for s in list_resp.json()["sessions"])

    # 6. Delete Session
    del_resp = client.delete(f"/api/agent/sessions/{session_id}")
    assert del_resp.status_code == 200
    assert "deleted" in del_resp.json()["message"]


def test_standalone_verification_endpoint():
    payload = {
        "subject": {"accuracy": 98.5, "latency_ms": 110},
        "assertions": [
            {"type": "threshold", "key": "accuracy", "operator": ">=", "value": 90},
            {"type": "threshold", "key": "latency_ms", "operator": "<=", "value": 200},
        ],
    }
    response = client.post("/api/agent/verify", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["verified"] is True
    assert data["passed_count"] == 2


def test_benchmark_endpoint():
    response = client.post("/api/agent/benchmark")
    assert response.status_code == 200
    data = response.json()
    assert data["total_tasks"] == 3
    assert data["passed_tasks"] == 3
    assert data["completion_rate_pct"] == 100.0
    assert data["system_verdict"] == "CERTIFIED"
