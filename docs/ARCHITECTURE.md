# AgentCraft — System Architecture

**AgentCraft** is an autonomous AI agent engineering framework built for the **AGENTCRAFT 2026 National AI Agent Challenge**. It combines multi-step goal decomposition, typed tool dispatch, deterministic verification gates, sandboxed isolation, and self-healing error recovery.

---

## 1. High-Level System Architecture

```mermaid
graph TD
    User([User / Operator / Judge]) -->|Goals & Tasks| UI[Frontend Mission Control]
    UI -->|REST / WebSocket| Gateway[FastAPI Backend Gateway]
    
    subgraph "Backend Orchestration Layer"
        Gateway --> AgentService[Agent Service]
        Gateway --> BenchmarkService[Benchmark Service]
        AgentService --> SessionStore[(Session State & Working Memory)]
    end

    subgraph "AI Reasoning Core (ai/)"
        AgentService --> Planner[Goal Planner & Synthesizer]
        Planner --> ExecutionEngine[Execution Engine]
        ExecutionEngine --> Recovery[Self-Healing Recovery Loop]
        ExecutionEngine --> VerifierEngine[Verification Subsystem]
    end

    subgraph "Tool Dispatch & Sandbox Ecosystem"
        ExecutionEngine --> CodeRunner[Code Runner Tool]
        ExecutionEngine --> FileManager[File Manager Tool]
        ExecutionEngine --> DataAnalyzer[Data Analyzer Tool]
        ExecutionEngine --> WebFetcher[Web Fetcher Tool]
        ExecutionEngine --> Verifier[Verifier Tool]
        
        FileManager --> Sandbox[(Sandboxed Filesystem)]
        CodeRunner --> IsolatedScope[Isolated Python Scope]
    end

    VerifierEngine -->|Verified Assertions| ExecutionEngine
    ExecutionEngine -->|Trace & Artifacts| SessionStore
    SessionStore -->|Telemetry Stream| UI
```

---

## 2. Component Breakdown

### 2.1 Frontend Mission Control (`frontend/`)
- **Technology**: React 19, Vite, Vanilla CSS design system (custom cyberpunk-glass aesthetic).
- **Responsibilities**:
  - Goal entry console with preset challenge templates.
  - Interactive multi-step execution plan timeline (DAG/linear).
  - Real-time terminal streaming logs and status indicators.
  - Deep-dive audit trace inspector displaying inputs, outputs, execution latencies, and assertion proofs.
  - One-click AGENTCRAFT 2026 capability benchmark dashboard.
  - Tool catalog browser showing available parameter schemas.

### 2.2 Backend Gateway & Orchestrator (`backend/`)
- **Technology**: FastAPI, Uvicorn, Pydantic v2, Python 3.12.
- **Responsibilities**:
  - Exposes RESTful endpoints for autonomous execution, session lifecycle management, step-by-step control, and benchmark running.
  - Houses `AgentService` for session state tracking and persistence.
  - Implements `BenchmarkService` for quantitative evaluation against competition criteria.
  - Enforces CORS policies, input validation, and structured error responses.

### 2.3 AI Reasoning Core (`ai/`)
- **Technology**: Pure Python reasoning engine with dual-mode execution (LLM-enabled and cognitive-deterministic).
- **Responsibilities**:
  - **Goal Decomposition**: Analyzes user intent and produces ordered, dependency-aware `PlanStep` graphs.
  - **Execution Engine**: Resolves dynamic memory variables (e.g. `{last_output}`, `{variable_name}`) and dispatches tools.
  - **Verification Subsystem**: Evaluates multi-criteria assertions (thresholds, schemas, regex, non-empty, expressions) before accepting step outputs.
  - **Self-Healing Recovery**: Dynamically catches runtime exceptions, path violations, or verification rejections, applying recovery tactics (path normalization, context defaults, tolerance adjustment) within strict retry bounds.
  - **Result Synthesis**: Compiles complete execution traces, generated artifacts, and confidence scores into verifiable audit records.

### 2.4 Tool Ecosystem (`ai/tools/`)
All tools inherit from `BaseTool` and return standardized `ToolResult` schemas:
- `code_runner`: Sandboxed Python execution capturing stdout/stderr and exporting generated variables.
- `file_manager`: Safe file creation, reading, directory listing, and regex search with path-traversal prevention.
- `data_analyzer`: Statistical profiling, IQR outlier detection, column summaries, and aggregations.
- `web_fetcher`: Real HTTP requests with fallbacks to offline structured knowledge retrieval for deterministic testing.
- `verifier`: Post-step assertion engine evaluating contract compliance.

---

## 3. Data Flow & Execution Sequence

```mermaid
sequenceDiagram
    autonumber
    actor User
    participant UI as Frontend UI
    participant API as FastAPI Backend
    participant Agent as AgentCraft Engine
    participant Tool as Tool Registry
    participant Verifier as Verifier Subsystem

    User->>UI: Submit Task Goal
    UI->>API: POST /api/agent/run
    API->>Agent: agent.run(goal)
    Agent->>Agent: plan(goal) -> PlanSteps[]
    
    loop For each PlanStep
        Agent->>Agent: Resolve Arguments from Memory
        Agent->>Tool: execute(tool_name, args)
        Tool-->>Agent: ToolResult (output, duration_ms)
        Agent->>Verifier: verify_step(assertions, output)
        alt Assertions Passed
            Verifier-->>Agent: Verified (True)
            Agent->>Agent: Update Memory & Artifacts
        else Assertions Failed
            Verifier-->>Agent: Failed (False)
            Agent->>Agent: _attempt_recovery(step, error)
        end
    end

    Agent->>Agent: Synthesize Final Output & Metrics
    Agent-->>API: AgentState (Trace, Artifacts, Metrics)
    API-->>UI: 200 OK (JSON Response)
    UI->>User: Render Interactive Visual Plan & Artifacts
```

---

## 4. Security & Sandboxing Model

1. **Path-Traversal Guards**: `FileManagerTool` normalizes all relative file paths against `temp_sandbox` and rejects attempts to write or read outside designated root boundaries.
2. **Execution Scope Isolation**: `CodeRunnerTool` runs scripts in an isolated dictionary scope with standard output redirection and restricted globals, preventing unauthorized environment destruction.
3. **Secret Segregation**: API keys (`OPENAI_API_KEY`, `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) reside exclusively in environment variables (`.env`) and are never leaked to frontend clients or persisted traces.
