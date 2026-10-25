# AgentCraft — AI Agent Core Engine (`ai/`)

The `ai/` package provides the autonomous reasoning engine for **AgentCraft**, built for the **AGENTCRAFT 2026 National AI Agent Challenge**.

---

## Architecture Overview

```text
ai/
├── agent.py               # Core AgentCraftAgent, PlanStep, AgentState, execution loop
├── tools/                 # Tool implementations & registry
│   ├── __init__.py        # ToolRegistry, tool discovery & dispatch
│   ├── base.py            # BaseTool abstract class, ToolResult, ToolParameter
│   ├── code_runner.py     # Sandboxed Python execution engine
│   ├── file_manager.py    # Path-traversal safe file system operations
│   ├── data_analyzer.py   # Statistical profiling, schema extraction, outlier detection
│   ├── web_fetcher.py     # HTTP client & structured knowledge retrieval
│   └── verifier.py        # Assertion evaluator (schema, threshold, regex, non-empty)
├── tests/                 # Unit & integration tests for AI agent and tools
│   ├── test_agent.py      # Agent planning, state tracking, and recovery tests
│   ├── test_tools.py      # Tool execution, edge cases, and invalid inputs
│   └── test_verification.py # Verifier assertion rules and validation gates
└── README.md              # Technical specification
```

---

## Core Capabilities

1. **Multi-Step Goal Planning (`AgentCraftAgent.plan`)**:
   - Decomposes high-level instructions into ordered `PlanStep` sequences with tool assignments, expected outcomes, and post-step verification rules.
   - Dual-mode synthesis: Uses LLM (OpenAI / Gemini / Anthropic) when API keys are configured, and a deterministic cognitive planner when offline or in test environments.

2. **State Management (`AgentState`)**:
   - Maintains an isolated session state containing working memory, plan steps, real-time logs, execution trace records, generated artifacts, and metrics.
   - Dynamic parameter substitution allows steps to read outputs from previous steps (e.g., `{last_output}`, `{variable_name}`).

3. **Verifiable Tool Calls**:
   - All tools produce standardized `ToolResult` objects containing status, execution time in milliseconds, output payload, and structured error messages.
   - Every step runs post-execution assertions through `VerifierTool` before state transitions are committed.

4. **Self-Healing Error Recovery (`_attempt_recovery`)**:
   - If a tool fails or verification gates reject an output, AgentCraft activates an automated recovery routine:
     - Normalizes file paths upon sandbox boundary violations.
     - Injects missing execution scopes on code runtime errors.
     - Adjusts verification tolerances dynamically on edge-case thresholds.
     - Enforces a configurable `max_retries_per_step` ceiling.

5. **Sandbox Security**:
   - `FileManagerTool` validates that all operations remain strictly within the configured sandbox directory.
   - `CodeRunnerTool` restricts hazardous built-ins and runs within an isolated local dictionary.

---

## Tool Registry Specifications

| Tool | Actions / Operations | Purpose |
| :--- | :--- | :--- |
| **`code_runner`** | `execute(code, context_vars)` | Executes Python code, captures stdout/stderr, extracts computed variables |
| **`file_manager`** | `read`, `write`, `list`, `exists`, `grep`, `delete` | Safe sandboxed file operations with path-traversal prevention |
| **`data_analyzer`** | `summarize`, `schema`, `outliers`, `aggregate` | Statistical profiling, IQR outlier detection, schema inference |
| **`web_fetcher`** | `fetch`, `search` | Real HTTP GET/POST queries and structured domain knowledge lookup |
| **`verifier`** | `threshold`, `schema`, `regex`, `non_empty`, `expression` | Evaluates assertion rules against intermediate states and outputs |

---

## Quick Example (Python)

```python
from ai.agent import AgentCraftAgent

agent = AgentCraftAgent()
state = agent.run("Analyze the benchmark agent dataset, find latency outliers, and generate a summary report.")

print("Status:", state.status)
print("Completed steps:", state.metrics["completed_steps"])
print("Verified assertions:", state.metrics["verifications_passed"])
print("Artifacts generated:", len(state.artifacts))
```
