"""
RakshaGrid Coordination REST API Routes
Exposes persistent endpoints for Response Teams, Operational Tasks,
Emergency Evacuation Shelters, and Relief Resource Stockpiles.
"""

from typing import Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from backend.database.session import get_db
from backend.rakshagrid.auth import (
    UserIdentity,
    UserRole,
    get_current_user,
    require_role,
)
from backend.rakshagrid.coordination_schemas import (
    TeamCreate,
    TeamUpdatePatch,
    TeamResponse,
    TeamPaginatedResponse,
    TaskCreate,
    TaskUpdatePatch,
    TaskResponse,
    TaskPaginatedResponse,
    ShelterCreate,
    ShelterUpdatePatch,
    ShelterAdmissionRequest,
    ShelterDischargeRequest,
    ShelterResponse,
    ShelterPaginatedResponse,
    ResourceCreate,
    ResourceUpdatePatch,
    ResourceAllocateRequest,
    ResourceReturnRequest,
    ResourceResponse,
    ResourcePaginatedResponse,
)
from backend.rakshagrid.coordination_service import coordination_service

router = APIRouter(
    prefix="/api/v1",
    tags=["RakshaGrid — Maps & Coordination (v1)"],
)


# ==============================================================================
# Response Teams Endpoints (/api/v1/teams)
# ==============================================================================

