"""
RakshaGrid Database Models
SQLAlchemy 2.0 ORM definitions for Disaster Intelligence and Response entities.
Implements UUID primary keys, relational foreign keys, indexed query paths,
and timestamped audit records.
"""

import json
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
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
    Uuid,
)
from sqlalchemy.orm import relationship

from backend.database.session import Base


def utcnow():
    return datetime.now(timezone.utc)


class Incident(Base):
    """
    Primary Disaster Incident Entity.
    Represents an active, monitored, or historical disaster event.
    """

    __tablename__ = "incidents"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_code = Column(String(50), unique=True, nullable=False, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Required Phase 2 Fields
    category = Column(String(50), nullable=False, index=True, default="other")
    severity = Column(String(20), nullable=False, index=True, default="medium")
    status = Column(String(30), nullable=False, index=True, default="reported")

    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    location_description = Column(String(255), nullable=True)

    source_type = Column(String(50), nullable=False, default="operator_report", index=True)
    verification_status = Column(String(30), nullable=False, default="unverified", index=True)

    reported_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    created_by = Column(String(100), nullable=False, default="system")
    assigned_commander = Column(String(100), nullable=True)
    affected_population = Column(Integer, nullable=True, default=0)

    # Timestamps
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    # Relationships
    updates = relationship(
        "IncidentUpdate",
        back_populates="incident",
        cascade="all, delete-orphan",
        order_by="desc(IncidentUpdate.created_at)",
    )
    alerts = relationship("Alert", back_populates="incident")
    tasks = relationship("ResponseTask", back_populates="incident", cascade="all, delete-orphan")
    risk_assessments = relationship("RiskAssessment", back_populates="incident")

    __table_args__ = (
        Index("ix_incidents_category_status", "category", "status"),
        Index("ix_incidents_lat_lon", "latitude", "longitude"),
        CheckConstraint(
            "category IN ('flood', 'severe_weather', 'wildfire', 'earthquake', 'landslide', 'industrial_accident', 'other')",
            name="ck_incident_category",
        ),
        CheckConstraint(
            "severity IN ('low', 'medium', 'high', 'critical')",
            name="ck_incident_severity",
        ),
        CheckConstraint(
            "status IN ('reported', 'under_assessment', 'confirmed', 'response_active', 'contained', 'resolved', 'closed')",
            name="ck_incident_status",
        ),
        CheckConstraint(
            "source_type IN ('operator_report', 'external_source', 'simulation')",
            name="ck_incident_source_type",
        ),
        CheckConstraint(
            "verification_status IN ('unverified', 'under_review', 'verified')",
            name="ck_incident_verification_status",
        ),
        CheckConstraint(
            "latitude IS NULL OR (latitude >= -90.0 AND latitude <= 90.0)",
            name="ck_incident_latitude",
        ),
        CheckConstraint(
            "longitude IS NULL OR (longitude >= -180.0 AND longitude <= 180.0)",
            name="ck_incident_longitude",
        ),
        CheckConstraint(
            "affected_population IS NULL OR affected_population >= 0",
            name="ck_incident_affected_pop",
        ),
    )

    # Backward compatibility properties for Phase 1 code
    @property
    def disaster_type(self) -> str:
        return self.category

    @disaster_type.setter
    def disaster_type(self, value: str):
        self.category = value

    @property
    def location_name(self) -> str:
        return self.location_description or "Unspecified Location"

    @location_name.setter
    def location_name(self, value: str):
        self.location_description = value

    @property
    def affected_region(self) -> str:
        return self.location_description or "Regional Operations"

    @affected_region.setter
    def affected_region(self, value: str):
        pass

    @property
    def affected_population_estimate(self) -> int:
        return self.affected_population or 0

    @affected_population_estimate.setter
    def affected_population_estimate(self, value: int):
        self.affected_population = value

    @property
    def casualty_count_estimate(self) -> int:
        return 0

    @casualty_count_estimate.setter
    def casualty_count_estimate(self, value: int):
        pass


class IncidentUpdate(Base):
    """
    Chronological Field, Status, and Situation Report History for an Incident.
    Guarantees immutable historical audit log of all changes.
    """

    __tablename__ = "incident_updates"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    actor_id = Column(String(100), nullable=True, index=True, default="system")

    previous_status = Column(String(30), nullable=True)
    new_status = Column(String(30), nullable=True)

    update_type = Column(String(50), nullable=False, default="situation_report", index=True)
    message = Column(Text, nullable=False)
    metadata_payload = Column(Text, nullable=True)  # JSON-encoded structured audit context

    verified = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)

    incident = relationship("Incident", back_populates="updates")

    # Backward compatibility properties
    @property
    def author_name(self) -> str:
        return self.actor_id or "System Operator"

    @author_name.setter
    def author_name(self, val: str):
        self.actor_id = val

    @property
    def author_role(self) -> str:
        return "Field Commander"

    @property
    def parsed_metadata(self) -> Dict[str, Any]:
        if not self.metadata_payload:
            return {}
        try:
            return json.loads(self.metadata_payload)
        except Exception:
            return {}


