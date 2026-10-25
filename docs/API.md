# AgentCraft — REST API Specification

The AgentCraft backend exposes a REST API powered by FastAPI, with automatic OpenAPI documentation available at `/docs` and schema definitions at `/redoc`.

---

## 1. System Endpoints

### 1.1 Root Status
- **Method**: `GET`
- **Path**: `/`
- **Response**:
```json
{
  "project": "AgentCraft",
  "competition": "AGENTCRAFT 2026 National AI Agent Challenge",
  "status": "online",
  "version": "1.0.0",
  "docs": "/docs",
  "health": "/api/health"
}
```

### 1.2 Health Check & Diagnostic Telemetry
- **Method**: `GET`
- **Path**: `/api/health`
- **Response**:
```json
{
  "status": "healthy",
  "service": "AgentCraft",
  "uptime_seconds": 124.52,
  "python_version": "3.12.10",
  "registered_tools_count": 5,
  "active_sessions_count": 2,
  "environment": "development",
  "execution_mode": "hybrid"
}
```

---

## 2. Autonomous Execution Endpoints

### 2.1 Run Autonomous Goal
Executes an end-to-end multi-step agent workflow.

- **Method**: `POST`
- **Path**: `/api/agent/run`
- **Request Body**:
```json
{
  "goal": "Analyze dataset of agents, detect latency outliers, and generate summary report",
  "initial_memory": {
    "benchmark_environment": "AGENTCRAFT-2026"
  }
}
```
- **Response (200 OK)**:
```json
{
  "success": true,
  "session_id": "a1b2c3d4",
  "status": "completed",
  "metrics": {
    "total_steps": 5,
    "completed_steps": 5,
    "tool_calls": 5,
    "retries": 0,
    "verifications_passed": 5,
    "verifications_failed": 0,
    "total_duration_ms": 38.45
  },
  "artifacts": [
    {
      "type": "file",
      "path": "reports/agent_evaluation_summary.md",
      "step_id": 5,
      "title": "Generate Comprehensive Evaluation Report"
    }
  ],
  "plan": [ ... ],
  "execution_trace": [ ... ],
  "logs": [ ... ],
  "final_output": {
    "summary": "AgentCraft executed 5/5 steps with 5 verified assertions in 38.45 ms."
  }
}
```

---

## 3. Interactive Session Endpoints

### 3.1 Create Interactive Session
- **Method**: `POST`
- **Path**: `/api/agent/sessions`
- **Request Body**:
```json
{
  "goal": "Compute mathematical fibonacci sequence and verify output"
}
```
- **Response (201 Created)**:
```json
{
  "session_id": "9f8e7d6c",
  "goal": "Compute mathematical fibonacci sequence and verify output",
  "status": "idle",
  "created_at": "[09:15:00] Session initialized with goal: '...'"
}
```

### 3.2 Generate Session Plan
- **Method**: `POST`
- **Path**: `/api/agent/sessions/{session_id}/plan`
- **Response (200 OK)**:
```json
{
  "session_id": "9f8e7d6c",
  "total_steps": 3,
  "plan": [
    {
      "step_id": 1,
      "title": "Execute Algorithmic Calculation",
      "tool_name": "code_runner",
      "tool_args": { ... },
      "status": "pending"
    }
  ]
}
```

### 3.3 Execute Single Step
- **Method**: `POST`
- **Path**: `/api/agent/sessions/{session_id}/step`
- **Request Body**:
```json
{
  "step_index": 0
}
```
- **Response (200 OK)**:
```json
{
  "session_id": "9f8e7d6c",
  "step": {
    "step_id": 1,
    "status": "succeeded",
    "duration_ms": 4.12,
    "result": { ... },
    "verification": { "verified": true, "passed_count": 2 }
  },
  "session_status": "running",
  "metrics": { ... }
}
```

### 3.4 Inspect Session
- **Method**: `GET`
- **Path**: `/api/agent/sessions/{session_id}`
- **Response (200 OK)**: Full session state including memory, artifacts, logs, and trace.

### 3.5 Delete Session
- **Method**: `DELETE`
- **Path**: `/api/agent/sessions/{session_id}`
- **Response (200 OK)**:
```json
{
  "message": "Session '9f8e7d6c' deleted successfully."
}
```

---

## 4. Tool & Verification Endpoints

### 4.1 List Registered Tools
- **Method**: `GET`
- **Path**: `/api/agent/tools`
- **Response (200 OK)**:
```json
{
  "total_tools": 5,
  "tools": [
    {
      "name": "code_runner",
      "description": "Executes a Python code block and returns stdout, stderr, and exported variables.",
      "parameters": { ... }
    },
    {
      "name": "file_manager",
      "description": "Performs safe file operations (read, write, list, grep, exists, delete) within the sandbox.",
      "parameters": { ... }
    }
  ]
}
```

### 4.2 Standalone Verification Gate
- **Method**: `POST`
- **Path**: `/api/agent/verify`
- **Request Body**:
```json
{
  "subject": { "accuracy": 98.2, "latency_ms": 115 },
  "assertions": [
    { "type": "threshold", "key": "accuracy", "operator": ">=", "value": 90 },
    { "type": "threshold", "key": "latency_ms", "operator": "<=", "value": 200 }
  ]
}
```
- **Response (200 OK)**:
```json
{
  "verified": true,
  "total_assertions": 2,
  "passed_count": 2,
  "failed_count": 0,
  "details": [
    {
      "assertion_id": 1,
      "passed": true,
      "message": "Evaluated: 98.2 >= 90.0 -> True"
    },
    {
      "assertion_id": 2,
      "passed": true,
      "message": "Evaluated: 115.0 <= 200.0 -> True"
    }
  ]
}
```

---

## 5. Evaluation Benchmark Endpoint

### 5.1 Run Challenge Capability Benchmark
- **Method**: `POST` (or `GET`)
- **Path**: `/api/agent/benchmark`
- **Response (200 OK)**:
```json
{
  "suite_name": "AGENTCRAFT 2026 Core Capability Benchmark",
  "total_tasks": 3,
  "passed_tasks": 3,
  "completion_rate_pct": 100.0,
  "total_steps_executed": 11,
  "total_verifications_passed": 7,
  "total_retries": 0,
  "suite_duration_ms": 82.14,
  "system_verdict": "CERTIFIED",
  "tasks": [ ... ]
}
```

---

## 6. Example cURL Commands

```bash
# Health Check
curl http://127.0.0.1:8000/api/health

# Run Autonomous Goal
curl -X POST http://127.0.0.1:8000/api/agent/run \
  -H "Content-Type: application/json" \
  -d '{"goal": "Compute mathematical fibonacci sequence and verify output"}'

# Run Benchmark
curl -X POST http://127.0.0.1:8000/api/agent/benchmark
```
