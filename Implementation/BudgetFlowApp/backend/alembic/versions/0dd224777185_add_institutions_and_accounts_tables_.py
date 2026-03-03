"""Add Institutions and Accounts tables UC02

Revision ID: 0dd224777185
Revises: ca29e518b024
Create Date: 2026-03-02 16:13:44.218732

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "0dd224777185"
down_revision: Union[str, Sequence[str], None] = "ca29e518b024"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "institutions",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_institutions_name"), "institutions", ["name"], unique=True)

    op.create_table(
        "financial_accounts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("institution_id", sa.UUID(), nullable=True),
        sa.Column("type", sa.String(length=50), nullable=False),
        sa.Column("nickname", sa.String(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("routing_number_last4", sa.String(length=4), nullable=True),
        sa.Column("card_last4", sa.String(length=4), nullable=True),
        sa.Column("credit_limit", sa.Float(), nullable=True),
        sa.Column("broker_name", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["institution_id"], ["institutions.id"], ondelete="SET NULL"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_financial_accounts_user_id"), "financial_accounts", ["user_id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_accounts_user_id"), table_name="financial_accounts")
    op.drop_table("financial_accounts")
    op.drop_index(op.f("ix_institutions_name"), table_name="institutions")
    op.drop_table("institutions")