class Alert(Base):
    """
    Public and Operational Emergency Alert Broadcast.
    Conforms to emergency warning and CAP (Common Alerting Protocol) conventions.
    """

    __tablename__ = "alerts"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    alert_code = Column(String(50), unique=True, nullable=False, index=True)
    headline = Column(String(255), nullable=False)
    urgency = Column(String(20), nullable=False)
    severity = Column(String(20), nullable=False, index=True)
    certainty = Column(String(20), nullable=False)
    target_region = Column(String(255), nullable=False)
    evacuation_recommended = Column(Boolean, default=False, nullable=False)
    instructions = Column(Text, nullable=False)
    broadcast_status = Column(String(20), nullable=False, default="active", index=True)
    
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

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    team_callsign = Column(String(100), unique=True, nullable=False, index=True)
    unit_type = Column(String(50), nullable=False, index=True)
    personnel_count = Column(Integer, nullable=False, default=1)
    commander_name = Column(String(100), nullable=False)
    contact_channel = Column(String(100), nullable=False)
    current_status = Column(String(30), nullable=False, default="available", index=True)
    
    current_latitude = Column(Float, nullable=True)
    current_longitude = Column(Float, nullable=True)
    base_location = Column(String(255), nullable=False)
    assigned_base_shelter_id = Column(Uuid, ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True)
    assigned_incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    tasks = relationship("ResponseTask", back_populates="assigned_team")
    base_shelter = relationship("Shelter", foreign_keys=[assigned_base_shelter_id])
    assigned_incident = relationship("Incident", foreign_keys=[assigned_incident_id])

    # Backward compatibility and ergonomic aliases
    @property
    def name(self) -> str:
        return self.team_callsign

    @name.setter
    def name(self, val: str):
        self.team_callsign = val

    @property
    def status(self) -> str:
        return self.current_status

    @status.setter
    def status(self, val: str):
        self.current_status = val

    @property
    def specialization(self) -> str:
        return self.unit_type

    @specialization.setter
    def specialization(self, val: str):
        self.unit_type = val

    @property
    def member_count(self) -> int:
        return self.personnel_count

    @member_count.setter
    def member_count(self, val: int):
        self.personnel_count = val


