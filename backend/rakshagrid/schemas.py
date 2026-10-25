"""
RakshaGrid Pydantic v2 Schemas
Defines structured, validated request and response payloads
for disaster monitoring, alerting, team deployment, and system telemetry.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class SubsystemHealth(BaseModel):
    """Status metadata for an individual RakshaGrid subsystem."""
    status: str = Field(..., description="operational, degraded, service_unavailable, or unconfigured")
    details: str = Field(..., description="Diagnostic summary or limitation explanation")
    latency_ms: Optional[float] = Field(default=None, description="Response time in milliseconds")


class RakshaGridHealthResponse(BaseModel):
    """Structured response for /api/rakshagrid/health."""
    status: str = Field(..., description="Overall health: operational, degraded, or maintenance")
    project: str = Field(default="RakshaGrid", description="Subsystem name")
    subtitle: str = Field(default="Disaster Intelligence and Response", description="Platform subtitle")
    version: str = Field(..., description="Semantic release version")
    environment: str = Field(..., description="development, staging, production, or test")
    demo_mode_active: bool = Field(..., description="Whether simulated/demo data is serving")
    defcon_level: int = Field(..., description="Current disaster threat severity level (1-5)")
    uptime_seconds: float = Field(..., description="Subsystem uptime")
    subsystems: Dict[str, SubsystemHealth] = Field(..., description="Individual subsystem health metrics")
    timestamp: datetime = Field(..., description="UTC server timestamp")


class DatabaseStatusResponse(BaseModel):
    """Database connectivity and migration status report."""
    configured: bool = Field(..., description="Whether database credentials or URL are set")
    host: str = Field(..., description="Target database host")
    port: int = Field(..., description="Target database port")
    database: str = Field(..., description="Target database name")
    status: str = Field(..., description="connected, service_unavailable, auth_failed, or disconnected")
    connection: bool = Field(..., description="Whether active TCP connection and SELECT 1 succeeded")
    latency_ms: Optional[float] = Field(default=None, description="Round-trip query latency in ms")
    detail: str = Field(..., description="Status explanation or setup guidance")
    active_migration_version: str = Field(default="0001_initial", description="Target Alembic migration revision")
    models_registered_count: int = Field(default=11, description="Number of declared SQLAlchemy models")


class IncidentSummary(BaseModel):
    """Disaster incident record summary."""
    id: str
    incident_code: str
    title: str
    disaster_type: str
    severity: str
    status: str
    latitude: float
    longitude: float
    location_name: str
    affected_region: str
    affected_population_estimate: int
    casualty_count_estimate: int
    description: Optional[str] = None
    reported_at: datetime
    updated_at: datetime
    is_demo: bool = Field(default=True, description="Indicates simulated demonstration data")


class AlertSummary(BaseModel):
    """Emergency alert broadcast summary."""
    id: str
    alert_code: str
    headline: str
    urgency: str
    severity: str
    certainty: str
    target_region: str
    evacuation_recommended: bool
    instructions: str
    broadcast_status: str
    issued_at: datetime
    expires_at: Optional[datetime] = None
    is_demo: bool = Field(default=True)


class ResponseTeamSummary(BaseModel):
    """Response team unit summary."""
    id: str
    team_callsign: str
    unit_type: str
    personnel_count: int
    commander_name: str
    contact_channel: str
    current_status: str
    base_location: str
    current_latitude: Optional[float] = None
    current_longitude: Optional[float] = None
    is_demo: bool = Field(default=True)


class ShelterSummary(BaseModel):
    """Evacuation shelter status summary."""
    id: str
    name: str
    shelter_type: str
    capacity: int
    current_occupancy: int
    occupancy_percent: float
    location_name: str
    supplies_status: str
    power_backup: bool
    medical_station: bool
    status: str
    is_demo: bool = Field(default=True)


class OverviewStats(BaseModel):
    """Tactical overview dashboard statistics."""
    defcon_level: int
    threat_description: str
    active_incidents_count: int
    critical_incidents_count: int
    deployed_teams_count: int
    active_alerts_count: int
    shelters_open_count: int
    total_sheltered_population: int
    total_shelter_capacity: int
    overall_shelter_occupancy_pct: float
    resource_readiness_pct: float
    database_status: str
    demo_mode_active: bool


class OverviewResponse(BaseModel):
    """Complete response for /api/rakshagrid/overview."""
    stats: OverviewStats
    active_incidents: List[IncidentSummary]
    high_priority_alerts: List[AlertSummary]
    recent_activity: List[Dict[str, Any]]
    disclaimer: str = Field(
        default="[FICTIONAL DEMO DATA - PHASE 1 FOUNDATION] Real-time sensors and live GPS tracking are deferred to Phase 2.",
        description="Clear Phase 1 demonstration data label",
    )


class RakshaGridErrorResponse(BaseModel):
    """Structured error payload conforming to platform conventions."""
    error: str = Field(..., description="Error classification")
    message: str = Field(..., description="Human-readable explanation")
    detail: Optional[str] = Field(default=None, description="Detailed diagnostic context")
    timestamp: datetime = Field(..., description="UTC error timestamp")
