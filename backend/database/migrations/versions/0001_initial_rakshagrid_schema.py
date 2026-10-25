"""initial_rakshagrid_schema

Revision ID: 0001_initial
Revises: 
Create Date: 2026-10-25 12:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Incidents
    op.create_table(
        "incidents",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_code", sa.String(length=50), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("disaster_type", sa.String(length=50), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("location_name", sa.String(length=255), nullable=False),
        sa.Column("affected_region", sa.String(length=255), nullable=False),
        sa.Column("affected_population_estimate", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("casualty_count_estimate", sa.Integer(), nullable=True, server_default="0"),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("reported_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("severity IN ('critical', 'severe', 'moderate', 'minor')", name="ck_incident_severity"),
        sa.CheckConstraint("status IN ('active', 'contained', 'assessing', 'closed')", name="ck_incident_status"),
    )
    op.create_index("ix_incidents_incident_code", "incidents", ["incident_code"], unique=True)
    op.create_index("ix_incidents_disaster_type", "incidents", ["disaster_type"])
    op.create_index("ix_incidents_severity", "incidents", ["severity"])
    op.create_index("ix_incidents_status", "incidents", ["status"])
    op.create_index("ix_incidents_lat_lon", "incidents", ["latitude", "longitude"])
    op.create_index("ix_incidents_type_status", "incidents", ["disaster_type", "status"])

    # 2. Shelters (created before response_teams & resources due to foreign keys)
    op.create_table(
        "shelters",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("shelter_type", sa.String(length=50), nullable=False),
        sa.Column("capacity", sa.Integer(), nullable=False),
        sa.Column("current_occupancy", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("address", sa.Text(), nullable=False),
        sa.Column("contact_person", sa.String(length=100), nullable=False),
        sa.Column("contact_phone", sa.String(length=50), nullable=False),
        sa.Column("supplies_status", sa.String(length=30), nullable=False, server_default="adequate"),
        sa.Column("power_backup", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("medical_station", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="open"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_shelters_name", "shelters", ["name"])
    op.create_index("ix_shelters_status", "shelters", ["status"])

    # 3. Incident Updates
    op.create_table(
        "incident_updates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("author_name", sa.String(length=100), nullable=False),
        sa.Column("author_role", sa.String(length=100), nullable=False),
        sa.Column("update_type", sa.String(length=50), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("verified", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_incident_updates_incident_id", "incident_updates", ["incident_id"])
    op.create_index("ix_incident_updates_created_at", "incident_updates", ["created_at"])

    # 4. Alerts
    op.create_table(
        "alerts",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("alert_code", sa.String(length=50), nullable=False),
        sa.Column("headline", sa.String(length=255), nullable=False),
        sa.Column("urgency", sa.String(length=20), nullable=False),
        sa.Column("severity", sa.String(length=20), nullable=False),
        sa.Column("certainty", sa.String(length=20), nullable=False),
        sa.Column("target_region", sa.String(length=255), nullable=False),
        sa.Column("evacuation_recommended", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("instructions", sa.Text(), nullable=False),
        sa.Column("broadcast_status", sa.String(length=20), nullable=False, server_default="active"),
        sa.Column("issued_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.CheckConstraint("broadcast_status IN ('active', 'expired', 'cancelled', 'draft')", name="ck_alert_status"),
    )
    op.create_index("ix_alerts_alert_code", "alerts", ["alert_code"], unique=True)
    op.create_index("ix_alerts_incident_id", "alerts", ["incident_id"])
    op.create_index("ix_alerts_severity", "alerts", ["severity"])
    op.create_index("ix_alerts_status", "alerts", ["broadcast_status"])

    # 5. Response Teams
    op.create_table(
        "response_teams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("team_callsign", sa.String(length=100), nullable=False),
        sa.Column("unit_type", sa.String(length=50), nullable=False),
        sa.Column("personnel_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("commander_name", sa.String(length=100), nullable=False),
        sa.Column("contact_channel", sa.String(length=100), nullable=False),
        sa.Column("current_status", sa.String(length=30), nullable=False, server_default="standby"),
        sa.Column("current_latitude", sa.Float(), nullable=True),
        sa.Column("current_longitude", sa.Float(), nullable=True),
        sa.Column("base_location", sa.String(length=255), nullable=False),
        sa.Column("assigned_base_shelter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_response_teams_callsign", "response_teams", ["team_callsign"], unique=True)
    op.create_index("ix_response_teams_unit_type", "response_teams", ["unit_type"])
    op.create_index("ix_response_teams_status", "response_teams", ["current_status"])

    # 6. Response Tasks
    op.create_table(
        "response_tasks",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="CASCADE"), nullable=False),
        sa.Column("assigned_team_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("response_teams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=False),
        sa.Column("priority", sa.String(length=20), nullable=False, server_default="high"),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="pending"),
        sa.Column("target_latitude", sa.Float(), nullable=True),
        sa.Column("target_longitude", sa.Float(), nullable=True),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_response_tasks_incident_id", "response_tasks", ["incident_id"])
    op.create_index("ix_response_tasks_assigned_team_id", "response_tasks", ["assigned_team_id"])
    op.create_index("ix_response_tasks_priority", "response_tasks", ["priority"])
    op.create_index("ix_response_tasks_status", "response_tasks", ["status"])

    # 7. Resources
    op.create_table(
        "resources",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_code", sa.String(length=50), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("category", sa.String(length=50), nullable=False),
        sa.Column("quantity_total", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("quantity_available", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("unit", sa.String(length=50), nullable=False),
        sa.Column("shelter_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("shelters.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resources_code", "resources", ["resource_code"], unique=True)
    op.create_index("ix_resources_category", "resources", ["category"])
    op.create_index("ix_resources_shelter_id", "resources", ["shelter_id"])

    # 8. Resource Movements
    op.create_table(
        "resource_movements",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("resource_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("resources.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_location", sa.String(length=255), nullable=False),
        sa.Column("destination_location", sa.String(length=255), nullable=False),
        sa.Column("quantity", sa.Float(), nullable=False),
        sa.Column("status", sa.String(length=30), nullable=False, server_default="dispatched"),
        sa.Column("transport_mode", sa.String(length=50), nullable=False),
        sa.Column("dispatched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("delivered_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_resource_movements_resource_id", "resource_movements", ["resource_id"])
    op.create_index("ix_resource_movements_status", "resource_movements", ["status"])

    # 9. Environmental Observations
    op.create_table(
        "environmental_observations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("station_id", sa.String(length=100), nullable=False),
        sa.Column("station_name", sa.String(length=255), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("metric_type", sa.String(length=50), nullable=False),
        sa.Column("value", sa.Float(), nullable=False),
        sa.Column("unit", sa.String(length=30), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False, server_default="nominal"),
        sa.Column("recorded_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_env_obs_station_id", "environmental_observations", ["station_id"])
    op.create_index("ix_env_obs_metric_type", "environmental_observations", ["metric_type"])
    op.create_index("ix_env_obs_status", "environmental_observations", ["status"])
    op.create_index("ix_env_obs_recorded_at", "environmental_observations", ["recorded_at"])

    # 10. Risk Assessments
    op.create_table(
        "risk_assessments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("incident_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("target_area", sa.String(length=255), nullable=False),
        sa.Column("hazard_type", sa.String(length=50), nullable=False),
        sa.Column("calculated_risk_score", sa.Float(), nullable=False),
        sa.Column("risk_level", sa.String(length=20), nullable=False),
        sa.Column("simulated_factors", sa.Text(), nullable=True),
        sa.Column("recommended_interventions", sa.Text(), nullable=False),
        sa.Column("assessed_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_risk_assessments_incident_id", "risk_assessments", ["incident_id"])
    op.create_index("ix_risk_assessments_risk_level", "risk_assessments", ["risk_level"])

    # 11. Audit Logs
    op.create_table(
        "audit_logs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("actor_id", sa.String(length=100), nullable=False),
        sa.Column("actor_role", sa.String(length=100), nullable=False),
        sa.Column("action", sa.String(length=100), nullable=False),
        sa.Column("entity_type", sa.String(length=50), nullable=False),
        sa.Column("entity_id", sa.String(length=100), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("ip_address", sa.String(length=50), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_audit_logs_actor_id", "audit_logs", ["actor_id"])
    op.create_index("ix_audit_logs_action", "audit_logs", ["action"])
    op.create_index("ix_audit_logs_created_at", "audit_logs", ["created_at"])


def downgrade() -> None:
    op.drop_table("audit_logs")
    op.drop_table("risk_assessments")
    op.drop_table("environmental_observations")
    op.drop_table("resource_movements")
    op.drop_table("resources")
    op.drop_table("response_tasks")
    op.drop_table("response_teams")
    op.drop_table("alerts")
    op.drop_table("incident_updates")
    op.drop_table("shelters")
    op.drop_table("incidents")
