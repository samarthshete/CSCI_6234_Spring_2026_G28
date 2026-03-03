import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import FinancialAccount
from app.models.alert import BudgetAlert
from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction


async def generate_alerts_for_user(
    db: AsyncSession, user_id: uuid.UUID,
) -> None:
    """
    Lazy alert generation: for every budget owned by the user, compute
    actual spend per budget-item category within the budget period, and
    create an alert row for each crossed threshold (idempotent via
    ON CONFLICT DO NOTHING on the unique constraint).
    """
    budgets_result = await db.execute(
        select(Budget).where(Budget.user_id == user_id)
    )
    budgets = list(budgets_result.scalars().unique().all())

    for budget in budgets:
        if not budget.items:
            continue

        cat_ids = [item.category_id for item in budget.items]

        # Sum absolute spend per category within the budget period,
        # scoped to the user's accounts.
        spent_query = (
            select(
                Transaction.category_id,
                func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("total_spent"),
            )
            .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
            .where(
                FinancialAccount.user_id == user_id,
                Transaction.category_id.in_(cat_ids),
                Transaction.posted_date >= budget.period_start,
                Transaction.posted_date <= budget.period_end,
            )
            .group_by(Transaction.category_id)
        )
        spent_result = await db.execute(spent_query)
        spent_map = {row[0]: row[1] for row in spent_result.all()}

        for item in budget.items:
            spent = spent_map.get(item.category_id, Decimal("0"))
            if item.limit_amount <= 0:
                continue
            pct = spent / item.limit_amount

            for threshold in (budget.thresholds or []):
                threshold_dec = Decimal(str(threshold))
                if pct >= threshold_dec:
                    stmt = (
                        pg_insert(BudgetAlert)
                        .values(
                            user_id=user_id,
                            budget_id=budget.id,
                            category_id=item.category_id,
                            threshold_percent=threshold_dec,
                            spent_amount=spent,
                            limit_amount=item.limit_amount,
                            period_start=budget.period_start,
                            period_end=budget.period_end,
                        )
                        .on_conflict_do_nothing(
                            constraint="uq_budget_alerts_budget_cat_thresh_period",
                        )
                    )
                    await db.execute(stmt)

    await db.commit()


async def list_alerts(
    db: AsyncSession,
    user_id: uuid.UUID,
    is_read: Optional[bool] = None,
) -> List[BudgetAlert]:
    await generate_alerts_for_user(db, user_id)

    stmt = (
        select(BudgetAlert)
        .where(BudgetAlert.user_id == user_id)
    )
    if is_read is not None:
        stmt = stmt.where(BudgetAlert.is_read == is_read)
    stmt = stmt.order_by(BudgetAlert.created_at.desc())

    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_alert_read(
    db: AsyncSession, user_id: uuid.UUID, alert_id: uuid.UUID,
) -> BudgetAlert:
    result = await db.execute(
        select(BudgetAlert).where(
            BudgetAlert.id == alert_id,
            BudgetAlert.user_id == user_id,
        )
    )
    alert = result.scalars().first()
    if not alert:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Alert not found.")
    alert.is_read = True
    await db.commit()
    await db.refresh(alert)
    return alert
