"""
AgentCraft Intelligent Alerts REST API Routes (/api/v1/alerts)
Exposes endpoints for querying emergency alerts, executing rule sweeps,
acknowledging warnings, and recording operational resolutions.
"""

from datetime import datetime
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
from backend.rakshagrid.security import alert_evaluation_limiter
from backend.services.alert_service import alert_service

router = APIRouter(
    prefix="/api/v1/alerts",
    tags=["AgentCraft — Intelligent Alerts API (v1)"],
)


# ==============================================================================
# Pydantic Schemas for Alerts Endpoints
# ==============================================================================

class AlertDetailResponse(BaseModel):
    id: str
    incident_id: Optional[str] = None
    alert_code: str
    headline: str
    urgency: str
    severity: str
    certainty: str
    target_region: str
    evacuation_recommended: bool
    instructions: str
    broadcast_status: str
    trigger_reason: Optional[str] = None
    source_type: Optional[str] = None
    dedup_key: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    resolved_by: Optional[str] = None
    issued_at: datetime
    created_at: datetime


class AcknowledgeAlertRequest(BaseModel):
    operator_name: Optional[str] = Field(default=None, description="Optional custom operator callsign/identifier.")


class ResolveAlertRequest(BaseModel):
    resolution_notes: str = Field(..., min_length=3, description="Operational justification and actions taken.")
    operator_name: Optional[str] = Field(default=None, description="Optional operator callsign.")


# ==============================================================================
# Route Endpoints
# ==============================================================================

@router.get(
    "",
    response_model=List[AlertDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List Emergency Alerts",
    description="Returns list of alerts with optional filtering by status (active, acknowledged, resolved), severity, and incident.",
)
def list_alerts(
    status_filter: Optional[str] = Query(None, alias="status", description="active, acknowledged, resolved, all"),
    severity: Optional[str] = Query(None, description="critical, high, medium, low"),
    incident_id: Optional[str] = Query(None, description="Filter by incident UUID"),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    alerts = alert_service.list_alerts(
        db=db,
        status_filter=status_filter,
        severity=severity,
        incident_id=incident_id,
        limit=limit,
    )
    return [
        AlertDetailResponse(
            id=str(a.id),
            incident_id=str(a.incident_id) if a.incident_id else None,
            alert_code=a.alert_code,
            headline=a.headline,
            urgency=a.urgency,
            severity=a.severity,
            certainty=a.certainty,
            target_region=a.target_region,
            evacuation_recommended=a.evacuation_recommended,
            instructions=a.instructions,
            broadcast_status=a.broadcast_status,
            trigger_reason=a.trigger_reason,
            source_type=a.source_type,
            dedup_key=a.dedup_key,
            acknowledged_at=a.acknowledged_at,
            acknowledged_by=a.acknowledged_by,
            resolved_at=a.resolved_at,
            resolved_by=a.resolved_by,
            issued_at=a.issued_at,
            created_at=a.created_at,
        )
        for a in alerts
    ]


@router.post(
    "/evaluate",
    status_code=status.HTTP_200_OK,
    summary="Evaluate Alert Threshold Rules",
    description="Sweeps active incidents, shelters, and resources against configured alert thresholds, suppressing duplicates within cooldown.",
)
def evaluate_alert_rules(
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
    _limiter: None = Depends(alert_evaluation_limiter),
):
    try:
        results = alert_service.evaluate_system_alerts(db)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Alert threshold evaluation failed: {str(e)}")


@router.post(
    "/{alert_id}/acknowledge",
    response_model=AlertDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Acknowledge Alert",
    description="Marks an active alert as acknowledged by on-duty watch commander.",
)
def acknowledge_alert(
    alert_id: str,
    req: Optional[AcknowledgeAlertRequest] = None,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    try:
        actor = (req.operator_name if req and req.operator_name else None) or f"{current_user.user_id} ({current_user.role})"
        alert = alert_service.acknowledge_alert(db, alert_id=alert_id, operator_name=actor)
        return AlertDetailResponse(
            id=str(alert.id),
            incident_id=str(alert.incident_id) if alert.incident_id else None,
            alert_code=alert.alert_code,
            headline=alert.headline,
            urgency=alert.urgency,
            severity=alert.severity,
            certainty=alert.certainty,
            target_region=alert.target_region,
            evacuation_recommended=alert.evacuation_recommended,
            instructions=alert.instructions,
            broadcast_status=alert.broadcast_status,
            trigger_reason=alert.trigger_reason,
            source_type=alert.source_type,
            dedup_key=alert.dedup_key,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            issued_at=alert.issued_at,
            created_at=alert.created_at,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to acknowledge alert: {str(e)}")


@router.post(
    "/{alert_id}/resolve",
    response_model=AlertDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Resolve Alert",
    description="Marks an alert as resolved with operational notes.",
)
def resolve_alert(
    alert_id: str,
    req: ResolveAlertRequest,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    try:
        actor = req.operator_name or f"{current_user.user_id} ({current_user.role})"
        alert = alert_service.resolve_alert(
            db,
            alert_id=alert_id,
            operator_name=actor,
            resolution_notes=req.resolution_notes,
        )
        return AlertDetailResponse(
            id=str(alert.id),
            incident_id=str(alert.incident_id) if alert.incident_id else None,
            alert_code=alert.alert_code,
            headline=alert.headline,
            urgency=alert.urgency,
            severity=alert.severity,
            certainty=alert.certainty,
            target_region=alert.target_region,
            evacuation_recommended=alert.evacuation_recommended,
            instructions=alert.instructions,
            broadcast_status=alert.broadcast_status,
            trigger_reason=alert.trigger_reason,
            source_type=alert.source_type,
            dedup_key=alert.dedup_key,
            acknowledged_at=alert.acknowledged_at,
            acknowledged_by=alert.acknowledged_by,
            resolved_at=alert.resolved_at,
            resolved_by=alert.resolved_by,
            issued_at=alert.issued_at,
            created_at=alert.created_at,
        )
    except ValueError as ve:
        raise HTTPException(status_code=404, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to resolve alert: {str(e)}")
