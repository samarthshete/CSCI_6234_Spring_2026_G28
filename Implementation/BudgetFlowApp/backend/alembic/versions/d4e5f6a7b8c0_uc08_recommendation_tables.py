"""UC08: risk_profiles, recommendation_runs, recommendation_items

Revision ID: d4e5f6a7b8c0
Revises: c3d4e5f6a7b9
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "d4e5f6a7b8c0"
down_revision: Union[str, None] = "c3d4e5f6a7b9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "risk_profiles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True),
        sa.Column("score", sa.Integer, nullable=False, server_default="50"),
        sa.Column("horizon_months", sa.Integer, nullable=False, server_default="60"),
        sa.Column("liquidity_need", sa.String(20), nullable=False, server_default="moderate"),
        sa.Column("answers_json", postgresql.JSONB, nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_risk_profiles_user_id", "risk_profiles", ["user_id"], unique=True)

    op.create_table(
        "recommendation_runs",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="completed"),
        sa.Column("inputs_snapshot", postgresql.JSONB, nullable=True),
        sa.Column("outputs", postgresql.JSONB, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("ix_rec_runs_user_created", "recommendation_runs", ["user_id", "created_at"])

    op.create_table(
        "recommendation_items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("run_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("recommendation_runs.id", ondelete="CASCADE"), nullable=False),
        sa.Column("priority", sa.Integer, nullable=False),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("details", postgresql.JSONB, nullable=True),
        sa.Column("confidence", sa.Numeric(4, 3), nullable=False, server_default="0.800"),
    )
    op.create_index("ix_rec_items_run_id", "recommendation_items", ["run_id"])


def downgrade() -> None:
    op.drop_index("ix_rec_items_run_id", table_name="recommendation_items")
    op.drop_table("recommendation_items")
    op.drop_index("ix_rec_runs_user_created", table_name="recommendation_runs")
    op.drop_table("recommendation_runs")
    op.drop_index("ix_risk_profiles_user_id", table_name="risk_profiles")
    op.drop_table("risk_profiles")