@router.get(
    "/teams",
    response_model=TeamPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Response Teams",
    description="Returns a paginated roster of response teams with optional filtering by status, unit type, and keyword search.",
)
def list_teams(
    page: int = Query(1, ge=1, description="Page number (1-indexed)"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status: available, assigned, busy, offline"),
    unit_type: Optional[str] = Query(None, description="Specialization: NDRF, SDRF, Medical, HAZMAT, Drone Recon"),
    search: Optional[str] = Query(None, description="Search in callsign, commander name, base location"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    items, total, total_pages = coordination_service.list_teams(
        db=db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        unit_type=unit_type,
        search=search,
    )
    return TeamPaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post(
    "/teams",
    response_model=TeamResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create Response Team",
    description="Registers a new emergency response unit in the operational roster.",
)
def create_team(
    payload: TeamCreate,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.create_team(db, payload)


@router.get(
    "/teams/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Response Team Details",
)
def get_team(
    team_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    return coordination_service.get_team(db, team_id)


@router.patch(
    "/teams/{team_id}",
    response_model=TeamResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Response Team",
)
def update_team(
    team_id: str,
    payload: TeamUpdatePatch,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.update_team(db, team_id, payload)


@router.delete(
    "/teams/{team_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Response Team",
)
def delete_team(
    team_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.ADMIN_ROLES)),
):
    return coordination_service.delete_team(db, team_id)


# ==============================================================================
# Response Tasks Endpoints (/api/v1/tasks)
# ==============================================================================

@router.get(
    "/tasks",
    response_model=TaskPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Response Tasks",
    description="Returns actionable tasks dispatched to response teams, filterable by incident, team, priority, and status.",
)
def list_tasks(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    incident_id: Optional[str] = Query(None, description="Filter by linked incident UUID"),
    assigned_team_id: Optional[str] = Query(None, description="Filter by assigned team UUID"),
    status_filter: Optional[str] = Query(None, alias="status", description="Status: pending, in_progress, completed, cancelled"),
    priority: Optional[str] = Query(None, description="Priority: low, medium, high, critical"),
    search: Optional[str] = Query(None, description="Search in title or description"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    items, total, total_pages = coordination_service.list_tasks(
        db=db,
        page=page,
        page_size=page_size,
        incident_id=incident_id,
        assigned_team_id=assigned_team_id,
        status_filter=status_filter,
        priority=priority,
        search=search,
    )
    return TaskPaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post(
    "/tasks",
    response_model=TaskResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create and Dispatch Task",
    description="Creates a task associated with an existing incident and optionally assigns an available response team.",
)
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.create_task(db, payload)


@router.get(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Task Details",
)
def get_task(
    task_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    return coordination_service.get_task(db, task_id)


@router.patch(
    "/tasks/{task_id}",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Task or Reassign Team",
)
def update_task(
    task_id: str,
    payload: TaskUpdatePatch,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.update_task(db, task_id, payload)


@router.post(
    "/tasks/{task_id}/complete",
    response_model=TaskResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark Task Completed",
    description="Marks task completed, records completion timestamp, and releases assigned response team to available.",
)
def complete_task(
    task_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.complete_task(db, task_id)


# ==============================================================================
# Shelters Endpoints (/api/v1/shelters)
# ==============================================================================

@router.get(
    "/shelters",
    response_model=ShelterPaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Evacuation Shelters",
    description="Returns evacuation shelters and relief camps with capacity telemetry, coordinates, and availability.",
)
def list_shelters(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, alias="status", description="Status: open, full, closed"),
    shelter_type: Optional[str] = Query(None, description="Type: Cyclone Shelter, School Hall, Stadium, Tent Camp"),
    available_only: bool = Query(False, description="Filter for open shelters with remaining capacity"),
    search: Optional[str] = Query(None, description="Search in name, address, or contact person"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    items, total, total_pages = coordination_service.list_shelters(
        db=db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
        shelter_type=shelter_type,
        available_only=available_only,
        search=search,
    )
    return ShelterPaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post(
    "/shelters",
    response_model=ShelterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Evacuation Shelter",
)
def create_shelter(
    payload: ShelterCreate,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.create_shelter(db, payload)


@router.get(
    "/shelters/{shelter_id}",
    response_model=ShelterResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Shelter Details",
)
def get_shelter(
    shelter_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    return coordination_service.get_shelter(db, shelter_id)


@router.patch(
    "/shelters/{shelter_id}",
    response_model=ShelterResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Shelter Details",
)
def update_shelter(
    shelter_id: str,
    payload: ShelterUpdatePatch,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.update_shelter(db, shelter_id, payload)


@router.post(
    "/shelters/{shelter_id}/admit",
    response_model=ShelterResponse,
    status_code=status.HTTP_200_OK,
    summary="Admit Occupants to Shelter",
    description="Registers new admissions to shelter, validating against maximum capacity and closed status.",
)
def admit_occupants(
    shelter_id: str,
    payload: ShelterAdmissionRequest,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.admit_occupants(db, shelter_id, payload.count, payload.notes)


@router.post(
    "/shelters/{shelter_id}/discharge",
    response_model=ShelterResponse,
    status_code=status.HTTP_200_OK,
    summary="Discharge Occupants from Shelter",
    description="Records discharge of occupants, preventing negative occupancy and auto-restoring open status.",
)
def discharge_occupants(
    shelter_id: str,
    payload: ShelterDischargeRequest,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.discharge_occupants(db, shelter_id, payload.count, payload.notes)


@router.delete(
    "/shelters/{shelter_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Shelter Facility",
)
def delete_shelter(
    shelter_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.ADMIN_ROLES)),
):
    return coordination_service.delete_shelter(db, shelter_id)


# ==============================================================================
# Resources Endpoints (/api/v1/resources)
# ==============================================================================

@router.get(
    "/resources",
    response_model=ResourcePaginatedResponse,
    status_code=status.HTTP_200_OK,
    summary="List Emergency Resources",
    description="Returns relief supplies, medical assets, and equipment inventory with allocation status.",
)
def list_resources(
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    category: Optional[str] = Query(None, description="Category: Medical, Food & Water, Rescue Equipment, Power & Fuel"),
    shelter_id: Optional[str] = Query(None, description="Filter by depot shelter UUID"),
    low_stock_only: bool = Query(False, description="Filter resources with <= 25% available stock"),
    search: Optional[str] = Query(None, description="Search in name, code, storage location"),
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    items, total, total_pages = coordination_service.list_resources(
        db=db,
        page=page,
        page_size=page_size,
        category=category,
        shelter_id=shelter_id,
        low_stock_only=low_stock_only,
        search=search,
    )
    return ResourcePaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)


@router.post(
    "/resources",
    response_model=ResourceResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Add Resource Stockpile",
)
def create_resource(
    payload: ResourceCreate,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.create_resource(db, payload)


@router.get(
    "/resources/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Get Resource Details and Movement Audit",
)
def get_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(get_current_user),
):
    return coordination_service.get_resource(db, resource_id)


@router.patch(
    "/resources/{resource_id}",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Update Resource Details",
)
def update_resource(
    resource_id: str,
    payload: ResourceUpdatePatch,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.update_resource(db, resource_id, payload)


@router.post(
    "/resources/{resource_id}/allocate",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Allocate Resource to Mission, Incident, Team, or Shelter",
    description="Transactionally deducts available stock, validates inventory bounds, and writes a resource movement audit record.",
)
def allocate_resource(
    resource_id: str,
    payload: ResourceAllocateRequest,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.allocate_resource(db, resource_id, payload)


@router.post(
    "/resources/{resource_id}/return",
    response_model=ResourceResponse,
    status_code=status.HTTP_200_OK,
    summary="Return Allocated Resources to Stockpile",
    description="Transactionally restores available inventory and logs return dispatch audit.",
)
def return_resource(
    resource_id: str,
    payload: ResourceReturnRequest,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.STAFF_ROLES)),
):
    return coordination_service.return_resource(db, resource_id, payload)


@router.delete(
    "/resources/{resource_id}",
    status_code=status.HTTP_200_OK,
    summary="Delete Resource Stockpile",
)
def delete_resource(
    resource_id: str,
    db: Session = Depends(get_db),
    _user: UserIdentity = Depends(require_role(UserRole.ADMIN_ROLES)),
):
    return coordination_service.delete_resource(db, resource_id)
