"""
RakshaGrid Database Models
SQLAlchemy 2.0 ORM definitions for Disaster Intelligence and Response entities.
Implements UUID primary keys, relational foreign keys, indexed query paths,
and timestamped audit records.
"""

import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import relationship

from backend.database.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class Incident(Base):
    """
    Primary Disaster Incident Entity.
    Represents an active, monitoring, or historical disaster event (flood, cyclone, earthquake, etc.).
    """

    __tablename__ = "incidents"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    disaster_type = Column(String(50), nullable=False, index=True)  # flood, cyclone, earthquake, wildfire, landslide, industrial
    severity = Column(String(20), nullable=False, index=True)  # critical, severe, moderate, minor
    status = Column(String(20), nullable=False, index=True, default="active")  # active, contained, assessing, closed
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    location_name = Column(String(255), nullable=False)
    affected_region = Column(String(255), nullable=False)
    affected_population_estimate = Column(Integer, default=0)
    casualty_count_estimate = Column(Integer, default=0)
    
    description = Column(Text, nullable=True)
    reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    updates = relationship("IncidentUpdate", back_populates="incident", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="incident")
    tasks = relationship("ResponseTask", back_populates="incident", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="incident")

    __table_args__ = (
        Index("ix_incidents_type_status", "disaster_type", "status"),
        Index("ix_incidents_lat_lon", "latitude", "longitude"),
        CheckConstraint("severity IN ('critical', 'severe', 'moderate', 'minor')", name="ck_incident_severity"),
        CheckConstraint("status IN ('active', 'contained', 'assessing', 'closed')", name="ck_incident_status"),
    )


class IncidentUpdate(Base):
    """
    Chronological Field and Situation Report Updates for an Incident.
    """

    __tablename__ = "incident_updates"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    author_name = Column(String(100), nullable=False)
    author_role = Column(String(100), nullable=False)  # e.g., On-site Incident Commander, NDRF Lead, Drone Operator
    update_type = Column(String(50), nullable=False)  # situation_report, casualty_update, containment, weather, evacuation
    message = Column(Text, nullable=False)
    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    incident = relationship("Incident", back_populates="updates")


class Alert(Base):
    """
    Public and Operational Emergency Alert Broadcast.
    Conforms to emergency warning and CAP (Common Alerting Protocol) conventions.
    """

    __tablename__ = "alerts"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_code = Column(String(50), unique=True, nullable=False, index=True)
    headline = Column(String(255), nullable=False)
    urgency = Column(String(20), nullable=False)  # immediate, expected, future, past
    severity = Column(String(20), nullable=False, index=True)  # extreme, severe, moderate, minor
    certainty = Column(String(20), nullable=False)  # observed, likely, possible, unlikely
    target_region = Column(String(255), nullable=False)
    evacuation_recommended = Column(Boolean, default=False, nullable=False)
    instructions = Column(Text, nullable=False)
    broadcast_status = Column(String(20), nullable=False, default="active", index=True)  # active, expired, cancelled, draft
    
    issued_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("Incident", back_populates="alerts")

    __table_args__ = (
        CheckConstraint("broadcast_status IN ('active', 'expired', 'cancelled', 'draft')", name="ck_alert_status"),
    )


class ResponseTeam(Base):
    """
    Emergency Response and Rescue Unit (NDRF, SDRF, Medical, HAZMAT, Aerial Drone Recon).
    """

    __tablename__ = "response_teams"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    team_callsign = Column(String(100), unique=True, nullable=False, index=True)
    unit_type = Column(String(50), nullable=False, index=True)  # ndrf, sdrf, medical_triage, fire_rescue, hazmat, aerial_drone, logistics
    personnel_count = Column(Integer, nullable=False, default=1)
    commander_name = Column(String(100), nullable=False)
    contact_channel = Column(String(100), nullable=False)  # VHF channel, satellite comms, cellular
    current_status = Column(String(30), nullable=False, default="standby", index=True)  # deployed, standby, en_route, resting, off_duty
    
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    base_location = Column(String(255), nullable=False)
    assigned_base_shelter_id = Column(UUID(as_uuid=True), ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    tasks = relationship("ResponseTask", back_populates="assigned_team")
    base_shelter = relationship("Shelter", foreign_keys=[assigned_base_shelter_id])


class ResponseTask(Base):
    """
    Actionable Task dispatched to Response Teams during an active incident.
    """

    __tablename__ = "response_tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_team_id = Column(UUID(as_uuid=True), ForeignKey("response_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="high", index=True)  # critical, high, medium, low
    status = Column(String(20), nullable=False, default="pending", index=True)  # pending, assigned, in_progress, completed, aborted
    
    target_latitude = Column(Float, nullable=True)
    target_longitude = Column(Float, nullable=True)
    due_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    incident = relationship("Incident", back_populates="tasks")
    assigned_team = relationship("ResponseTeam", back_populates="tasks")


