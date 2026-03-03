from typing import List
import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.account import AccountRead, AccountUpdate, AccountCreate
from app.services import account_service

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=List[AccountRead])
async def list_accounts(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all accounts belonging to the current user."""
    return await account_service.list_accounts(db, current_user.id)


@router.post("", response_model=AccountRead, status_code=status.HTTP_201_CREATED)
async def create_account(
    payload: AccountCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new financial account for the current user."""
    return await account_service.create_account(db, current_user.id, payload)


@router.get("/{account_id}", response_model=AccountRead)
async def get_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get one account by id. Returns 404 if not found or not owned by user."""
    return await account_service.get_account(db, current_user.id, account_id)


@router.patch("/{account_id}", response_model=AccountRead)
async def update_account(
    account_id: uuid.UUID,
    payload: AccountUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Update an account. Returns 404 if not found or not owned by user."""
    return await account_service.update_account(db, current_user.id, account_id, payload)


@router.delete("/{account_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    account_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete an account. Returns 404 if not found or not owned by user."""
    await account_service.delete_account(db, current_user.id, account_id)
