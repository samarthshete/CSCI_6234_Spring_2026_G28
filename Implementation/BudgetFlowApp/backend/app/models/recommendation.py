import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional, List

from sqlalchemy import String, ForeignKey, DateTime, Numeric, Integer, Index, Text
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.user import Base


class RiskProfile(Base):
    __tablename__ = "risk_profiles"
    __table_args__ = (
        Index("ix_risk_profiles_user_id", "user_id", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
    )
    score: Mapped[int] = mapped_column(Integer, nullable=False, default=50)
    horizon_months: Mapped[int] = mapped_column(Integer, nullable=False, default=60)
    liquidity_need: Mapped[str] = mapped_column(String(20), nullable=False, default="moderate")
    answers_json: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")


class RecommendationRun(Base):
    __tablename__ = "recommendation_runs"
    __table_args__ = (
        Index("ix_rec_runs_user_created", "user_id", "created_at"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
    )
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="completed")
    inputs_snapshot: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    outputs: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, server_default="now()")

    items: Mapped[List["RecommendationItem"]] = relationship(
        "RecommendationItem", back_populates="run",
        cascade="all, delete-orphan", passive_deletes=True, lazy="selectin",
        order_by="RecommendationItem.priority",
    )


class RecommendationItem(Base):
    __tablename__ = "recommendation_items"
    __table_args__ = (
        Index("ix_rec_items_run_id", "run_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    run_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("recommendation_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    priority: Mapped[int] = mapped_column(Integer, nullable=False)
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    details: Mapped[Optional[dict]] = mapped_column(JSONB, nullable=True)
    confidence: Mapped[Decimal] = mapped_column(Numeric(4, 3), nullable=False, default=Decimal("0.8"))

    run: Mapped["RecommendationRun"] = relationship("RecommendationRun", back_populates="items")
