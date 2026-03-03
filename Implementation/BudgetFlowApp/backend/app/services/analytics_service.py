import uuid
from datetime import date
from decimal import Decimal
from typing import Dict, List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, func, cast, Date
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import FinancialAccount
from app.models.budget import Budget, BudgetItem
from app.models.transaction import Transaction


def _base_expense_query(user_id: uuid.UUID):
    """Reusable base: user-isolated transactions joined via account."""
    return (
        select(func.coalesce(func.sum(func.abs(Transaction.amount)), 0))
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(FinancialAccount.user_id == user_id)
    )


def _apply_filters(stmt, date_from=None, date_to=None, account_ids=None, category_ids=None):
    if date_from:
        stmt = stmt.where(Transaction.posted_date >= date_from)
    if date_to:
        stmt = stmt.where(Transaction.posted_date <= date_to)
    if account_ids:
        stmt = stmt.where(Transaction.account_id.in_(account_ids))
    if category_ids:
        stmt = stmt.where(Transaction.category_id.in_(category_ids))
    return stmt


async def get_summary(
    db: AsyncSession,
    user_id: uuid.UUID,
    date_from: Optional[date] = None,
    date_to: Optional[date] = None,
    account_ids: Optional[List[uuid.UUID]] = None,
    category_ids: Optional[List[uuid.UUID]] = None,
) -> dict:
    # Total spending
    total_stmt = _base_expense_query(user_id)
    total_stmt = _apply_filters(total_stmt, date_from, date_to, account_ids, category_ids)
    total_result = await db.execute(total_stmt)
    total_spending = total_result.scalar() or Decimal("0")

    # By category
    by_cat_stmt = (
        select(
            Transaction.category_id,
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("total"),
        )
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(FinancialAccount.user_id == user_id)
        .group_by(Transaction.category_id)
    )
    by_cat_stmt = _apply_filters(by_cat_stmt, date_from, date_to, account_ids, category_ids)
    cat_result = await db.execute(by_cat_stmt)
    by_category = [
        {"category_id": str(row[0]) if row[0] else None, "total": row[1]}
        for row in cat_result.all()
    ]

    # By account
    by_acct_stmt = (
        select(
            Transaction.account_id,
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("total"),
        )
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(FinancialAccount.user_id == user_id)
        .group_by(Transaction.account_id)
    )
    by_acct_stmt = _apply_filters(by_acct_stmt, date_from, date_to, account_ids, category_ids)
    acct_result = await db.execute(by_acct_stmt)
    by_account = [
        {"account_id": str(row[0]), "total": row[1]}
        for row in acct_result.all()
    ]

    return {
        "total_spending": total_spending,
        "by_category": by_category,
        "by_account": by_account,
    }


async def get_trends(
    db: AsyncSession,
    user_id: uuid.UUID,
    date_from: date,
    date_to: date,
    group_by: str = "month",
) -> list:
    period_expr = cast(func.date_trunc(group_by, Transaction.posted_date), Date).label("period")

    stmt = (
        select(
            period_expr,
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("total"),
        )
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(
            FinancialAccount.user_id == user_id,
            Transaction.posted_date >= date_from,
            Transaction.posted_date <= date_to,
        )
        .group_by(period_expr)
        .order_by(period_expr)
    )
    result = await db.execute(stmt)
    return [{"period": row[0].isoformat(), "total": row[1]} for row in result.all()]


async def get_budget_vs_actual(
    db: AsyncSession,
    user_id: uuid.UUID,
    budget_id: uuid.UUID,
) -> list:
    budget_result = await db.execute(
        select(Budget).where(Budget.id == budget_id, Budget.user_id == user_id)
    )
    budget = budget_result.scalars().first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found.")

    rows = []
    if not budget.items:
        return rows

    cat_ids = [item.category_id for item in budget.items]
    limit_map: Dict[uuid.UUID, Decimal] = {item.category_id: item.limit_amount for item in budget.items}

    spent_stmt = (
        select(
            Transaction.category_id,
            func.coalesce(func.sum(func.abs(Transaction.amount)), 0).label("spent"),
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
    spent_result = await db.execute(spent_stmt)
    spent_map = {row[0]: row[1] for row in spent_result.all()}

    for cat_id in cat_ids:
        limit_amt = limit_map[cat_id]
        spent_amt = spent_map.get(cat_id, Decimal("0"))
        pct = (spent_amt / limit_amt) if limit_amt > 0 else Decimal("0")
        rows.append({
            "category_id": str(cat_id),
            "limit_amount": limit_amt,
            "spent_amount": spent_amt,
            "percent": round(pct, 4),
        })

    return rows