class ResponseTask(Base):
    """
    Actionable Task dispatched to Response Teams during an active incident.
    """

    __tablename__ = "response_tasks"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False, index=True)
    assigned_team_id = Column(Uuid, ForeignKey("response_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    priority = Column(String(20), nullable=False, default="high", index=True)
    status = Column(String(20), nullable=False, default="pending", index=True)
    
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

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False, index=True)
    shelter_type = Column(String(50), nullable=False)
    capacity = Column(Integer, nullable=False)
    current_occupancy = Column(Integer, nullable=False, default=0)
    
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    address = Column(Text, nullable=False)
    contact_person = Column(String(100), nullable=False, default="Shelter Manager")
    contact_phone = Column(String(50), nullable=False, default="N/A")
    
    supplies_status = Column(String(30), nullable=False, default="adequate")
    power_backup = Column(Boolean, default=True, nullable=False)
    medical_station = Column(Boolean, default=True, nullable=False)
    status = Column(String(20), nullable=False, default="open", index=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    resources = relationship("Resource", back_populates="shelter")

    @property
    def remaining_capacity(self) -> int:
        return max(0, (self.capacity or 0) - (self.current_occupancy or 0))

    @property
    def occupancy(self) -> int:
        return self.current_occupancy or 0

    @occupancy.setter
    def occupancy(self, val: int):
        self.current_occupancy = val


class Resource(Base):
    """
    Relief Resource Stockpile (Medical kits, water purification, inflatable rafts, rations, generators).
    """

    __tablename__ = "resources"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    resource_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    category = Column(String(50), nullable=False, index=True)
    quantity_total = Column(Float, nullable=False, default=0.0)
    quantity_available = Column(Float, nullable=False, default=0.0)
    unit = Column(String(50), nullable=False)
    shelter_id = Column(Uuid, ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True, index=True)
    storage_location = Column(String(255), nullable=True, default="Central Logistics Warehouse")
    status = Column(String(30), nullable=False, default="in_stock", index=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    updated_at = Column(DateTime(timezone=True), default=utcnow, onupdate=utcnow, nullable=False)

    shelter = relationship("Shelter", back_populates="resources")
    movements = relationship("ResourceMovement", back_populates="resource")


class ResourceMovement(Base):
    """
    Log of Emergency Supplies and Asset Dispatches between Warehouses and Shelters.
    """

    __tablename__ = "resource_movements"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    resource_id = Column(Uuid, ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False, index=True)
    source_location = Column(String(255), nullable=False)
    destination_location = Column(String(255), nullable=False)
    quantity = Column(Float, nullable=False)
    status = Column(String(30), nullable=False, default="dispatched", index=True)
    transport_mode = Column(String(50), nullable=False)
    
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    task_id = Column(Uuid, ForeignKey("response_tasks.id", ondelete="SET NULL"), nullable=True, index=True)
    team_id = Column(Uuid, ForeignKey("response_teams.id", ondelete="SET NULL"), nullable=True, index=True)
    shelter_id = Column(Uuid, ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True, index=True)
    notes = Column(Text, nullable=True)

    dispatched_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    delivered_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    resource = relationship("Resource", back_populates="movements")


class EnvironmentalObservation(Base):
    """
    Sensor & Telemetry Observation (River level gauges, rain gauges, seismic sensors, wind speed).
    """

    __tablename__ = "environmental_observations"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    station_id = Column(String(100), nullable=False, index=True)
    station_name = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    metric_type = Column(String(50), nullable=False, index=True)
    value = Column(Float, nullable=False)
    unit = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False, default="nominal", index=True)
    
    recorded_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)


class RiskAssessment(Base):
    """
    Hazard Risk Evaluation and Impact Projection.
    """

    __tablename__ = "risk_assessments"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    incident_id = Column(Uuid, ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True, index=True)
    target_area = Column(String(255), nullable=False)
    hazard_type = Column(String(50), nullable=False)
    calculated_risk_score = Column(Float, nullable=False)
    risk_level = Column(String(20), nullable=False, index=True)
    simulated_factors = Column(Text, nullable=True)
    recommended_interventions = Column(Text, nullable=False)
    
    assessed_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False)

    incident = relationship("Incident", back_populates="risk_assessments")


class AuditLog(Base):
    """
    Immutable Operational Audit Trail of Dispatch Actions and Decision Gate Overrides.
    """

    __tablename__ = "audit_logs"

    id = Column(Uuid, primary_key=True, default=uuid.uuid4)
    actor_id = Column(String(100), nullable=False, index=True)
    actor_role = Column(String(100), nullable=False)
    action = Column(String(100), nullable=False, index=True)
    entity_type = Column(String(50), nullable=False)
    entity_id = Column(String(100), nullable=False)
    details = Column(Text, nullable=True)
    ip_address = Column(String(50), nullable=True)
    
    created_at = Column(DateTime(timezone=True), default=utcnow, nullable=False, index=True)
