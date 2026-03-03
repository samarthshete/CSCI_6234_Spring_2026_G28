"""UC02 cleanup: drop nickname column if it still exists (idempotent safety)

Revision ID: b7f8e9a0c1d2
Revises: a1b2c3d4e5f6
Create Date: 2026-03-02

Migration a1b2c3d4e5f6 renames nickname -> name, but if the DB was
bootstrapped with partial migration history or manual DDL, nickname
may linger alongside name.  This migration makes the final state
deterministic:
  - If nickname exists and name does NOT exist: rename nickname -> name.
  - If both exist: backfill name from nickname where name IS NULL, then drop nickname.
  - If only name exists: no-op.
"""
from typing import Sequence, Union

from alembic import op
from sqlalchemy import inspect, text


revision: str = "b7f8e9a0c1d2"
down_revision: Union[str, Sequence[str], None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def _column_exists(connection, table: str, column: str) -> bool:
    insp = inspect(connection)
    cols = {c["name"] for c in insp.get_columns(table)}
    return column in cols


def upgrade() -> None:
    conn = op.get_bind()
    has_nickname = _column_exists(conn, "financial_accounts", "nickname")
    has_name = _column_exists(conn, "financial_accounts", "name")

    if has_nickname and not has_name:
        conn.execute(text("ALTER TABLE financial_accounts RENAME COLUMN nickname TO name"))
    elif has_nickname and has_name:
        conn.execute(text("UPDATE financial_accounts SET name = nickname WHERE name IS NULL"))
        op.drop_column("financial_accounts", "nickname")


def downgrade() -> None:
    pass
