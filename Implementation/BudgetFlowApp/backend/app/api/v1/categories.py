import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.category import CategoryCreate, CategoryUpdate, CategoryRead, CategorizeRequest
from app.schemas.transaction import TransactionRead
from app.services import categorization_service

router = APIRouter(redirect_slashes=False)


# ---------------------------------------------------------------------------
# Categories CRUD
# ---------------------------------------------------------------------------

@router.get("", response_model=List[CategoryRead])
async def list_categories(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cats = await categorization_service.list_categories(db, current_user.id)
    return cats


@router.post("", response_model=CategoryRead, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = await categorization_service.create_category(db, current_user.id, payload.model_dump())
    return cat


@router.patch("/{category_id}", response_model=CategoryRead)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = await categorization_service.update_category(
        db, current_user.id, category_id, payload.model_dump(exclude_unset=True),
    )
    return cat
