"""
AgentCraft Evaluation Benchmark Service
Executes automated standardized benchmarks assessing planning,
tool accuracy, verification gates, and recovery performance.
"""

import time
from typing import Any, Dict, List
from ai.agent import AgentCraftAgent
from ai.tools import ToolRegistry


class BenchmarkService:
    """Runs automated challenge suites to quantify AgentCraft capabilities."""

    BENCHMARK_TASKS = [
        {
            "id": "task_1_data_profiling",
            "title": "Dataset Outlier Detection & Report Synthesis",
            "goal": "Analyze dataset of agents, detect latency outliers, and generate summary report",
            "expected_artifacts": 1,
            "min_completed_steps": 4,
        },
        {
            "id": "task_2_algorithmic_invariants",
            "title": "Algorithmic Invariant Computation & Verification",
            "goal": "Compute mathematical fibonacci sequence and verify output",
            "expected_artifacts": 1,
            "min_completed_steps": 3,
        },
        {
            "id": "task_3_knowledge_synthesis",
            "title": "Knowledge Retrieval & Acceptance Gating",
            "goal": "Retrieve domain knowledge for AgentCraft architecture and verify acceptance gates",
            "expected_artifacts": 1,
            "min_completed_steps": 3,
        },
    ]

    def run_suite(self) -> Dict[str, Any]:
        start_time = time.perf_counter()
        results: List[Dict[str, Any]] = []

        total_tasks = len(self.BENCHMARK_TASKS)
        passed_tasks = 0
        total_steps = 0
        total_verifications = 0
        total_retries = 0

        registry = ToolRegistry(allow_network=False)
        agent = AgentCraftAgent(registry=registry, execution_mode="deterministic")

        for task in self.BENCHMARK_TASKS:
            task_start = time.perf_counter()
            state = agent.run(task["goal"])
            task_duration = (time.perf_counter() - task_start) * 1000.0

            passed = (
                state.status == "completed"
                and state.metrics["completed_steps"] >= task["min_completed_steps"]
                and len(state.artifacts) >= task["expected_artifacts"]
            )
            if passed:
                passed_tasks += 1

            total_steps += state.metrics["completed_steps"]
            total_verifications += state.metrics["verifications_passed"]
            total_retries += state.metrics["retries"]

            results.append({
                "task_id": task["id"],
                "title": task["title"],
                "passed": passed,
                "status": state.status,
                "completed_steps": state.metrics["completed_steps"],
                "verifications_passed": state.metrics["verifications_passed"],
                "retries": state.metrics["retries"],
                "duration_ms": round(task_duration, 2),
                "artifacts_count": len(state.artifacts),
            })

        suite_duration = (time.perf_counter() - start_time) * 1000.0
        completion_rate = (passed_tasks / total_tasks) * 100.0 if total_tasks else 0.0

        return {
            "suite_name": "AGENTCRAFT 2026 Core Capability Benchmark",
            "timestamp": time.time(),
            "total_tasks": total_tasks,
            "passed_tasks": passed_tasks,
            "completion_rate_pct": round(completion_rate, 2),
            "total_steps_executed": total_steps,
            "total_verifications_passed": total_verifications,
            "total_retries": total_retries,
            "suite_duration_ms": round(suite_duration, 2),
            "tasks": results,
            "system_verdict": "CERTIFIED" if completion_rate >= 90.0 else "NEEDS_OPTIMIZATION",
        }


benchmark_service = BenchmarkService()
