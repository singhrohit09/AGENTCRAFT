"""
AgentCraft Intelligence REST API Routes (/api/v1/intelligence)
Exposes endpoints for deterministic risk analysis, external meteorological telemetry,
AI disaster agent situational synthesis, scenario simulations, and human approval decision gates.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.rakshagrid.auth import (
    UserIdentity,
    UserRole,
    get_current_user,
    require_role,
)
from backend.rakshagrid.models import Incident, RiskAssessment
from backend.services.external_data_service import disaster_data_service
from backend.services.risk_engine import disaster_risk_engine
from backend.services.disaster_agent_service import disaster_agent_service
from backend.services.simulation_service import simulation_engine

router = APIRouter(
    prefix="/api/v1/intelligence",
    tags=["AgentCraft — Intelligence & Risk API (v1)"],
)


# ==============================================================================
# Pydantic Schemas for Intelligence Endpoints
# ==============================================================================

class RiskAssessmentResponse(BaseModel):
    incident_id: Optional[str]
    incident_code: Optional[str]
    title: Optional[str]
    target_area: str
    hazard_type: str
    reported_severity: str
    operational_status: str
    calculated_risk_score: float
    risk_level: str
    scoring_breakdown: List[Dict[str, Any]]
    data_sources: List[Dict[str, Any]]
    data_gaps: List[str]
    uncertainty_points: float
    confidence_score: float
    recommended_interventions: List[str]
    scientific_limitation_disclaimer: str
    assessed_at: str
    assessment_id: Optional[str] = None


class WeatherQueryResponse(BaseModel):
    latitude: float
    longitude: float
    weather: Dict[str, Any]
    flood: Dict[str, Any]
    overall_freshness_seconds: Optional[float]
    is_stale: bool


class AnalyzeSituationRequest(BaseModel):
    incident_id: Optional[str] = Field(default=None, description="Optional incident UUID or code to focus analysis on.")


class ApprovePlanRequest(BaseModel):
    analysis_id: str = Field(..., description="UUID of the AI analysis record.")
    approve: bool = Field(default=True, description="True to approve proposal, False to reject.")
    notes: Optional[str] = Field(default="", description="Operator approval justification or conditions.")


class RunSimulationRequest(BaseModel):
    scenario_type: str = Field(
        ...,
        description="heavy_rainfall | multi_incident | team_unavailability | shelter_surge | supply_shortage | cascade_compound",
    )
    scenario_name: Optional[str] = Field(default="", description="Descriptive label for simulation run.")
    parameters: Dict[str, Any] = Field(default_factory=dict, description="Scenario-specific stress parameters.")


# ==============================================================================
# 1. Explainable Disaster Risk Assessment Endpoints
# ==============================================================================

@router.post(
    "/risk/assess/{incident_id}",
    response_model=RiskAssessmentResponse,
    status_code=status.HTTP_200_OK,
    summary="Assess Incident Risk",
    description="Calculates normalized risk score (0-100), contributing factors, uncertainty penalties, and persists assessment.",
)
def assess_incident_risk(
    incident_id: str,
    persist: bool = Query(True, description="Whether to persist assessment to database history"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    from ai.tools.disaster_tools import find_incident
    inc = find_incident(db, incident_id)
    if not inc:
        raise HTTPException(status_code=404, detail=f"Incident '{incident_id}' not found.")

    res = disaster_risk_engine.assess_incident(inc, db=db, persist=persist)
    return RiskAssessmentResponse(**res)


@router.get(
    "/risk/assessments",
    status_code=status.HTTP_200_OK,
    summary="List Historical Risk Assessments",
    description="Returns chronological audit history of previous incident risk evaluations.",
)
def list_risk_assessments(
    incident_id: Optional[str] = Query(None, description="Filter by incident UUID"),
    limit: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    query = db.query(RiskAssessment)
    if incident_id:
        try:
            from uuid import UUID
            iid = UUID(str(incident_id))
            query = query.filter(RiskAssessment.incident_id == iid)
        except ValueError:
            pass

    records = query.order_by(RiskAssessment.assessed_at.desc()).limit(limit).all()
    results = []
    for r in records:
        import json
        results.append({
            "id": str(r.id),
            "incident_id": str(r.incident_id) if r.incident_id else None,
            "target_area": r.target_area,
            "hazard_type": r.hazard_type,
            "calculated_risk_score": r.calculated_risk_score,
            "risk_level": r.risk_level,
            "confidence_score": r.confidence_score,
            "factors": json.loads(r.simulated_factors) if r.simulated_factors else [],
            "interventions": json.loads(r.recommended_interventions) if r.recommended_interventions else [],
            "assessed_at": r.assessed_at.isoformat() if r.assessed_at else None,
        })
    return {"count": len(results), "assessments": results}


# ==============================================================================
# 2. External Disaster Data Integration Endpoints
# ==============================================================================

@router.get(
    "/external-data/weather",
    response_model=WeatherQueryResponse,
    status_code=status.HTTP_200_OK,
    summary="Fetch Meteorological Observations",
    description="Retrieves live, cached, or fallback weather and river flood telemetry for coordinates with freshness metrics.",
)
def get_external_weather(
    latitude: float = Query(..., ge=-90.0, le=90.0),
    longitude: float = Query(..., ge=-180.0, le=180.0),
    force_refresh: bool = Query(False, description="Bypass cache and force fresh provider query"),
    _user: UserIdentity = Depends(get_current_user),
):
    w = disaster_data_service.get_weather(latitude, longitude, force_refresh=force_refresh)
    f = disaster_data_service.get_flood_data(latitude, longitude, force_refresh=force_refresh)
    return WeatherQueryResponse(
        latitude=latitude,
        longitude=longitude,
        weather=w,
        flood=f,
        overall_freshness_seconds=w.get("freshness_seconds"),
        is_stale=w.get("is_stale", False) or f.get("is_stale", False),
    )


@router.get(
    "/external-data/health",
    status_code=status.HTTP_200_OK,
    summary="External Data Integrations Health",
    description="Reports connectivity and cache telemetry for external disaster data providers.",
)
def get_external_data_health(_user: UserIdentity = Depends(get_current_user)):
    return disaster_data_service.get_provider_health()


# ==============================================================================
# 3. AI Disaster Intelligence Agent Endpoints
# ==============================================================================

@router.post(
    "/agent/analyze",
    status_code=status.HTTP_200_OK,
    summary="AI Agent Situational Analysis",
    description="Executes full evidence retrieval across incidents, teams, shelters, and supplies to synthesize priority triage and tactical response recommendations.",
)
def run_agent_analysis(
    req: AnalyzeSituationRequest,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    try:
        result = disaster_agent_service.analyze_situation(db, target_incident_id=req.incident_id)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"AI agent situational analysis failed: {str(e)}")


@router.post(
    "/agent/plan/approve",
    status_code=status.HTTP_200_OK,
    summary="Approve or Reject AI Response Plan",
    description="Operational Decision Gate: Requires explicit human authorization before response plan recommendations are accepted.",
)
def approve_agent_plan(
    req: ApprovePlanRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    try:
        operator_label = f"{current_user.user_id} ({current_user.role})"
        res = disaster_agent_service.approve_recommendation(
            db=db,
            analysis_id=req.analysis_id,
            approved_by=operator_label,
            approve=req.approve,
            notes=req.notes or "",
        )
        return res
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to record approval decision: {str(e)}")


# ==============================================================================
# 4. Disaster Scenario Simulation Endpoints
# ==============================================================================

@router.post(
    "/simulations/run",
    status_code=status.HTTP_200_OK,
    summary="Run Hypothetical Disaster Simulation",
    description="Executes scenario stress-test (heavy rainfall, multi-incident, team outage, shelter surge) with guaranteed state isolation.",
)
def run_disaster_simulation(
    req: RunSimulationRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(get_current_user),
):
    try:
        operator_label = f"{current_user.user_id} ({current_user.role})"
        result = simulation_engine.run_simulation(
            db=db,
            scenario_type=req.scenario_type,
            scenario_name=req.scenario_name or "",
            parameters=req.parameters,
            operator_name=operator_label,
        )
        return result
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Simulation run failed: {str(e)}")


@router.get(
    "/simulations/history",
    status_code=status.HTTP_200_OK,
    summary="List Simulation History",
    description="Retrieves audit log of previous hypothetical simulation runs.",
)
def list_simulations_history(
    limit: int = Query(20, ge=1, le=50),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    return {"simulations": simulation_engine.list_simulations(db, limit=limit)}
