"""UC04b: partial unique indexes for category name uniqueness

The existing uq_categories_user_name constraint uses (user_id, name) but
PostgreSQL treats NULLs as distinct, so it cannot prevent two system
categories with the same name.  Replace with two partial unique indexes:
  - uq_categories_system_name   WHERE user_id IS NULL   (unique by name alone)
  - uq_categories_user_name_v2  WHERE user_id IS NOT NULL (unique per user+name)

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-03

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a7b8c9d0"
down_revision: Union[str, Sequence[str], None] = "d4e5f6a7b8c9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_constraint("uq_categories_user_name", "categories", type_="unique")

    op.execute(
        "CREATE UNIQUE INDEX uq_categories_system_name "
        "ON categories (name) WHERE user_id IS NULL"
    )
    op.execute(
        "CREATE UNIQUE INDEX uq_categories_user_name_v2 "
        "ON categories (user_id, name) WHERE user_id IS NOT NULL"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS uq_categories_user_name_v2")
    op.execute("DROP INDEX IF EXISTS uq_categories_system_name")

    op.create_unique_constraint("uq_categories_user_name", "categories", ["user_id", "name"])
