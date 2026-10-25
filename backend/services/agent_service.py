"""
AgentCraft Backend Agent Service
Manages session lifecycles, state persistence, agent instance execution,
and integration with the AI reasoning engine.
"""

from typing import Any, Dict, List, Optional
from ai.agent import AgentCraftAgent, AgentState, PlanStep
from ai.tools import ToolRegistry


class AgentService:
    """Singleton service orchestrating AgentCraft sessions and tool dispatch."""

    def __init__(self, sandbox_dir: Optional[str] = None):
        self.registry = ToolRegistry(sandbox_dir=sandbox_dir)
        self.agent = AgentCraftAgent(registry=self.registry)
        self.sessions: Dict[str, AgentState] = {}

    def create_session(self, goal: str, initial_memory: Optional[Dict[str, Any]] = None) -> AgentState:
        """Creates and registers a new agent session."""
        state = self.agent.create_session(goal=goal, initial_memory=initial_memory)
        self.sessions[state.session_id] = state
        return state

    def get_session(self, session_id: str) -> Optional[AgentState]:
        """Retrieves a session by ID."""
        return self.sessions.get(session_id)

    def list_sessions(self) -> List[Dict[str, Any]]:
        """Returns summarized metadata for all active sessions."""
        summaries = []
        for s in self.sessions.values():
            summaries.append({
                "session_id": s.session_id,
                "goal": s.goal,
                "status": s.status,
                "total_steps": len(s.plan),
                "completed_steps": s.metrics.get("completed_steps", 0),
                "artifacts_count": len(s.artifacts),
            })
        return summaries

    def delete_session(self, session_id: str) -> bool:
        """Removes a session from memory."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            return True
        return False

    def generate_plan(self, session_id: str) -> List[PlanStep]:
        """Generates a structured plan for the specified session."""
        state = self.get_session(session_id)
        if not state:
            raise KeyError(f"Session '{session_id}' not found.")
        return self.agent.plan(state)

    def execute_step(self, session_id: str, step_index: int) -> PlanStep:
        """Executes a single plan step in an active session."""
        state = self.get_session(session_id)
        if not state:
            raise KeyError(f"Session '{session_id}' not found.")
        return self.agent.execute_step(state, step_index)

    def run_autonomous(self, goal: str, initial_memory: Optional[Dict[str, Any]] = None) -> AgentState:
        """Executes an end-to-end autonomous session for the given goal."""
        state = self.agent.run(goal=goal, initial_memory=initial_memory)
        self.sessions[state.session_id] = state
        return state

    def get_registered_tools(self) -> List[Dict[str, Any]]:
        """Returns schemas for all registered tools."""
        return self.registry.list_tools()

    def run_direct_verification(self, assertions: List[Dict[str, Any]], subject: Any) -> Dict[str, Any]:
        """Runs standalone verification assertions."""
        res = self.registry.execute("verifier", assertions=assertions, subject=subject)
        return res.output or {"verified": False, "error": res.error}


# Global instance
agent_service = AgentService()
