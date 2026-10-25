"""
Pydantic v2 Schemas for RakshaGrid Incident Management
Defines request validation rules, coordinate boundaries,
enumerated classifications, and structured response representations.
"""

from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator


class IncidentCategory(str, Enum):
    FLOOD = "flood"
    SEVERE_WEATHER = "severe_weather"
    WILDFIRE = "wildfire"
    EARTHQUAKE = "earthquake"
    LANDSLIDE = "landslide"
    INDUSTRIAL_ACCIDENT = "industrial_accident"
    OTHER = "other"

    @classmethod
    def normalize(cls, value: str) -> "IncidentCategory":
        cleaned = value.lower().strip().replace(" ", "_").replace("-", "_")
        # Handle synonyms
        synonyms = {
            "cyclone": cls.SEVERE_WEATHER,
            "storm": cls.SEVERE_WEATHER,
            "hurricane": cls.SEVERE_WEATHER,
            "industrial": cls.INDUSTRIAL_ACCIDENT,
            "chemical": cls.INDUSTRIAL_ACCIDENT,
            "fire": cls.WILDFIRE,
            "quake": cls.EARTHQUAKE,
        }
        if cleaned in synonyms:
            return synonyms[cleaned]
        for member in cls:
            if member.value == cleaned:
                return member
        return cls.OTHER


