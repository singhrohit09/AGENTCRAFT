"""
RakshaGrid API Routes
Exposes REST endpoints for disaster intelligence monitoring, system health,
PostgreSQL database status verification, emergency alerts, and team logistics.
"""

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.rakshagrid.config import rakshagrid_settings
from backend.rakshagrid.schemas import (
    RakshaGridHealthResponse,
    DatabaseStatusResponse,
    OverviewResponse,
    IncidentSummary,
    AlertSummary,
    ResponseTeamSummary,
    ShelterSummary,
    RakshaGridErrorResponse,
)
from backend.rakshagrid.service import rakshagrid_service

router = APIRouter(
    prefix="/api/rakshagrid",
    tags=["RakshaGrid — Disaster Intelligence & Response"],
    responses={
        status.HTTP_500_INTERNAL_SERVER_ERROR: {
            "model": RakshaGridErrorResponse,
            "description": "Internal operational failure in disaster module",
        }
    },
)


@router.get(
    "/health",
    response_model=RakshaGridHealthResponse,
    status_code=status.HTTP_200_OK,
    summary="RakshaGrid Subsystem Health",
    description="Reports diagnostic telemetry across database, alerting engine, geospatial indexer, and operational parameters.",
)
def get_health():
    """Retrieve health and readiness telemetry for the RakshaGrid disaster platform."""
    try:
        return rakshagrid_service.get_health_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Health diagnostic check failed: {str(e)}",
        )


@router.get(
    "/database/status",
    response_model=DatabaseStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="PostgreSQL Database Verification",
    description="Inspects PostgreSQL connectivity, migration version status, and declared ORM models.",
)
def get_database_status():
    """Inspects PostgreSQL database connection and Alembic migration status."""
    try:
        return rakshagrid_service.get_database_status()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database status inspection failed: {str(e)}",
        )


@router.get(
    "/overview",
    response_model=OverviewResponse,
    status_code=status.HTTP_200_OK,
    summary="Tactical Mission Control Overview",
    description="Aggregates active disaster incidents, DEFCON threat level, emergency alerts, and shelter occupancy.",
)
def get_tactical_overview(db: Session = Depends(get_db)):
    """Retrieves aggregated statistics and high-priority alerts for the overview dashboard."""
    try:
        return rakshagrid_service.get_overview_data(db=db)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate tactical overview: {str(e)}",
        )


@router.get(
    "/incidents",
    response_model=List[IncidentSummary],
    status_code=status.HTTP_200_OK,
    summary="Query Disaster Incidents",
    description="Lists tracked disaster incidents with optional filters by hazard type, severity level, or status.",
)
def list_incidents(
    disaster_type: Optional[str] = Query(None, description="Filter by hazard: flood, cyclone, earthquake, wildfire, landslide"),
    severity: Optional[str] = Query(None, description="Filter by severity: critical, severe, moderate, minor"),
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: active, contained, assessing, closed"),
):
    """Lists disaster incidents with structured criteria filtering."""
    try:
        return rakshagrid_service.list_incidents(
            disaster_type=disaster_type,
            severity=severity,
            status=status_filter,
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list incidents: {str(e)}",
        )


@router.get(
    "/alerts",
    response_model=List[AlertSummary],
    status_code=status.HTTP_200_OK,
    summary="Query Emergency Alerts",
    description="Retrieves active or archived public emergency broadcasts.",
)
def list_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity: extreme, severe, moderate, minor"),
    active_only: bool = Query(True, description="When true, only active broadcasts are returned"),
):
    """Retrieves emergency warning and evacuation alerts."""
    try:
        return rakshagrid_service.list_alerts(severity=severity, active_only=active_only)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list alerts: {str(e)}",
        )


@router.get(
    "/teams",
    response_model=List[ResponseTeamSummary],
    status_code=status.HTTP_200_OK,
    summary="Query Emergency Response Teams",
    description="Retrieves operational status of NDRF, SDRF, Medical, and Aerial Drone rescue teams.",
)
def list_teams(
    status_filter: Optional[str] = Query(None, alias="status", description="Filter by status: deployed, standby, en_route"),
):
    """Lists rescue and emergency response units."""
    try:
        return rakshagrid_service.list_teams(status=status_filter)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list response teams: {str(e)}",
        )


@router.get(
    "/shelters",
    response_model=List[ShelterSummary],
    status_code=status.HTTP_200_OK,
    summary="Query Evacuation Shelters",
    description="Lists relief camps and evacuation shelters with real-time capacity and occupancy.",
)
def list_shelters():
    """Lists relief shelters and capacity utilization."""
    try:
        return rakshagrid_service.list_shelters()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to list shelters: {str(e)}",
        )


@router.get(
    "/config",
    status_code=status.HTTP_200_OK,
    summary="Public Operational Configuration",
    description="Returns sanitized public configuration parameters and Phase 1 operational flags.",
)
def get_public_config():
    """Returns safe operational settings (no credentials or secrets)."""
    return {
        "app_name": rakshagrid_settings.RAKSHAGRID_APP_NAME,
        "subtitle": rakshagrid_settings.RAKSHAGRID_SUBTITLE,
        "version": rakshagrid_settings.RAKSHAGRID_VERSION,
        "environment": rakshagrid_settings.RAKSHAGRID_ENV,
        "demo_mode": rakshagrid_settings.RAKSHAGRID_DEMO_MODE,
        "defcon_level": rakshagrid_settings.RAKSHAGRID_DEFCON_LEVEL,
        "alert_threshold": rakshagrid_settings.RAKSHAGRID_ALERT_THRESHOLD,
        "database_configured": rakshagrid_settings.is_database_configured,
        "database_host": rakshagrid_settings.POSTGRES_HOST,
        "database_port": rakshagrid_settings.POSTGRES_PORT,
        "database_name": rakshagrid_settings.POSTGRES_DB,
    }
