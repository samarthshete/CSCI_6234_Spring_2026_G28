"""UC06: budget_alerts table

Revision ID: a1b2c3d4e5f7
Revises: f6a7b8c9d0e1
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f7"
down_revision: Union[str, Sequence[str], None] = "f6a7b8c9d0e1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budget_alerts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=True),
        sa.Column("category_id", sa.UUID(), nullable=True),
        sa.Column("threshold_percent", sa.Numeric(4, 3), nullable=False),
        sa.Column("spent_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("limit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "budget_id", "category_id", "threshold_percent", "period_start",
            name="uq_budget_alerts_budget_cat_thresh_period",
        ),
    )
    op.create_index("ix_budget_alerts_user_id", "budget_alerts", ["user_id"])
    op.create_index("ix_budget_alerts_budget_id", "budget_alerts", ["budget_id"])
    op.create_index("ix_budget_alerts_category_id", "budget_alerts", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_budget_alerts_category_id", table_name="budget_alerts")
    op.drop_index("ix_budget_alerts_budget_id", table_name="budget_alerts")
    op.drop_index("ix_budget_alerts_user_id", table_name="budget_alerts")
    op.drop_table("budget_alerts")
