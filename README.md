# AgentCraft ⚡ & RakshaGrid 🛡️

[![Python 3.12](https://img.shields.io/badge/Python-3.12-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React 19](https://img.shields.io/badge/React-19-61DAFB.svg)](https://react.dev/)
[![Vite](https://img.shields.io/badge/Vite-8.0+-646CFF.svg)](https://vitejs.dev/)
[![Test Suite](https://img.shields.io/badge/Tests-69%20Passed-10b981.svg)]()
[![Benchmark Verdict](https://img.shields.io/badge/Benchmark-CERTIFIED%20(100%25)-00f0ff.svg)]()
[![Challenge](https://img.shields.io/badge/Challenge-AGENTCRAFT%202026-a855f7.svg)]()

> **AgentCraft** is an autonomous AI agent engineering platform developed for the **AGENTCRAFT 2026 National AI Agent Challenge**, powering **RakshaGrid** — an emergency operations and disaster intelligence platform for hazard monitoring, CAP alerting, and rescue coordination. See [docs/RAKSHAGRID.md](docs/RAKSHAGRID.md) for full subsystem documentation.

---

## 🎯 Problem Statement & Core Mission

Conventional LLM agents suffer from three major points of failure:
1. **Unverified Hallucinations**: Claiming solutions without executing real code, inspecting live files, or asserting correctness.
2. **Fragility & Crash Prone**: Breaking at the first tool error or path issue rather than diagnosing and self-healing.
3. **Black-Box Outputs**: Providing conversational text without reproducible execution traces, generated artifacts, or measurable verification proofs.

**AgentCraft** solves this by enforcing a closed **Plan-Act-Verify-Heal** cognitive lifecycle:
- **Dynamic Multi-Step Planning**: Decomposes high-level instructions into an ordered DAG/linear plan with explicit tool assignments and acceptance criteria.
- **Real Tool Execution**: Dispatches sandboxed Python code runners, path-safe file managers, statistical dataset analyzers, and knowledge retrieval fetchers.
- **Contract-Based Verification**: Runs multi-criteria assertion checks (thresholds, schemas, regex, non-empty, expressions) on intermediate step outputs before transitioning state.
- **Self-Healing Error Recovery**: Autonomously corrects path traversal violations, injects missing runtime scopes, and adjusts tolerance thresholds when exceptions arise.
- **Hybrid Execution Engine**: Seamlessly executes using live LLMs (OpenAI, Gemini, Anthropic) when configured, or operates with 100% reliability in offline/deterministic mode with zero missing API key errors.

---

## 🏛️ Project Structure

```text
AgentCraft/
├── .agents/
│   └── skills/
│       ├── agentcraft-evaluator/        # Capability benchmark evaluation runbook
│       └── agentcraft-tool-builder/     # Tool authoring & sandboxing guidelines
├── ai/
│   ├── README.md                        # AI reasoning engine specifications
│   ├── agent.py                         # Core AgentCraftAgent, PlanStep, AgentState
│   ├── tools/
│   │   ├── __init__.py                  # Central tool registry & dispatcher
│   │   ├── base.py                      # BaseTool, ToolResult, ToolParameter
│   │   ├── code_runner.py               # Sandboxed Python execution engine
│   │   ├── file_manager.py              # Path-traversal safe file operations
│   │   ├── data_analyzer.py             # Statistical profiling & IQR outlier detection
│   │   ├── web_fetcher.py               # HTTP client & structured knowledge retrieval
│   │   └── verifier.py                  # Multi-criteria assertion evaluator
│   └── tests/
│       ├── test_agent.py                # Agent planning, state tracking, and recovery
│       ├── test_tools.py                # Tool unit tests, sandboxing, and edge cases
│       └── test_verification.py         # Schema, threshold, and regex assertion tests
├── backend/
│   ├── README.md                        # Backend service documentation
│   ├── requirements.txt                 # FastAPI, Pydantic v2, SQLAlchemy, Alembic, psycopg
│   ├── app.py                           # FastAPI application entrypoint & static mount
│   ├── database/                        # Database sessions, connection pools & migrations
│   │   ├── session.py                   # Engine, session factory & connection test
│   │   └── migrations/                  # Alembic versions & 0002_phase2_incident_management
│   ├── rakshagrid/                      # RakshaGrid disaster intelligence subsystem
│   │   ├── config.py                    # Settings & environment validation
│   │   ├── auth.py                      # Role-based authorization & dev auth mode
│   │   ├── models.py                    # 11 PostgreSQL SQLAlchemy ORM models
│   │   ├── incident_schemas.py          # Phase 2 incident CRUD Pydantic v2 schemas
│   │   ├── incident_service.py          # Transactional incident & audit timeline service
│   │   ├── schemas.py                   # Phase 1 diagnostic schemas
│   │   └── service.py                   # Diagnostic checks & disaster telemetry
│   ├── routes/
│   │   ├── __init__.py                  # Route exports
│   │   ├── agent_routes.py              # AgentCraft agent REST API
│   │   ├── incident_routes.py           # Phase 2 /api/v1/incidents REST endpoints
│   │   └── rakshagrid_routes.py         # RakshaGrid disaster operations API
│   ├── scripts/
│   │   └── seed_dev_data.py             # Deterministic development incident seeder
│   ├── services/
│   │   ├── __init__.py                  # Service exports
│   │   ├── agent_service.py             # Session lifecycle & execution service
│   │   └── benchmark_service.py         # AGENTCRAFT 2026 benchmark test suite
│   └── tests/
│       ├── test_api.py                  # API happy-path & workflow tests
│       ├── test_failures.py             # 404s, invalid payloads, and validation errors
│       ├── test_incidents_api.py        # Phase 2 Incident API & persistence tests (16 tests)
│       └── test_rakshagrid_api.py       # RakshaGrid API & database models tests
├── docs/
│   ├── RAKSHAGRID.md                    # RakshaGrid disaster platform architecture & setup
│   ├── ARCHITECTURE.md                  # Detailed system architecture & Mermaid diagrams
│   ├── AGENT_DESIGN.md                  # Cognitive model, state machine, and self-healing
│   ├── API.md                           # REST API reference and cURL examples
│   ├── EVALUATION.md                    # Benchmark metrics, scoring, and reproducibility
│   └── LIMITATIONS.md                   # Current boundaries, assumptions, and roadmap
├── frontend/                            # Vite + React Mission Control dashboard
│   ├── src/
│   │   ├── App.jsx                      # Interactive dashboard with timeline & telemetry
│   │   ├── index.css                    # Cyberpunk-glass design system
│   │   └── main.jsx                     # Application bootstrap
│   ├── index.html                       # Semantic HTML5 entry with Outfit & Inter fonts
│   └── vite.config.js                   # Vite config with backend API proxy
├── .env.example                         # Safe configuration template
├── .gitignore                           # Git ignore rules for Python, Node, & secrets
├── AGENTS.md                            # Repository rules & standards for AI assistants
├── README.md                            # Project overview & quickstart
├── SKILLS_SETUP.md                      # Antigravity skills guide & configurations
└── workflow.md                          # Development, testing, & release runbook
```

---

## ⚡ Quickstart Guide

### 1. Prerequisites
- Python 3.12+
- Node.js 20+ & npm

### 2. Backend Setup
```bash
# Clone the repository
git clone <repository-url>
cd AgentCraft

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1   # On Windows
# source .venv/bin/activate    # On Linux/macOS

# Install dependencies
pip install -r backend/requirements.txt

# Configure environment variables
copy .env.example .env
```

### 3. Frontend Setup
```bash
cd frontend
npm install
cd ..
```

### 4. Running the Complete System

**Option A — Concurrent Dev Servers**:
- **Backend API**:
  ```bash
  python -m backend.app
  # Listening on http://127.0.0.1:8000 (OpenAPI docs at /docs)
  ```
- **Frontend UI**:
  ```bash
  cd frontend
  npm run dev
  # Listening on http://localhost:3000
  ```

**Option B — Single-Port Production Mode**:
```bash
# Build frontend
cd frontend
npm run build
cd ..

# Start backend (serves both API and UI)
python -m backend.app
# Open http://127.0.0.1:8000 in your browser
```

---

## 🧪 Testing & Verification

Run the test suite covering agent planning, tool operations, sandbox boundaries, API endpoints, and failure cases:

```bash
# Run all 42 tests
.\.venv\Scripts\python.exe -m pytest ai/tests backend/tests -v
```

### Run Automated Capability Benchmark
```bash
.\.venv\Scripts\python.exe -c "from backend.services.benchmark_service import benchmark_service; import json; print(json.dumps(benchmark_service.run_suite(), indent=2))"
```

Expected Benchmark Output:
```json
{
  "suite_name": "AGENTCRAFT 2026 Core Capability Benchmark",
  "total_tasks": 3,
  "passed_tasks": 3,
  "completion_rate_pct": 100.0,
  "total_steps_executed": 12,
  "total_verifications_passed": 7,
  "total_retries": 0,
  "system_verdict": "CERTIFIED"
}
```

---

## 📊 Key Working Features

1. **Mission Control Console**:
   - Interactive goal input with 1-click preset templates.
   - Dual execution modes: Autonomous Run (instant end-to-end) or Step Mode (interactive step-by-step execution).
2. **Live Multi-Step Plan Timeline**:
   - Visual step sequence with tool tags, execution status, latency timing, and verification check badges.
3. **Real-Time Terminal Streaming**:
   - Live color-coded logs showing tool arguments, stdout/stderr, assertion proofs, and recovery events.
4. **Audit Trace & Telemetry**:
   - Deep inspection of every executed step, inputs, outputs, duration, and pass/fail assertion details.
5. **Artifacts & Working Memory Store**:
   - Live browsing of generated files (Markdown reports, JSON datasets) and working memory variables.
6. **Integrated Capability Benchmark**:
   - In-app evaluation suite that validates agent capabilities against AGENTCRAFT 2026 challenge standards.
7. **Tool Schema Catalog**:
   - Introspection of registered tools (`code_runner`, `file_manager`, `data_analyzer`, `web_fetcher`, `verifier`).

---

## 🛡️ Security & Sandboxing

- **Path Normalization**: Rejects and sanitizes path traversals attempting to escape `./temp_sandbox`.
- **Restricted Execution**: Code execution runs within an isolated namespace with standard library mathematical modules, blocking OS-level corruption.
- **Zero Hardcoded Secrets**: All credentials reside in `.env`. Safe defaults work out of the box with zero external API dependencies required.

---

## 📖 Detailed Documentation

- [System Architecture](docs/ARCHITECTURE.md)
- [Agent Cognitive Design](docs/AGENT_DESIGN.md)
- [REST API Specification](docs/API.md)
- [Evaluation & Benchmarks](docs/EVALUATION.md)
- [System Limitations & Roadmap](docs/LIMITATIONS.md)
- [Agent Repository Guidelines](AGENTS.md)
- [Skills Configuration Guide](SKILLS_SETUP.md)
- [Development Workflow Runbook](workflow.md)

---

## 🏆 AGENTCRAFT 2026 National AI Agent Challenge

Built for the **AGENTCRAFT 2026 National AI Agent Challenge**, demonstrating deterministic rigor, self-healing execution, and verifiable AI agent problem-solving.
