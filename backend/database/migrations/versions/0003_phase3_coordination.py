"""phase3_coordination
Adds fields and index enhancements for ResponseTeam, Shelter, Resource, and ResourceMovement

Revision ID: 0003_phase3_coordination
Revises: 0002_phase2_incidents
Create Date: 2026-10-26 18:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0003_phase3_coordination"
down_revision: Union[str, None] = "0002_phase2_incidents"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update shelters table (allow nullable coordinates)
    with op.batch_alter_table("shelters") as batch_op:
        batch_op.alter_column("latitude", nullable=True)
        batch_op.alter_column("longitude", nullable=True)

    # 2. Update response_teams table
    with op.batch_alter_table("response_teams") as batch_op:
        batch_op.add_column(
            sa.Column(
                "assigned_incident_id",
                sa.Uuid(),
                sa.ForeignKey("incidents.id", ondelete="SET NULL", name="fk_response_teams_incident"),
                nullable=True,
            )
        )
        batch_op.create_index("ix_response_teams_assigned_incident_id", ["assigned_incident_id"])

    # 3. Update resources table
    with op.batch_alter_table("resources") as batch_op:
        batch_op.add_column(
            sa.Column(
                "storage_location",
                sa.String(length=255),
                nullable=True,
                server_default="Central Logistics Warehouse",
            )
        )
        batch_op.add_column(
            sa.Column(
                "status",
                sa.String(length=30),
                nullable=False,
                server_default="in_stock",
            )
        )
        batch_op.create_index("ix_resources_status", ["status"])

    # 4. Update resource_movements table
    with op.batch_alter_table("resource_movements") as batch_op:
        batch_op.add_column(
            sa.Column(
                "incident_id",
                sa.Uuid(),
                sa.ForeignKey("incidents.id", ondelete="SET NULL", name="fk_resmov_incident"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "task_id",
                sa.Uuid(),
                sa.ForeignKey("response_tasks.id", ondelete="SET NULL", name="fk_resmov_task"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "team_id",
                sa.Uuid(),
                sa.ForeignKey("response_teams.id", ondelete="SET NULL", name="fk_resmov_team"),
                nullable=True,
            )
        )
        batch_op.add_column(
            sa.Column(
                "shelter_id",
                sa.Uuid(),
                sa.ForeignKey("shelters.id", ondelete="SET NULL", name="fk_resmov_shelter"),
                nullable=True,
            )
        )
        batch_op.add_column(sa.Column("notes", sa.Text(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table("resource_movements") as batch_op:
        batch_op.drop_column("notes")
        batch_op.drop_column("shelter_id")
        batch_op.drop_column("team_id")
        batch_op.drop_column("task_id")
        batch_op.drop_column("incident_id")

    with op.batch_alter_table("resources") as batch_op:
        batch_op.drop_index("ix_resources_status")
        batch_op.drop_column("status")
        batch_op.drop_column("storage_location")

    with op.batch_alter_table("response_teams") as batch_op:
        batch_op.drop_index("ix_response_teams_assigned_incident_id")
        batch_op.drop_column("assigned_incident_id")

    with op.batch_alter_table("shelters") as batch_op:
        batch_op.alter_column("longitude", nullable=False)
        batch_op.alter_column("latitude", nullable=False)
