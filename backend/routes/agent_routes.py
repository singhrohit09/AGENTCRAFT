"""
AgentCraft API Routes
Exposes REST endpoints for autonomous execution, session control,
tool discovery, step-by-step stepping, verification, and benchmark suites.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from backend.rakshagrid.security import autonomous_agent_limiter
from backend.services.agent_service import agent_service
from backend.services.benchmark_service import benchmark_service

router = APIRouter(prefix="/api/agent", tags=["AgentCraft Agent"])


class RunGoalRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="The user goal or task specification.")
    initial_memory: Optional[Dict[str, Any]] = Field(default=None, description="Optional working memory variables.")


class CreateSessionRequest(BaseModel):
    goal: str = Field(..., min_length=3, description="The user goal to plan.")
    initial_memory: Optional[Dict[str, Any]] = Field(default=None, description="Optional working memory.")


class ExecuteStepRequest(BaseModel):
    step_index: int = Field(..., ge=0, description="Zero-based index of the step to execute.")


class VerifyRequest(BaseModel):
    assertions: List[Dict[str, Any]] = Field(..., min_length=1, description="List of assertion rules.")
    subject: Any = Field(..., description="Subject data or dictionary to verify.")


@router.post("/run", status_code=status.HTTP_200_OK)
def run_autonomous_goal(req: RunGoalRequest, _limiter: None = Depends(autonomous_agent_limiter)):
    """Executes a goal end-to-end autonomously with full planning, tool calls, and verification."""
    try:
        state = agent_service.run_autonomous(goal=req.goal, initial_memory=req.initial_memory)
        return {
            "success": state.status == "completed",
            "session_id": state.session_id,
            "status": state.status,
            "metrics": state.metrics,
            "artifacts": state.artifacts,
            "plan": [p.model_dump() for p in state.plan],
            "execution_trace": [rec.model_dump() for rec in state.execution_trace],
            "logs": state.logs,
            "final_output": state.final_output,
            "error_summary": state.error_summary,
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Autonomous execution failed: {str(e)}")


@router.post("/sessions", status_code=status.HTTP_201_CREATED)
def create_session(req: CreateSessionRequest):
    """Initializes a new interactive agent session."""
    state = agent_service.create_session(goal=req.goal, initial_memory=req.initial_memory)
    return {
        "session_id": state.session_id,
        "goal": state.goal,
        "status": state.status,
        "created_at": state.logs[0] if state.logs else "",
    }


@router.get("/sessions", status_code=status.HTTP_200_OK)
def list_sessions():
    """Lists all active and historical agent sessions."""
    return {"sessions": agent_service.list_sessions()}


@router.get("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def get_session(session_id: str):
    """Retrieves full state, logs, artifacts, and plan for a specific session."""
    state = agent_service.get_session(session_id)
    if not state:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return {
        "session_id": state.session_id,
        "goal": state.goal,
        "status": state.status,
        "plan": [p.model_dump() for p in state.plan],
        "current_step_index": state.current_step_index,
        "memory": state.memory,
        "artifacts": state.artifacts,
        "execution_trace": [rec.model_dump() for rec in state.execution_trace],
        "logs": state.logs,
        "metrics": state.metrics,
        "final_output": state.final_output,
        "error_summary": state.error_summary,
    }


@router.delete("/sessions/{session_id}", status_code=status.HTTP_200_OK)
def delete_session(session_id: str):
    """Deletes an active session."""
    deleted = agent_service.delete_session(session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"Session '{session_id}' not found.")
    return {"message": f"Session '{session_id}' deleted successfully."}


@router.post("/sessions/{session_id}/plan", status_code=status.HTTP_200_OK)
def generate_session_plan(session_id: str):
    """Generates the multi-step execution plan for an existing session."""
    try:
        plan = agent_service.generate_plan(session_id)
        return {
            "session_id": session_id,
            "total_steps": len(plan),
            "plan": [p.model_dump() for p in plan],
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.post("/sessions/{session_id}/step", status_code=status.HTTP_200_OK)
def execute_session_step(session_id: str, req: ExecuteStepRequest):
    """Executes a single step in a step-by-step interactive workflow."""
    try:
        step = agent_service.execute_step(session_id, req.step_index)
        state = agent_service.get_session(session_id)
        return {
            "session_id": session_id,
            "step": step.model_dump(),
            "session_status": state.status if state else "unknown",
            "metrics": state.metrics if state else {},
        }
    except KeyError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except IndexError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Step execution error: {str(e)}")


@router.get("/tools", status_code=status.HTTP_200_OK)
def get_tools():
    """Returns schemas and documentation for all tools available to AgentCraft."""
    tools = agent_service.get_registered_tools()
    return {"total_tools": len(tools), "tools": tools}


@router.post("/verify", status_code=status.HTTP_200_OK)
def run_standalone_verification(req: VerifyRequest):
    """Evaluates assertion rules directly on subject data."""
    report = agent_service.run_direct_verification(assertions=req.assertions, subject=req.subject)
    return report


@router.post("/benchmark", status_code=status.HTTP_200_OK)
@router.get("/benchmark", status_code=status.HTTP_200_OK)
def run_benchmark():
    """Runs the AGENTCRAFT 2026 Core Capability Benchmark suite."""
    report = benchmark_service.run_suite()
    return report
