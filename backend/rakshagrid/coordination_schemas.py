"""
Pydantic v2 Schemas for Phase 3 Coordination & Disaster Logistics
Enforces strict boundary checks, validation, and serialization for
Response Teams, Tasks, Shelters, Resources, and Allocations.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


VALID_TEAM_STATUSES = {"available", "assigned", "busy", "offline", "standby", "deployed"}
VALID_TASK_STATUSES = {"pending", "in_progress", "completed", "cancelled"}
VALID_TASK_PRIORITIES = {"low", "medium", "high", "critical"}
VALID_SHELTER_STATUSES = {"open", "full", "closed"}


# ==============================================================================
# Response Teams Schemas
# ==============================================================================

class TeamCreate(BaseModel):
    team_callsign: str = Field(..., min_length=2, max_length=100, description="Unique callsign for response unit")
    unit_type: str = Field(..., min_length=2, max_length=50, description="Unit type or specialization (e.g., NDRF, SDRF, Medical, HAZMAT)")
    personnel_count: int = Field(1, ge=1, description="Number of members deployed in the team")
    commander_name: str = Field(..., min_length=2, max_length=100, description="Lead commander or officer in charge")
    contact_channel: str = Field(..., min_length=2, max_length=100, description="Radio channel, satellite phone, or dispatch frequency")
    current_status: str = Field("available", description="Status: available, assigned, busy, offline")
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    base_location: str = Field(..., min_length=2, max_length=255, description="Staging base, station, or camp location")
    assigned_base_shelter_id: Optional[str] = Field(None, description="Optional UUID of assigned base shelter")
    assigned_incident_id: Optional[str] = Field(None, description="Optional UUID of assigned active incident")

    @field_validator("current_status")
    @classmethod
    def validate_team_status(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in VALID_TEAM_STATUSES:
            raise ValueError(f"Invalid team status '{v}'. Allowed: {sorted(list(VALID_TEAM_STATUSES))}")
        if norm == "standby":
            return "available"
        if norm == "deployed":
            return "assigned"
        return norm


class TeamUpdatePatch(BaseModel):
    team_callsign: Optional[str] = Field(None, min_length=2, max_length=100)
    unit_type: Optional[str] = Field(None, min_length=2, max_length=50)
    personnel_count: Optional[int] = Field(None, ge=1)
    commander_name: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_channel: Optional[str] = Field(None, min_length=2, max_length=100)
    current_status: Optional[str] = None
    current_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    current_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    base_location: Optional[str] = Field(None, min_length=2, max_length=255)
    assigned_base_shelter_id: Optional[str] = None
    assigned_incident_id: Optional[str] = None

    @field_validator("current_status")
    @classmethod
    def validate_team_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        norm = v.strip().lower()
        if norm not in VALID_TEAM_STATUSES:
            raise ValueError(f"Invalid team status '{v}'. Allowed: {sorted(list(VALID_TEAM_STATUSES))}")
        if norm == "standby":
            return "available"
        if norm == "deployed":
            return "assigned"
        return norm


class TeamResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    team_callsign: str
    unit_type: str
    personnel_count: int
    commander_name: str
    contact_channel: str
    current_status: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    base_location: str
    assigned_base_shelter_id: Optional[str] = None
    assigned_incident_id: Optional[str] = None
    assigned_incident_title: Optional[str] = None
    assigned_incident_code: Optional[str] = None
    active_tasks_count: int = 0
    created_at: datetime
    updated_at: datetime


class TeamPaginatedResponse(BaseModel):
    items: List[TeamResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==============================================================================
# Response Tasks Schemas
# ==============================================================================

class TaskCreate(BaseModel):
    incident_id: str = Field(..., description="UUID of linked incident")
    title: str = Field(..., min_length=3, max_length=255, description="Task headline or operational mission")
    description: str = Field(..., min_length=3, description="Detailed task directives and field instructions")
    priority: str = Field("high", description="Priority level: low, medium, high, critical")
    assigned_team_id: Optional[str] = Field(None, description="Optional UUID of assigned response unit")
    target_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    target_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    due_at: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid task priority '{v}'. Allowed: {sorted(list(VALID_TASK_PRIORITIES))}")
        return norm


class TaskUpdatePatch(BaseModel):
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, min_length=3)
    priority: Optional[str] = None
    status: Optional[str] = None
    assigned_team_id: Optional[str] = None
    target_latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    target_longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    due_at: Optional[datetime] = None

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        norm = v.strip().lower()
        if norm not in VALID_TASK_PRIORITIES:
            raise ValueError(f"Invalid task priority '{v}'. Allowed: {sorted(list(VALID_TASK_PRIORITIES))}")
        return norm

    @field_validator("status")
    @classmethod
    def validate_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        norm = v.strip().lower()
        if norm not in VALID_TASK_STATUSES:
            raise ValueError(f"Invalid task status '{v}'. Allowed: {sorted(list(VALID_TASK_STATUSES))}")
        return norm


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    incident_id: str
    incident_title: Optional[str] = None
    incident_code: Optional[str] = None
    assigned_team_id: Optional[str] = None
    assigned_team_callsign: Optional[str] = None
    title: str
    description: str
    priority: str
    status: str
    target_latitude: Optional[float] = None
    target_longitude: Optional[float] = None
    due_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime


class TaskPaginatedResponse(BaseModel):
    items: List[TaskResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==============================================================================
# Shelters Schemas
# ==============================================================================

class ShelterCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255, description="Facility or shelter name")
    shelter_type: str = Field(..., min_length=2, max_length=50, description="Cyclone Shelter, School Hall, Stadium, Tent Camp")
    capacity: int = Field(..., ge=1, description="Maximum occupant capacity")
    current_occupancy: int = Field(0, ge=0, description="Current sheltered headcount")
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    address: str = Field(..., min_length=3, description="Physical address or location description")
    contact_person: str = Field("Shelter Manager", min_length=2, max_length=100)
    contact_phone: str = Field("N/A", min_length=2, max_length=50)
    supplies_status: str = Field("adequate", max_length=30)
    power_backup: bool = True
    medical_station: bool = True
    status: str = Field("open", description="Status: open, full, closed")

    @field_validator("status")
    @classmethod
    def validate_shelter_status(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in VALID_SHELTER_STATUSES:
            raise ValueError(f"Invalid shelter status '{v}'. Allowed: {sorted(list(VALID_SHELTER_STATUSES))}")
        return norm

    @model_validator(mode="after")
    def validate_occupancy_capacity(self):
        if self.current_occupancy > self.capacity:
            raise ValueError(f"Occupancy ({self.current_occupancy}) cannot exceed capacity ({self.capacity})")
        return self


class ShelterUpdatePatch(BaseModel):
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    shelter_type: Optional[str] = Field(None, min_length=2, max_length=50)
    capacity: Optional[int] = Field(None, ge=1)
    current_occupancy: Optional[int] = Field(None, ge=0)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    address: Optional[str] = Field(None, min_length=3)
    contact_person: Optional[str] = Field(None, min_length=2, max_length=100)
    contact_phone: Optional[str] = Field(None, min_length=2, max_length=50)
    supplies_status: Optional[str] = None
    power_backup: Optional[bool] = None
    medical_station: Optional[bool] = None
    status: Optional[str] = None

    @field_validator("status")
    @classmethod
    def validate_shelter_status(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return None
        norm = v.strip().lower()
        if norm not in VALID_SHELTER_STATUSES:
            raise ValueError(f"Invalid shelter status '{v}'. Allowed: {sorted(list(VALID_SHELTER_STATUSES))}")
        return norm


class ShelterAdmissionRequest(BaseModel):
    count: int = Field(1, ge=1, description="Number of persons to admit")
    notes: Optional[str] = Field(None, description="Optional admission notes")


class ShelterDischargeRequest(BaseModel):
    count: int = Field(1, ge=1, description="Number of persons to discharge")
    notes: Optional[str] = Field(None, description="Optional discharge notes")


class ShelterResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    shelter_type: str
    capacity: int
    current_occupancy: int
    remaining_capacity: int
    occupancy_pct: float
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    address: str
    contact_person: str
    contact_phone: str
    supplies_status: str
    power_backup: bool
    medical_station: bool
    status: str
    created_at: datetime
    updated_at: datetime


class ShelterPaginatedResponse(BaseModel):
    items: List[ShelterResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


# ==============================================================================
# Resources Schemas
# ==============================================================================

class ResourceCreate(BaseModel):
    resource_code: str = Field(..., min_length=2, max_length=50, description="Unique inventory SKU or asset code")
    name: str = Field(..., min_length=2, max_length=255, description="Resource item name")
    category: str = Field(..., min_length=2, max_length=50, description="Medical, Food & Water, Rescue Equipment, etc.")
    quantity_total: float = Field(..., ge=0.0, description="Total physical inventory in stockpile")
    quantity_available: Optional[float] = Field(None, ge=0.0, description="Quantity available for dispatch")
    unit: str = Field(..., min_length=1, max_length=50, description="Measurement unit (kits, units, boxes, craft)")
    shelter_id: Optional[str] = Field(None, description="Assigned shelter depot if stored on-site")
    storage_location: Optional[str] = Field("Central Logistics Warehouse", max_length=255)
    status: str = Field("in_stock", max_length=30)

    @model_validator(mode="after")
    def set_and_validate_available(self):
        if self.quantity_available is None:
            self.quantity_available = self.quantity_total
        if self.quantity_available > self.quantity_total:
            raise ValueError(f"Available stock ({self.quantity_available}) cannot exceed total stock ({self.quantity_total})")
        return self


class ResourceUpdatePatch(BaseModel):
    resource_code: Optional[str] = Field(None, min_length=2, max_length=50)
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    category: Optional[str] = Field(None, min_length=2, max_length=50)
    quantity_total: Optional[float] = Field(None, ge=0.0)
    quantity_available: Optional[float] = Field(None, ge=0.0)
    unit: Optional[str] = Field(None, min_length=1, max_length=50)
    shelter_id: Optional[str] = None
    storage_location: Optional[str] = None
    status: Optional[str] = None


class ResourceAllocateRequest(BaseModel):
    quantity: float = Field(..., gt=0.0, description="Amount of resource to allocate")
    destination_location: str = Field(..., min_length=2, max_length=255, description="Target destination, team, or shelter")
    transport_mode: Optional[str] = Field("Ground Logistics", max_length=50)
    incident_id: Optional[str] = Field(None, description="Optional linked incident UUID")
    task_id: Optional[str] = Field(None, description="Optional linked task UUID")
    team_id: Optional[str] = Field(None, description="Optional linked response team UUID")
    shelter_id: Optional[str] = Field(None, description="Optional linked shelter UUID")
    notes: Optional[str] = Field(None, description="Operational justification or dispatch notes")


class ResourceReturnRequest(BaseModel):
    quantity: float = Field(..., gt=0.0, description="Amount of resource being returned to inventory")
    source_location: str = Field(..., min_length=2, max_length=255, description="Origin location of returned assets")
    notes: Optional[str] = Field(None, description="Return verification notes")


class ResourceMovementResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_id: str
    source_location: str
    destination_location: str
    quantity: float
    status: str
    transport_mode: str
    dispatched_at: datetime
    delivered_at: Optional[datetime] = None
    incident_id: Optional[str] = None
    task_id: Optional[str] = None
    team_id: Optional[str] = None
    shelter_id: Optional[str] = None
    notes: Optional[str] = None
    created_at: datetime


class ResourceResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    resource_code: str
    name: str
    category: str
    quantity_total: float
    quantity_available: float
    allocated_quantity: float
    unit: str
    shelter_id: Optional[str] = None
    shelter_name: Optional[str] = None
    storage_location: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: datetime
    recent_movements: List[ResourceMovementResponse] = []


class ResourcePaginatedResponse(BaseModel):
    items: List[ResourceResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
