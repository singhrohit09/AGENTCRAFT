"""
Tests for AgentCraft Core Agent
Validates planning, state tracking, execution loop, verification gates, and error recovery.
"""

import pytest
import tempfile
import shutil
from ai.agent import AgentCraftAgent, AgentState, PlanStep
from ai.tools import ToolRegistry


class TestAgentCraftAgent:
    def setup_method(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.registry = ToolRegistry(sandbox_dir=self.tmp_dir, allow_network=False)
        self.agent = AgentCraftAgent(
            registry=self.registry,
            max_retries_per_step=2,
            execution_mode="deterministic",
        )

    def teardown_method(self):
        shutil.rmtree(self.tmp_dir, ignore_errors=True)

    def test_session_initialization(self):
        state = self.agent.create_session("Build benchmark dataset", initial_memory={"author": "AgentCraft"})
        assert state.goal == "Build benchmark dataset"
        assert state.status == "idle"
        assert state.memory["author"] == "AgentCraft"
        assert len(state.logs) >= 1

    def test_plan_synthesis_data_workflow(self):
        state = self.agent.create_session("Analyze dataset of agents and detect outliers")
        plan = self.agent.plan(state)
        assert len(plan) >= 4
        tools_in_plan = [s.tool_name for s in plan]
        assert "file_manager" in tools_in_plan
        assert "data_analyzer" in tools_in_plan
        assert state.metrics["total_steps"] == len(plan)

    def test_end_to_end_agent_execution_algorithmic(self):
        goal = "Compute mathematical fibonacci sequence and verify output"
        state = self.agent.run(goal)

        assert state.status == "completed"
        assert state.metrics["completed_steps"] == len(state.plan)
        assert state.metrics["tool_calls"] >= 3
        assert state.metrics["verifications_passed"] >= 1
        assert len(state.execution_trace) == len(state.plan)
        assert state.final_output is not None
        assert state.final_output["session_id"] == state.session_id

    def test_end_to_end_data_analysis_workflow(self):
        goal = "Profile agent dataset and generate evaluation report"
        state = self.agent.run(goal)

        assert state.status == "completed"
        assert len(state.artifacts) >= 1
        assert any(a["type"] == "file" for a in state.artifacts)
        assert "last_output" in state.memory

    def test_invalid_step_execution_raises_index_error(self):
        state = self.agent.create_session("Test invalid index")
        self.agent.plan(state)
        with pytest.raises(IndexError):
            self.agent.execute_step(state, step_index=99)

    def test_self_healing_recovery_on_path_error(self):
        state = self.agent.create_session("Self healing test")
        step = PlanStep(
            step_id=1,
            title="Write with path escape",
            description="Intentionally invalid path that requires normalization",
            tool_name="file_manager",
            tool_args={"action": "write", "path": "../../illegal_escape.txt", "content": "recovered"},
            expected_outcome="Normalized and written",
        )
        state.plan = [step]
        executed = self.agent.execute_step(state, 0)
        # Verify that error was detected, recovery was attempted, and retry count incremented
        assert executed.retries >= 1
        assert state.metrics["retries"] >= 1
