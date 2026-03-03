from typing import List

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.account import InstitutionRead
from app.services import account_service

router = APIRouter(redirect_slashes=False)


class InstitutionCreate(BaseModel):
    name: str


@router.get("", response_model=List[InstitutionRead])
async def list_institutions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all institutions (auth required for consistency)."""
    return await account_service.list_institutions(db)


@router.post("", response_model=InstitutionRead, status_code=status.HTTP_201_CREATED)
async def create_institution(
    payload: InstitutionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create an institution. Returns 400 if name already exists."""
    return await account_service.create_institution(db, payload.name)
