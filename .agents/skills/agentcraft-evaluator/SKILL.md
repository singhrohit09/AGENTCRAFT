---
name: agentcraft-evaluator
description: >-
  Use this skill to evaluate AgentCraft agent performance, run capability benchmarks,
  and verify agent accuracy, tool dispatch precision, and recovery rates against AGENTCRAFT 2026 challenge standards.
---

# AgentCraft Evaluator Skill

This skill provides the standard operating procedure for measuring, benchmarking, and validating the AgentCraft autonomous agent.

## Evaluation Workflow

### 1. Execute the Automated Capability Suite
Run the standardized benchmark via Python CLI or backend endpoint:

```bash
# Python CLI invocation
.\.venv\Scripts\python.exe -c "from backend.services.benchmark_service import benchmark_service; import json; print(json.dumps(benchmark_service.run_suite(), indent=2))"
```

Or via REST API:
```bash
curl -X POST http://127.0.0.1:8000/api/agent/benchmark
```

### 2. Verify Benchmark Metrics
Validate that the evaluation meets the minimum competition thresholds:
- **Completion Rate**: Must be >= 90%
- **Tool Dispatch Accuracy**: Must be 100% (zero unregistered tool calls)
- **Assertion Verification**: All intermediate state assertions must report `verified: true`
- **Error Recovery**: Any path traversal or runtime faults must successfully trigger self-healing

### 3. Run Verification on Custom Artifacts
To evaluate a generated artifact or intermediate result against custom acceptance criteria:

```python
from ai.tools.verifier import VerifierTool

verifier = VerifierTool()
result = verifier.run(
    assertions=[
        {"type": "threshold", "key": "accuracy", "operator": ">=", "value": 95},
        {"type": "non_empty", "key": "summary"},
    ],
    subject={"accuracy": 98.2, "summary": "All steps executed cleanly."},
)
print("Verification Status:", result.output["verified"])
```
