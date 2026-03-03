import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, or_, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.budget import Budget, BudgetItem
from app.models.category import Category


async def _validate_category_ids(
    db: AsyncSession, user_id: uuid.UUID, category_ids: List[uuid.UUID],
) -> None:
    """Every referenced category must be system-owned (user_id NULL) or owned by current user."""
    if not category_ids:
        return
    result = await db.execute(
        select(Category.id).where(
            Category.id.in_(category_ids),
            or_(Category.user_id == user_id, Category.user_id.is_(None)),
        )
    )
    found = {row[0] for row in result.all()}
    missing = set(category_ids) - found
    if missing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"detail": "Category not found", "code": "CATEGORY_NOT_FOUND"},
        )


def _validate_limit_amounts(items_data: list) -> None:
    for it in items_data:
        if it["limit_amount"] is None or float(it["limit_amount"]) <= 0:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"detail": "limit_amount must be > 0", "code": "INVALID_LIMIT_AMOUNT"},
            )


async def _get_owned_budget(
    db: AsyncSession, user_id: uuid.UUID, budget_id: uuid.UUID,
) -> Budget:
    result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    budget = result.scalars().first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")
    return budget


async def list_budgets(
    db: AsyncSession,
    user_id: uuid.UUID,
    period_from: Optional[str] = None,
    period_to: Optional[str] = None,
) -> List[Budget]:
    from datetime import datetime as _dt

    stmt = select(Budget).where(Budget.user_id == user_id)
    if period_from:
        stmt = stmt.where(Budget.period_end >= _dt.strptime(period_from, "%Y-%m-%d").date())
    if period_to:
        stmt = stmt.where(Budget.period_start <= _dt.strptime(period_to, "%Y-%m-%d").date())
    stmt = stmt.order_by(Budget.period_start.desc())
    result = await db.execute(stmt)
    return list(result.scalars().unique().all())


async def get_budget(
    db: AsyncSession, user_id: uuid.UUID, budget_id: uuid.UUID,
) -> Budget:
    return await _get_owned_budget(db, user_id, budget_id)


async def create_budget(
    db: AsyncSession, user_id: uuid.UUID, payload: dict,
) -> Budget:
    items_data = payload.pop("items", [])
    cat_ids = [it["category_id"] for it in items_data]
    await _validate_category_ids(db, user_id, cat_ids)
    _validate_limit_amounts(items_data)

    budget = Budget(
        user_id=user_id,
        name=payload["name"],
        period_start=payload["period_start"],
        period_end=payload["period_end"],
        period_type=payload.get("period_type", "monthly"),
        thresholds=payload.get("thresholds", [0.8, 0.9, 1.0]),
    )
    db.add(budget)
    await db.flush()

    for it in items_data:
        item = BudgetItem(
            budget_id=budget.id,
            category_id=it["category_id"],
            limit_amount=it["limit_amount"],
        )
        db.add(item)

    await db.commit()
    await db.refresh(budget)
    return budget


async def update_budget(
    db: AsyncSession, user_id: uuid.UUID, budget_id: uuid.UUID, payload: dict,
) -> Budget:
    budget = await _get_owned_budget(db, user_id, budget_id)

    if "name" in payload and payload["name"] is not None:
        budget.name = payload["name"]
    if "period_start" in payload and payload["period_start"] is not None:
        budget.period_start = payload["period_start"]
    if "period_end" in payload and payload["period_end"] is not None:
        budget.period_end = payload["period_end"]

    start = budget.period_start
    end = budget.period_end
    if end < start:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="period_end must be >= period_start",
        )

    if "period_type" in payload and payload["period_type"] is not None:
        budget.period_type = payload["period_type"]
    if "thresholds" in payload and payload["thresholds"] is not None:
        budget.thresholds = payload["thresholds"]

    if "items" in payload and payload["items"] is not None:
        items_data = payload["items"]
        cat_ids = [it["category_id"] for it in items_data]

        seen = set()
        for cid in cat_ids:
            if cid in seen:
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail={"detail": "Duplicate category_id in items", "code": "DUPLICATE_ITEM"},
                )
            seen.add(cid)

        await _validate_category_ids(db, user_id, cat_ids)
        _validate_limit_amounts(items_data)

        await db.execute(
            delete(BudgetItem).where(BudgetItem.budget_id == budget.id)
        )

        for it in items_data:
            db.add(BudgetItem(
                budget_id=budget.id,
                category_id=it["category_id"],
                limit_amount=it["limit_amount"],
            ))

    budget.updated_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(budget)
    return budget


async def delete_budget(
    db: AsyncSession, user_id: uuid.UUID, budget_id: uuid.UUID,
) -> None:
    budget = await _get_owned_budget(db, user_id, budget_id)
    await db.delete(budget)
    await db.commit()
