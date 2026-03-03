"""UC04: categories table + transaction categorization columns

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB


revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, Sequence[str], None] = "c3d4e5f6a7b8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "categories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("type", sa.String(20), nullable=False, server_default="expense"),
        sa.Column("rules", JSONB(), nullable=False, server_default=sa.text("'[]'::jsonb")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "name", name="uq_categories_user_name"),
    )
    op.create_index("ix_categories_user_id", "categories", ["user_id"])
    op.create_index("ix_categories_name", "categories", ["name"])

    # Add categorization columns to transactions
    op.add_column("transactions", sa.Column("category_confidence", sa.Numeric(4, 3), nullable=True))
    op.add_column("transactions", sa.Column("categorization_source", sa.String(20), nullable=True))
    op.add_column("transactions", sa.Column("needs_manual", sa.Boolean(), nullable=False, server_default="false"))

    # Add FK from transactions.category_id -> categories.id (column already exists as plain UUID)
    op.create_foreign_key(
        "fk_transactions_category_id",
        "transactions", "categories",
        ["category_id"], ["id"],
        ondelete="SET NULL",
    )
    op.create_index("ix_transactions_category_id", "transactions", ["category_id"])


def downgrade() -> None:
    op.drop_index("ix_transactions_category_id", table_name="transactions")
    op.drop_constraint("fk_transactions_category_id", "transactions", type_="foreignkey")
    op.drop_column("transactions", "needs_manual")
    op.drop_column("transactions", "categorization_source")
    op.drop_column("transactions", "category_confidence")
    op.drop_index("ix_categories_name", table_name="categories")
    op.drop_index("ix_categories_user_id", table_name="categories")
    op.drop_table("categories")