class Shelter(Base):
    """
    Emergency Evacuation Shelter or Relief Camp Facility.
    """

    __tablename__ = "shelters"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    shelter_type = Column(String(50), nullable=False)  # school, stadium, community_center, temporary_tent, medical_camp
    capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, nullable=False, default=0)
    
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    address = Column(Text, nullable=False)
    contact_person = Column(String(100), nullable=False)
    contact_phone = Column(String(50), nullable=False)
    
    supplies_status = Column(String(30), nullable=False, default="adequate")  # adequate, low, critical
    power_backup = Column(Boolean, default=True, nullable=False)
    medical_station = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), nullable=False, default="open", index=True)  # open, full, standby, closed
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    resources = relationship("Resource", back_populates="shelter")


class Resource(Base):
    """
    Relief Resource Stockpile (Medical kits, water purification, inflatable rafts, rations, generators).
    """

    __tablename__ = "resources"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)  # medical, food_water, rescue_equipment, shelter_gear, power_fuel
    quantity_total = Column(Float, nullable=False, default=0.0)
    quantity_available = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False)  # units, liters, metric_tons, kits, packs
    shelter_id = Column(UUID(as_uuid=True), ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    shelter = relationship("Shelter", back_populates="resources")
    movements = relationship("ResourceMovement", back_populates="resource")


class ResourceMovement(Base):
    """
    Log of Emergency Supplies and Asset Dispatches between Warehouses and Shelters.
    """

    __tablename__ = "resource_movements"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    resource_id = Column(UUID(as_uuid=True), ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_location = Column(String(255), nullable=False)
    destination_location = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String(30), nullable=False, default="dispatched", index=True)  # requested, dispatched, in_transit, delivered, cancelled
    transport_mode = Column(String(50), nullable=False)  # road_truck, airlift_helo, boat, foot_courier
    
    dispatched_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    resource = relationship("Resource", back_populates="movements")


class EnvironmentalObservation(Base):
    """
    Sensor & Telemetry Observation (River level gauges, rain gauges, seismic sensors, wind speed).
    """

    __tablename__ = "environmental_observations"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    station_id = Column(String(100), nullable=False, index=True)
    station_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False, index=True)  # water_level_meters, rainfall_mm_hr, wind_gust_kmh, seismic_magnitude
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="nominal", index=True)  # nominal, warning, alert, emergency
    
    recorded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class RiskAssessment(Base):
    """
    Hazard Risk Evaluation and Impact Projection.
    """

    __tablename__ = "risk_assessments"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    incident_id = Column(UUID(as_uuid=True), ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    target_area = Column(String(255), nullable=False)
    hazard_type = Column(String(50), nullable=False)
    calculated_risk_score = Column(Float, nullable=False)  # 0.0 to 100.0
    risk_level = Column(String(20), nullable=False, index=True)  # low, moderate, high, extreme
    simulated_factors = Column(Text, nullable=True)  # JSON-encoded factors
    recommended_interventions = Column(Text, nullable=False)
    
    assessed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("Incident", back_populates="risk_assessments")


class AuditLog(Base):
    """
    Immutable Operational Audit Trail of Dispatch Actions and Decision Gate Overrides.
    """

    __tablename__ = "audit_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    actor_id = Column(String(100), nullable=False, index=True)
    actor_role = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False, index=True)  # dispatch_team, issue_alert, reallocate_supplies, change_status
    entity_type = Column(String(50), nullable=False)  # incident, alert, team, task, shelter
    entity_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)  # JSON-encoded change payload
    ip_address = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
