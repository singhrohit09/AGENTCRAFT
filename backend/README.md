# AgentCraft Backend Service (`backend/`)

The `backend/` directory houses the RESTful microservice for **AgentCraft**, built on FastAPI and Uvicorn. It exposes endpoints for autonomous agent execution, interactive step control, session state inspection, tool catalogs, standalone verification, and automated benchmark scoring.

---

## Directory Structure

```text
backend/
├── app.py               # Main FastAPI entry point & middleware configuration
├── requirements.txt     # Python backend dependencies
├── README.md            # Backend documentation & API guide
├── routes/              # API route definitions
│   ├── __init__.py      # Route exports
│   └── agent_routes.py  # REST endpoints for agent operations
├── services/            # Business logic and lifecycle orchestration
│   ├── __init__.py      # Service exports
│   ├── agent_service.py # Session lifecycle and agent execution service
│   └── benchmark_service.py # Automated capability benchmark suite
└── tests/               # Backend endpoint and error handling tests
    ├── test_api.py      # Happy-path REST API test cases
    └── test_failures.py # Error handling, 404s, invalid payloads, edge cases
```

---

## API Endpoints

| Method | Endpoint | Description | Request Body / Params |
| :--- | :--- | :--- | :--- |
| `GET` | `/` | Service root and competition metadata | None |
| `GET` | `/api/health` | System health, uptime, tool count, and active sessions | None |
| `POST` | `/api/agent/run` | Autonomous execution of a goal end-to-end | `{"goal": str, "initial_memory": dict}` |
| `POST` | `/api/agent/sessions` | Create a new interactive session | `{"goal": str, "initial_memory": dict}` |
| `GET` | `/api/agent/sessions` | List active sessions | None |
| `GET` | `/api/agent/sessions/{id}` | Inspect full session state, logs, trace, artifacts | Path: `id` |
| `DELETE` | `/api/agent/sessions/{id}`| Delete a session | Path: `id` |
| `POST` | `/api/agent/sessions/{id}/plan` | Generate multi-step plan for a session | Path: `id` |
| `POST` | `/api/agent/sessions/{id}/step` | Execute a single plan step by index | `{"step_index": int}` |
| `GET` | `/api/agent/tools` | Catalog of available agent tools and parameter schemas | None |
| `POST` | `/api/agent/verify` | Run standalone verification assertions on subject data | `{"assertions": list, "subject": any}` |
| `POST` | `/api/agent/benchmark` | Run AGENTCRAFT 2026 Core Capability Benchmark | None |

---

## Running the Backend

From the repository root with virtual environment activated:

```bash
# Activate virtual environment (Windows)
.\.venv\Scripts\Activate.ps1

# Run development server
python -m backend.app
# OR via uvicorn directly
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

The interactive OpenAPI Swagger UI is available at:
`http://127.0.0.1:8000/docs`
