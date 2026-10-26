"""phase2_incident_management

Revision ID: 0002_phase2_incidents
Revises: 0001_initial
Create Date: 2026-10-25 14:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0002_phase2_incidents"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update incidents table columns
    with op.batch_alter_table("incidents") as batch_op:
        # Add new Phase 2 columns if not present
        batch_op.add_column(sa.Column("category", sa.String(length=50), nullable=True, server_default="other"))
        batch_op.add_column(sa.Column("location_description", sa.String(length=255), nullable=True))
        batch_op.add_column(sa.Column("source_type", sa.String(length=50), nullable=False, server_default="operator_report"))
        batch_op.add_column(sa.Column("verification_status", sa.String(length=30), nullable=False, server_default="unverified"))
        batch_op.add_column(sa.Column("created_by", sa.String(length=100), nullable=False, server_default="system"))
        batch_op.add_column(sa.Column("assigned_commander", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("affected_population", sa.Integer(), nullable=True, server_default="0"))
        batch_op.alter_column("disaster_type", nullable=True)
        batch_op.alter_column("location_name", nullable=True)
        batch_op.alter_column("affected_region", nullable=True)
        batch_op.alter_column("latitude", nullable=True)
        batch_op.alter_column("longitude", nullable=True)

        # Create indexes
        batch_op.create_index("ix_incidents_category", ["category"])
        batch_op.create_index("ix_incidents_source_type", ["source_type"])
        batch_op.create_index("ix_incidents_verification_status", ["verification_status"])

    # 2. Update incident_updates table columns
    with op.batch_alter_table("incident_updates") as batch_op:
        batch_op.add_column(sa.Column("actor_id", sa.String(length=100), nullable=True, server_default="system"))
        batch_op.add_column(sa.Column("previous_status", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("new_status", sa.String(length=30), nullable=True))
        batch_op.add_column(sa.Column("metadata_payload", sa.Text(), nullable=True))
        batch_op.alter_column("author_name", nullable=True)
        batch_op.alter_column("author_role", nullable=True)

        batch_op.create_index("ix_incident_updates_actor_id", ["actor_id"])
        batch_op.create_index("ix_incident_updates_update_type", ["update_type"])


def downgrade() -> None:
    with op.batch_alter_table("incident_updates") as batch_op:
        batch_op.drop_index("ix_incident_updates_update_type")
        batch_op.drop_index("ix_incident_updates_actor_id")
        batch_op.drop_column("metadata_payload")
        batch_op.drop_column("new_status")
        batch_op.drop_column("previous_status")
        batch_op.drop_column("actor_id")

    with op.batch_alter_table("incidents") as batch_op:
        batch_op.drop_index("ix_incidents_verification_status")
        batch_op.drop_index("ix_incidents_source_type")
        batch_op.drop_index("ix_incidents_category")
        batch_op.drop_column("affected_population")
        batch_op.drop_column("assigned_commander")
        batch_op.drop_column("created_by")
        batch_op.drop_column("verification_status")
        batch_op.drop_column("source_type")
        batch_op.drop_column("location_description")
        batch_op.drop_column("category")
