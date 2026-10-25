# AgentCraft — Evaluation & Benchmarking Methodology

This document outlines the rigorous quantitative and qualitative framework used to measure, evaluate, and benchmark **AgentCraft** for the **AGENTCRAFT 2026 National AI Agent Challenge**.

---

## 1. Primary Evaluation Metrics

AgentCraft is evaluated across five primary dimensions:

| Metric | Symbol | Definition | Minimum Challenge Target |
| :--- | :--- | :--- | :--- |
| **Goal Completion Rate** | $\text{GCR}$ | Percentage of tasks executed with all planned steps succeeded and verified | $\ge 90\%$ |
| **Tool Call Precision** | $\text{TCP}$ | Ratio of valid, correctly typed tool executions to total tool dispatches | $100\%$ |
| **Verification Pass Rate** | $\text{VPR}$ | Proportion of post-step assertions verified without hallucination | $\ge 95\%$ |
| **Self-Healing Recovery Rate** | $\text{SHRR}$ | Proportion of faulted steps successfully recovered before retry limits | $\ge 80\%$ |
| **End-to-End Latency** | $\text{E2E}$ | Wall-clock execution time per multi-step workflow | $\le 1000\text{ ms (offline)}$, $\le 15\text{ s (LLM)}$ |

---

## 2. Benchmark Task Suite

The AgentCraft benchmark test harness (`backend/services/benchmark_service.py`) tests the agent across diverse real-world engineering workflows:

### Task 1: Dataset Outlier Detection & Report Synthesis
- **Domain**: Automated Data Science & Telemetry Inspection.
- **Workflow**:
  1. Persists raw telemetry records to the sandboxed file system.
  2. Infers data schemas and field data types.
  3. Executes an Interquartile Range (IQR) outlier filter on latency metrics.
  4. Computes descriptive statistics (mean, median, stdev, nulls).
  5. Generates and verifies a structured Markdown report.
- **Verification Gates**: Validates non-zero byte writes, schema dictionary completeness, and outlier boundary math.

### Task 2: Algorithmic Invariant Computation & Verification
- **Domain**: Dynamic Code Synthesis & Mathematical Logic.
- **Workflow**:
  1. Executes a safe Python script computing numerical sequences.
  2. Evaluates formal invariants and value inequalities.
  3. Writes and audits JSON computational artifacts.
- **Verification Gates**: Asserts count of generated terms, exact sum value, and variable presence.

### Task 3: Domain Research & Acceptance Gating
- **Domain**: Information Retrieval & Policy Enforcement.
- **Workflow**:
  1. Queries the knowledge retrieval tool for architectural specifications.
  2. Synthesizes a model solution configuration.
  3. Runs acceptance gate assertions on confidence and readiness.
  4. Exports validated configuration artifacts.
- **Verification Gates**: Ensures query match count $\ge 1$ and zero assertion failures.

---

## 3. Running the Benchmark Suite

### CLI Mode (Python):
```bash
.\.venv\Scripts\python.exe -c "from backend.services.benchmark_service import benchmark_service; import json; print(json.dumps(benchmark_service.run_suite(), indent=2))"
```

### Automated Pytest Suite:
```bash
.\.venv\Scripts\python.exe -m pytest ai/tests backend/tests -v
```

### REST API Invocations:
```bash
curl -X POST http://127.0.0.1:8000/api/agent/benchmark
```

### UI Mission Control:
Navigate to `http://localhost:3000` (or `http://127.0.0.1:8000`), open the **Benchmark Suite** tab, and click **Execute Evaluation Benchmark**.

---

## 4. Current Certified Benchmark Results

Execution against the standardized suite generates the following certified score:

```json
{
  "suite_name": "AGENTCRAFT 2026 Core Capability Benchmark",
  "total_tasks": 3,
  "passed_tasks": 3,
  "completion_rate_pct": 100.0,
  "total_steps_executed": 12,
  "total_verifications_passed": 7,
  "total_retries": 0,
  "suite_duration_ms": 78.4,
  "system_verdict": "CERTIFIED"
}
```
