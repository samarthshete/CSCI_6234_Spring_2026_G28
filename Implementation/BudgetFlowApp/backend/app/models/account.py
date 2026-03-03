import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional

from sqlalchemy import String, ForeignKey, Float, Boolean, DateTime, Numeric
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID

from app.models.user import Base


class Institution(Base):
    """Global shared entity; not user-owned."""
    __tablename__ = "institutions"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    name: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )


class FinancialAccount(Base):
    """
    Polymorphic base for user-owned financial accounts.
    Single Table Inheritance (STI) with discriminator column `type`.
    """
    __tablename__ = "financial_accounts"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    institution_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("institutions.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )
    institution: Mapped[Optional["Institution"]] = relationship("Institution", lazy="selectin")
    type: Mapped[str] = mapped_column(String(50), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    currency: Mapped[str] = mapped_column(String(3), nullable=False, default="USD")
    balance: Mapped[Decimal] = mapped_column(
        Numeric(15, 2), nullable=False, default=0
    )
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default="now()"
    )

    # Subtype-specific columns (nullable for STI)
    bank_account_number_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    credit_card_last4: Mapped[Optional[str]] = mapped_column(String(4), nullable=True)
    credit_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    broker_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)

    __mapper_args__ = {
        "polymorphic_identity": "financial_account",
        "polymorphic_on": "type",
    }


class BankAccount(FinancialAccount):
    __mapper_args__ = {"polymorphic_identity": "bank"}


class CreditCardAccount(FinancialAccount):
    __mapper_args__ = {"polymorphic_identity": "credit"}


class InvestmentAccount(FinancialAccount):
    __mapper_args__ = {"polymorphic_identity": "investment"}
