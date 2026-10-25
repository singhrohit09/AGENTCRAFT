"""
RakshaGrid Incident API Routes (/api/v1/incidents)
Exposes REST endpoints for persistent incident management,
status lifecycle transitions, timeline history, and administrative archival.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.rakshagrid.auth import (
    UserIdentity,
    UserRole,
    get_current_user,
    require_authenticated_user,
    require_role,
)
from backend.rakshagrid.incident_schemas import (
    IncidentCreate,
    IncidentUpdatePatch,
    IncidentResponse,
    IncidentPaginatedResponse,
    IncidentUpdateCreate,
    IncidentUpdateResponse,
)
from backend.rakshagrid.incident_service import incident_service

router = APIRouter(
    prefix="/api/v1/incidents",
    tags=["RakshaGrid — Incidents API (v1)"],
)


@router.get(
    "",
    response_model=IncidentPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Incidents",
    description="Returns a paginated list of disaster incidents with optional filters by category, severity, status, search, and sorting.",
)
def list_incidents(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page (max 100)"),
    category: Optional[str] = Query(None, description="Hazard category: flood, severe_weather, wildfire, earthquake, landslide, industrial_accident, other"),
    severity: Optional[str] = Query(None, description="Severity level: low, medium, high, critical"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status: reported, under_assessment, confirmed, response_active, contained, resolved, closed"),
    verification_status: Optional[str] = Query(None, description="unverified, under_review, verified"),
    search: Optional[str] = Query(None, description="Search keyword in title, description, code, or location"),
    sort_by: str = Query("created_at", description="Sort column: created_at or reported_at"),
    sort_order: str = Query("desc", description="Sort order: desc or asc"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    """List disaster incidents with search, filters, pagination, and sorting."""
    items, total, total_pages = incident_service.list_incidents(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        severity=severity,
        status_filter=status_filter,
        verification_status=verification_status,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )

    serialized = []
    for inc in items:
        resp = IncidentResponse.model_validate(inc)
        resp.updates_count = len(inc.updates) if inc.updates else 0
        serialized.append(resp)

    return IncidentPaginatedResponse(
        items=serialized,
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.post(
    "",
    response_model=IncidentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Incident",
    description="Creates a new disaster incident and atomically records its creation history in the audit timeline.",
)
def create_incident(
    payload: IncidentCreate,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    """Log and persist a new disaster incident."""
    incident = incident_service.create_incident(db, payload, current_user)
    resp = IncidentResponse.model_validate(incident)
    resp.updates_count = len(incident.updates) if incident.updates else 1
    return resp


@router.get(
    "/{incident_id}",
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Incident Details",
    description="Retrieves a single incident by its UUID identifier.",
)
def get_incident(
    incident_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    """Retrieve full details for an incident."""
    incident = incident_service.get_incident(db, incident_id)
    resp = IncidentResponse.model_validate(incident)
    resp.updates_count = len(incident.updates) if incident.updates else 0
    return resp


@router.patch(
    "/{incident_id}",
    response_model=IncidentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Incident",
    description="Modifies permitted incident fields, validates status transitions, and writes an immutable audit record.",
)
def update_incident(
    incident_id: str,
    payload: IncidentUpdatePatch,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    """Update fields or transition status of an incident."""
    incident = incident_service.update_incident(db, incident_id, payload, current_user)
    resp = IncidentResponse.model_validate(incident)
    resp.updates_count = len(incident.updates) if incident.updates else 0
    return resp


@router.get(
    "/{incident_id}/updates",
    status_code=status.HTTP_200_OK,
    summary="Get Incident Timeline",
    description="Returns chronological timeline updates and situation reports for an incident.",
)
def get_incident_updates(
    incident_id: str,
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    """Retrieve historical timeline updates."""
    updates, total = incident_service.list_incident_updates(db, incident_id, page, page_size)
    serialized = []
    for u in updates:
        serialized.append({
            "id": str(u.id),
            "incident_id": str(u.incident_id),
            "actor_id": u.actor_id,
            "previous_status": u.previous_status,
            "new_status": u.new_status,
            "update_type": u.update_type,
            "message": u.message,
            "metadata_payload": u.parsed_metadata,
            "created_at": u.created_at,
        })
    return {
        "items": serialized,
        "total": total,
        "page": page,
        "page_size": page_size,
    }


@router.post(
    "/{incident_id}/updates",
    response_model=IncidentUpdateResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Incident Situation Update",
    description="Appends a new verified update, field report, or status note to the incident timeline.",
)
def add_incident_update(
    incident_id: str,
    payload: IncidentUpdateCreate,
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    """Append a situation report or timeline log entry."""
    update = incident_service.add_incident_update(db, incident_id, payload, current_user)
    return IncidentUpdateResponse(
        id=str(update.id),
        incident_id=str(update.incident_id),
        actor_id=update.actor_id,
        previous_status=update.previous_status,
        new_status=update.new_status,
        update_type=update.update_type,
        message=update.message,
        metadata_payload=update.parsed_metadata,
        created_at=update.created_at,
    )


@router.post(
    "/seed",
    status_code=status.HTTP_200_OK,
    summary="Seed Deterministic Incidents",
    description="Development and testing only. Inserts idempotent simulated disaster incidents and timeline histories.",
)
def seed_dev_incidents_api(
    reset: bool = Query(False, description="Clear existing simulation records before seeding"),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    """Seed fictional simulation incidents for development."""
    from backend.rakshagrid.config import rakshagrid_settings
    from backend.scripts.seed_dev_data import seed_dev_incidents

    if rakshagrid_settings.is_production:
        from fastapi import HTTPException
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Seeding prohibited in production mode.")
    return seed_dev_incidents(db, reset=reset)


@router.delete(
    "/{incident_id}",
    status_code=status.HTTP_200_OK,
    summary="Archive or Delete Incident",
    description="Restricted to administrators. Archives and closes the incident by default, preserving historical integrity.",
)
def delete_incident(
    incident_id: str,
    permanent: bool = Query(False, description="When true, permanently deletes record from database"),
    db: Session = Depends(get_db),
    current_user: UserIdentity = Depends(require_role(UserRole.ADMIN_ROLES)),
):
    """Archive or permanently delete an incident (Admin privilege required)."""
    return incident_service.archive_or_delete_incident(db, incident_id, current_user, permanent=permanent)
