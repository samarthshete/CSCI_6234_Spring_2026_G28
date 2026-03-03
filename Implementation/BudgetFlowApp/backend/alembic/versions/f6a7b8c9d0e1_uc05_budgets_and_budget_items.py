"""UC05: budgets and budget_items tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "f6a7b8c9d0e1"
down_revision: Union[str, Sequence[str], None] = "e5f6a7b8c9d0"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "budgets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("period_start", sa.Date(), nullable=False),
        sa.Column("period_end", sa.Date(), nullable=False),
        sa.Column("period_type", sa.String(20), nullable=False, server_default="monthly"),
        sa.Column("thresholds", JSONB(), nullable=False, server_default=sa.text("'[0.8, 0.9, 1.0]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("period_end >= period_start", name="ck_budgets_period_range"),
    )
    op.create_index("ix_budgets_user_id", "budgets", ["user_id"])
    op.create_index("ix_budgets_period_start", "budgets", ["period_start"])
    op.create_index("ix_budgets_period_end", "budgets", ["period_end"])

    op.create_table(
        "budget_items",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("budget_id", sa.UUID(), nullable=False),
        sa.Column("category_id", sa.UUID(), nullable=False),
        sa.Column("limit_amount", sa.Numeric(14, 2), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["budget_id"], ["budgets.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["category_id"], ["categories.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("budget_id", "category_id", name="uq_budget_items_budget_category"),
        sa.CheckConstraint("limit_amount > 0", name="ck_budget_items_positive_limit"),
    )
    op.create_index("ix_budget_items_budget_id", "budget_items", ["budget_id"])
    op.create_index("ix_budget_items_category_id", "budget_items", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_budget_items_category_id", table_name="budget_items")
    op.drop_index("ix_budget_items_budget_id", table_name="budget_items")
    op.drop_table("budget_items")
    op.drop_index("ix_budgets_period_end", table_name="budgets")
    op.drop_index("ix_budgets_period_start", table_name="budgets")
    op.drop_index("ix_budgets_user_id", table_name="budgets")
    op.drop_table("budgets")
