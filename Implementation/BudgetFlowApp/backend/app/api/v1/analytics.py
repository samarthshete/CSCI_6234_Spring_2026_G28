import uuid
from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.analytics import SummaryResponse, TrendPoint, BudgetVsActualItem
from app.services import analytics_service

router = APIRouter(redirect_slashes=False)


def _parse_date(v: Optional[str]) -> Optional[date]:
    if v is None:
        return None
    return datetime.strptime(v, "%Y-%m-%d").date()


def _parse_uuid_list(v: Optional[str]) -> Optional[List[uuid.UUID]]:
    if not v:
        return None
    return [uuid.UUID(x.strip()) for x in v.split(",") if x.strip()]


@router.get("/summary", response_model=SummaryResponse)
async def get_summary(
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    account_ids: Optional[str] = Query(None, description="Comma-separated UUIDs"),
    category_ids: Optional[str] = Query(None, description="Comma-separated UUIDs"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await analytics_service.get_summary(
        db, current_user.id,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        account_ids=_parse_uuid_list(account_ids),
        category_ids=_parse_uuid_list(category_ids),
    )


@router.get("/trends", response_model=List[TrendPoint])
async def get_trends(
    date_from: str = Query(...),
    date_to: str = Query(...),
    group_by: str = Query("month", pattern=r"^(day|week|month)$"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await analytics_service.get_trends(
        db, current_user.id,
        date_from=_parse_date(date_from),
        date_to=_parse_date(date_to),
        group_by=group_by,
    )


@router.get("/budget-vs-actual", response_model=List[BudgetVsActualItem])
async def get_budget_vs_actual(
    budget_id: uuid.UUID = Query(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await analytics_service.get_budget_vs_actual(db, current_user.id, budget_id)
