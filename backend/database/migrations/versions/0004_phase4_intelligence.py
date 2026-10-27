"""phase4_intelligence

Revision ID: 0004_phase4_intelligence
Revises: 0003_phase3_coordination
Create Date: 2026-10-27 10:55:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "0004_phase4_intelligence"
down_revision: Union[str, None] = "0003_phase3_coordination"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Update alerts table with lifecycle and deduplication fields and expand status check constraint
    with op.batch_alter_table(
        "alerts",
        recreate="always",
        table_args=(
            sa.CheckConstraint(
                "broadcast_status IN ('active', 'acknowledged', 'resolved', 'expired', 'cancelled', 'draft')",
                name="ck_alert_status",
            ),
        ),
    ) as batch_op:
        batch_op.drop_constraint("ck_alert_status", type_="check")
        batch_op.add_column(sa.Column("acknowledged_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("acknowledged_by", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("resolved_at", sa.DateTime(timezone=True), nullable=True))
        batch_op.add_column(sa.Column("resolved_by", sa.String(length=100), nullable=True))
        batch_op.add_column(sa.Column("trigger_reason", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("source_type", sa.String(length=50), nullable=False, server_default="risk_engine"))
        batch_op.add_column(sa.Column("dedup_key", sa.String(length=120), nullable=True))
        batch_op.create_index("ix_alerts_dedup_key", ["dedup_key"])

    # 2. Update risk_assessments table
    with op.batch_alter_table("risk_assessments") as batch_op:
        batch_op.add_column(sa.Column("data_sources", sa.Text(), nullable=True))
        batch_op.add_column(sa.Column("confidence_score", sa.Float(), nullable=False, server_default="1.0"))

    # 3. Create disaster_simulations table
    op.create_table(
        "disaster_simulations",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("scenario_name", sa.String(length=100), nullable=False),
        sa.Column("scenario_type", sa.String(length=50), nullable=False),
        sa.Column("input_parameters", sa.Text(), nullable=False),
        sa.Column("results_summary", sa.Text(), nullable=False),
        sa.Column("created_by", sa.String(length=100), nullable=False, server_default="operator"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_disaster_simulations_scenario_type", "disaster_simulations", ["scenario_type"])
    op.create_index("ix_disaster_simulations_created_at", "disaster_simulations", ["created_at"])

    # 4. Create ai_analysis_records table
    op.create_table(
        "ai_analysis_records",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("incident_id", sa.Uuid(), sa.ForeignKey("incidents.id", ondelete="SET NULL"), nullable=True),
        sa.Column("query_type", sa.String(length=50), nullable=False),
        sa.Column("provider", sa.String(length=50), nullable=False),
        sa.Column("model_name", sa.String(length=100), nullable=False),
        sa.Column("prompt_summary", sa.Text(), nullable=True),
        sa.Column("response_content", sa.Text(), nullable=False),
        sa.Column("structured_payload", sa.Text(), nullable=True),
        sa.Column("tools_used", sa.Text(), nullable=True),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=False, server_default=sa.text("1")),
        sa.Column("approval_status", sa.String(length=30), nullable=False, server_default="pending"),
        sa.Column("approved_by", sa.String(length=100), nullable=True),
        sa.Column("approved_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_ai_analysis_records_incident_id", "ai_analysis_records", ["incident_id"])
    op.create_index("ix_ai_analysis_records_query_type", "ai_analysis_records", ["query_type"])
    op.create_index("ix_ai_analysis_records_approval_status", "ai_analysis_records", ["approval_status"])
    op.create_index("ix_ai_analysis_records_created_at", "ai_analysis_records", ["created_at"])


def downgrade() -> None:
    op.drop_table("ai_analysis_records")
    op.drop_table("disaster_simulations")

    with op.batch_alter_table("risk_assessments") as batch_op:
        batch_op.drop_column("confidence_score")
        batch_op.drop_column("data_sources")

    with op.batch_alter_table("alerts") as batch_op:
        batch_op.drop_index("ix_alerts_dedup_key")
        batch_op.drop_column("dedup_key")
        batch_op.drop_column("source_type")
        batch_op.drop_column("trigger_reason")
        batch_op.drop_column("resolved_by")
        batch_op.drop_column("resolved_at")
        batch_op.drop_column("acknowledged_by")
        batch_op.drop_column("acknowledged_at")
