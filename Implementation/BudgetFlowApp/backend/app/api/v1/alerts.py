import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.alert import AlertRead
from app.services import alert_service

router = APIRouter(redirect_slashes=False)


@router.get("", response_model=List[AlertRead])
async def list_alerts(
    is_read: Optional[bool] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await alert_service.list_alerts(db, current_user.id, is_read)


@router.patch("/{alert_id}/read", response_model=AlertRead)
async def mark_alert_read(
    alert_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await alert_service.mark_alert_read(db, current_user.id, alert_id)
