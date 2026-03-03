"""UC02 schema: name, balance, is_active, timestamps, column renames

Revision ID: a1b2c3d4e5f6
Revises: 0dd224777185
Create Date: 2026-03-02

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "0dd224777185"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # institutions: add created_at
    op.add_column(
        "institutions",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )

    # financial_accounts: add new columns
    op.add_column(
        "financial_accounts",
        sa.Column("balance", sa.Numeric(15, 2), server_default="0", nullable=False),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("is_active", sa.Boolean(), server_default="true", nullable=False),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("bank_account_number_last4", sa.String(4), nullable=True),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("credit_card_last4", sa.String(4), nullable=True),
    )
    # Copy data from old columns to new, then drop old and rename (or rename in place)
    op.execute("UPDATE financial_accounts SET bank_account_number_last4 = routing_number_last4")
    op.execute("UPDATE financial_accounts SET credit_card_last4 = card_last4")
    op.drop_column("financial_accounts", "routing_number_last4")
    op.drop_column("financial_accounts", "card_last4")
    op.execute("ALTER TABLE financial_accounts RENAME COLUMN nickname TO name")
    # Ensure name and currency allow new lengths/defaults if needed
    op.alter_column(
        "financial_accounts",
        "name",
        existing_type=sa.String(),
        type_=sa.String(255),
        existing_nullable=False,
    )
    op.alter_column(
        "financial_accounts",
        "currency",
        existing_type=sa.String(3),
        server_default="USD",
    )
    op.create_index(
        op.f("ix_financial_accounts_institution_id"),
        "financial_accounts",
        ["institution_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_financial_accounts_institution_id"), table_name="financial_accounts")
    op.execute("ALTER TABLE financial_accounts RENAME COLUMN name TO nickname")
    op.add_column(
        "financial_accounts",
        sa.Column("routing_number_last4", sa.String(4), nullable=True),
    )
    op.add_column(
        "financial_accounts",
        sa.Column("card_last4", sa.String(4), nullable=True),
    )
    op.execute("UPDATE financial_accounts SET routing_number_last4 = bank_account_number_last4")
    op.execute("UPDATE financial_accounts SET card_last4 = credit_card_last4")
    op.drop_column("financial_accounts", "bank_account_number_last4")
    op.drop_column("financial_accounts", "credit_card_last4")
    op.drop_column("financial_accounts", "updated_at")
    op.drop_column("financial_accounts", "created_at")
    op.drop_column("financial_accounts", "is_active")
    op.drop_column("financial_accounts", "balance")
    op.drop_column("institutions", "created_at")
