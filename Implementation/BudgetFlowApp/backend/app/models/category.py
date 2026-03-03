import uuid
from datetime import datetime
from typing import Optional

from sqlalchemy import String, ForeignKey, DateTime, Index
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.user import Base


class Category(Base):
    __tablename__ = "categories"
    __table_args__ = (
        # Partial unique indexes enforced at DB level via migration UC04b:
        #   uq_categories_system_name   ON (name)          WHERE user_id IS NULL
        #   uq_categories_user_name_v2  ON (user_id, name) WHERE user_id IS NOT NULL
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False, default="expense")
    rules: Mapped[list] = mapped_column(JSONB, nullable=False, server_default="'[]'::jsonb")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")
