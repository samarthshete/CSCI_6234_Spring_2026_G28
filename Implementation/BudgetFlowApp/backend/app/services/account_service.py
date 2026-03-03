"""Account service: CRUD for institutions and financial accounts with user isolation."""

import uuid
from datetime import datetime, timezone
from typing import List, Union

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import (
    Institution,
    FinancialAccount,
    BankAccount,
    CreditCardAccount,
    InvestmentAccount,
)
from app.schemas.account import (
    BankAccountCreate,
    CreditCardAccountCreate,
    InvestmentAccountCreate,
    AccountUpdate,
)


async def list_accounts(db: AsyncSession, user_id: uuid.UUID) -> List[FinancialAccount]:
    """List all financial accounts owned by the user."""
    result = await db.execute(
        select(FinancialAccount).where(FinancialAccount.user_id == user_id)
    )
    return list(result.scalars().all())


async def get_account(
    db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID
) -> FinancialAccount:
    """Get one account by id; must belong to user. Raises 404 if not found or not owned."""
    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Account not found.",
        )
    return account


async def create_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    payload: Union[BankAccountCreate, CreditCardAccountCreate, InvestmentAccountCreate],
) -> FinancialAccount:
    """Create a new financial account for the user."""
    data = payload.model_dump(exclude_unset=True)
    if payload.type == "bank":
        account = BankAccount(**data, user_id=user_id)
    elif payload.type == "credit":
        account = CreditCardAccount(**data, user_id=user_id)
    elif payload.type == "investment":
        account = InvestmentAccount(**data, user_id=user_id)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid account type. Must be bank, credit, or investment.",
        )
    db.add(account)
    await db.commit()
    await db.refresh(account)
    return account


async def update_account(
    db: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    payload: AccountUpdate,
) -> FinancialAccount:
    """Update an account; must belong to user. Raises 404 if not found or not owned."""
    account = await get_account(db, user_id, account_id)
    update_data = payload.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(account, key, value)
    account.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(account)
    return account


async def delete_account(
    db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID
) -> None:
    """Delete an account; must belong to user. Raises 404 if not found or not owned."""
    account = await get_account(db, user_id, account_id)
    await db.delete(account)
    await db.commit()


async def list_institutions(db: AsyncSession) -> List[Institution]:
    """List all institutions (global, no user filter)."""
    result = await db.execute(select(Institution))
    return list(result.scalars().all())


async def create_institution(db: AsyncSession, name: str) -> Institution:
    """Create an institution. Raises 400 if name already exists."""
    existing = await db.execute(select(Institution).where(Institution.name == name))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An institution with this name already exists.",
        )
    institution = Institution(name=name)
    db.add(institution)
    await db.commit()
    await db.refresh(institution)
    return institution