class IncidentSeverity(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

    @classmethod
    def normalize(cls, value: str) -> "IncidentSeverity":
        cleaned = value.lower().strip()
        synonyms = {
            "minor": cls.LOW,
            "moderate": cls.MEDIUM,
            "severe": cls.HIGH,
            "extreme": cls.CRITICAL,
        }
        if cleaned in synonyms:
            return synonyms[cleaned]
        for member in cls:
            if member.value == cleaned:
                return member
        raise ValueError(f"Invalid severity '{value}'. Allowed: {[m.value for m in cls]}")


class IncidentStatus(str, Enum):
    REPORTED = "reported"
    UNDER_ASSESSMENT = "under_assessment"
    CONFIRMED = "confirmed"
    RESPONSE_ACTIVE = "response_active"
    CONTAINED = "contained"
    RESOLVED = "resolved"
    CLOSED = "closed"

    @classmethod
    def normalize(cls, value: str) -> "IncidentStatus":
        cleaned = value.lower().strip().replace(" ", "_").replace("-", "_")
        synonyms = {
            "active": cls.RESPONSE_ACTIVE,
            "assessing": cls.UNDER_ASSESSMENT,
            "open": cls.REPORTED,
        }
        if cleaned in synonyms:
            return synonyms[cleaned]
        for member in cls:
            if member.value == cleaned:
                return member
        raise ValueError(f"Invalid status '{value}'. Allowed: {[m.value for m in cls]}")


class VerificationStatus(str, Enum):
    UNVERIFIED = "unverified"
    UNDER_REVIEW = "under_review"
    VERIFIED = "verified"


class SourceType(str, Enum):
    OPERATOR_REPORT = "operator_report"
    EXTERNAL_SOURCE = "external_source"
    SIMULATION = "simulation"


# Valid status state transitions map
VALID_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    IncidentStatus.REPORTED: [IncidentStatus.UNDER_ASSESSMENT, IncidentStatus.CONFIRMED, IncidentStatus.CLOSED],
    IncidentStatus.UNDER_ASSESSMENT: [IncidentStatus.CONFIRMED, IncidentStatus.CLOSED],
    IncidentStatus.CONFIRMED: [IncidentStatus.RESPONSE_ACTIVE, IncidentStatus.CONTAINED, IncidentStatus.CLOSED],
    IncidentStatus.RESPONSE_ACTIVE: [IncidentStatus.CONTAINED, IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
    IncidentStatus.CONTAINED: [IncidentStatus.RESPONSE_ACTIVE, IncidentStatus.RESOLVED, IncidentStatus.CLOSED],
    IncidentStatus.RESOLVED: [IncidentStatus.CLOSED, IncidentStatus.RESPONSE_ACTIVE],
    IncidentStatus.CLOSED: [IncidentStatus.UNDER_ASSESSMENT],  # Reopening requires re-assessment
}


class IncidentCreate(BaseModel):
    """Payload for creating a new incident."""
    title: str = Field(..., min_length=3, max_length=255, description="Headline description of the disaster event")
    description: Optional[str] = Field(None, max_length=5000, description="Detailed operational overview")
    category: IncidentCategory = Field(default=IncidentCategory.OTHER)
    severity: IncidentSeverity = Field(default=IncidentSeverity.MEDIUM)
    status: IncidentStatus = Field(default=IncidentStatus.REPORTED)
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0, description="WGS84 latitude (-90 to 90)")
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0, description="WGS84 longitude (-180 to 180)")
    location_description: Optional[str] = Field(None, max_length=255, description="Human-readable location or sector")
    source_type: SourceType = Field(default=SourceType.OPERATOR_REPORT)
    verification_status: VerificationStatus = Field(default=VerificationStatus.UNVERIFIED)
    reported_at: Optional[datetime] = Field(default=None)
    assigned_commander: Optional[str] = Field(None, max_length=100)
    affected_population: Optional[int] = Field(default=0, ge=0, description="Estimated population count (>= 0)")

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentCategory.normalize(v)
        return v

    @field_validator("severity", mode="before")
    @classmethod
    def parse_severity(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentSeverity.normalize(v)
        return v

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentStatus.normalize(v)
        return v


class IncidentUpdatePatch(BaseModel):
    """Payload for modifying an existing incident record."""
    title: Optional[str] = Field(None, min_length=3, max_length=255)
    description: Optional[str] = Field(None, max_length=5000)
    category: Optional[IncidentCategory] = None
    severity: Optional[IncidentSeverity] = None
    status: Optional[IncidentStatus] = None
    latitude: Optional[float] = Field(None, ge=-90.0, le=90.0)
    longitude: Optional[float] = Field(None, ge=-180.0, le=180.0)
    location_description: Optional[str] = Field(None, max_length=255)
    source_type: Optional[SourceType] = None
    verification_status: Optional[VerificationStatus] = None
    assigned_commander: Optional[str] = Field(None, max_length=100)
    affected_population: Optional[int] = Field(None, ge=0)
    change_reason: Optional[str] = Field(None, max_length=500, description="Required justification note when closing or escalating")

    @field_validator("category", mode="before")
    @classmethod
    def parse_category(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentCategory.normalize(v)
        return v

    @field_validator("severity", mode="before")
    @classmethod
    def parse_severity(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentSeverity.normalize(v)
        return v

    @field_validator("status", mode="before")
    @classmethod
    def parse_status(cls, v: Any) -> Any:
        if isinstance(v, str):
            return IncidentStatus.normalize(v)
        return v


class IncidentResponse(BaseModel):
    """Complete serialized representation of an incident."""
    id: str
    incident_code: str
    title: str
    description: Optional[str] = None
    category: str
    severity: str
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    location_description: Optional[str] = None
    source_type: str
    verification_status: str
    reported_at: datetime
    created_by: str
    assigned_commander: Optional[str] = None
    affected_population: int = 0
    created_at: datetime
    updated_at: datetime
    updates_count: int = 0

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", mode="before")
    @classmethod
    def serialize_id(cls, v: Any) -> str:
        return str(v) if v is not None else ""


class IncidentPaginatedResponse(BaseModel):
    """Paginated collection of incidents."""
    items: List[IncidentResponse]
    total: int
    page: int
    page_size: int
    total_pages: int


class IncidentUpdateCreate(BaseModel):
    """Payload for appending an operational situation update or timeline log."""
    message: str = Field(..., min_length=2, max_length=4000, description="Field update content")
    update_type: str = Field(default="situation_report", description="creation, status_change, situation_report, field_note, or closure")
    new_status: Optional[IncidentStatus] = None
    metadata_payload: Optional[Dict[str, Any]] = None

    @field_validator("new_status", mode="before")
    @classmethod
    def parse_new_status(cls, v: Any) -> Any:
        if isinstance(v, str) and v.strip():
            return IncidentStatus.normalize(v)
        return v


class IncidentUpdateResponse(BaseModel):
    """Chronological timeline update record."""
    id: str
    incident_id: str
    actor_id: Optional[str] = None
    previous_status: Optional[str] = None
    new_status: Optional[str] = None
    update_type: str
    message: str
    metadata_payload: Optional[Dict[str, Any]] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("id", "incident_id", mode="before")
    @classmethod
    def serialize_uuids(cls, v: Any) -> str:
        return str(v) if v is not None else ""
