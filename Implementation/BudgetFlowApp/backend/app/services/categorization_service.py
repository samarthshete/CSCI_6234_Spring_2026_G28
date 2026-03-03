import re
import uuid
from decimal import Decimal
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import FinancialAccount
from app.models.category import Category
from app.models.transaction import Transaction, Merchant


# ---------------------------------------------------------------------------
# Category CRUD
# ---------------------------------------------------------------------------

async def list_categories(
    db: AsyncSession, user_id: uuid.UUID,
) -> List[Category]:
    result = await db.execute(
        select(Category)
        .where(or_(Category.user_id == user_id, Category.user_id.is_(None)))
        .order_by(Category.name)
    )
    return list(result.scalars().all())


async def create_category(
    db: AsyncSession, user_id: uuid.UUID, payload: dict,
) -> Category:
    rules_raw = payload.get("rules", [])
    rules = [r if isinstance(r, dict) else r.model_dump() for r in rules_raw]
    _validate_rules(rules)
    cat = Category(
        user_id=user_id,
        name=payload["name"],
        type=payload.get("type", "expense"),
        rules=rules,
    )
    db.add(cat)
    await db.flush()
    await db.commit()
    await db.refresh(cat)
    return cat


async def update_category(
    db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID, payload: dict,
) -> Category:
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    if cat.user_id is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="System categories are read-only.")
    if cat.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    if "name" in payload and payload["name"] is not None:
        cat.name = payload["name"]
    if "type" in payload and payload["type"] is not None:
        cat.type = payload["type"]
    if "rules" in payload and payload["rules"] is not None:
        rules_raw = payload["rules"]
        rules = [r if isinstance(r, dict) else r.model_dump() for r in rules_raw]
        _validate_rules(rules)
        cat.rules = rules
    await db.commit()
    await db.refresh(cat)
    return cat


def _validate_rules(rules: list) -> None:
    """Pre-validate all regex patterns at write time."""
    for rule in rules:
        if rule.get("match") == "regex":
            pattern = rule.get("pattern", "")
            try:
                re.compile(pattern)
            except re.error:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"detail": "Invalid regex pattern", "code": "INVALID_REGEX"},
                )


# ---------------------------------------------------------------------------
# Rule engine
# ---------------------------------------------------------------------------

def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _match_rule(rule: dict, text: str) -> bool:
    pattern = rule.get("pattern", "")
    match_type = rule.get("match", "contains")
    if match_type == "regex":
        try:
            return bool(re.search(pattern, text, re.IGNORECASE))
        except re.error:
            return False
    # default: contains
    return _normalize(pattern) in text


def _run_rules_engine(
    categories: List[Category], description_normalized: str, merchant_normalized: Optional[str],
) -> Optional[Category]:
    """
    Evaluate all rules across all categories.
    Returns the winning category or None.
    """
    candidates = []
    for cat in categories:
        for rule in (cat.rules or []):
            pattern = rule.get("pattern", "")
            priority = rule.get("priority", 100)
            matched = False
            if description_normalized and _match_rule(rule, description_normalized):
                matched = True
            if not matched and merchant_normalized and _match_rule(rule, merchant_normalized):
                matched = True
            if matched:
                candidates.append((priority, -len(pattern), cat.name, cat))
                break

    if not candidates:
        return None

    candidates.sort(key=lambda c: (c[0], c[1], c[2]))
    return candidates[0][3]


# ---------------------------------------------------------------------------
# Transaction categorization
# ---------------------------------------------------------------------------

async def _get_user_transaction(
    db: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID,
) -> Transaction:
    """Fetch a transaction and verify user ownership via account."""
    result = await db.execute(
        select(Transaction)
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(
            Transaction.id == transaction_id,
            FinancialAccount.user_id == user_id,
        )
    )
    tx = result.scalars().first()
    if not tx:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Transaction not found.")
    return tx


async def categorize_transaction(
    db: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    manual_category_id: Optional[uuid.UUID] = None,
) -> Transaction:
    tx = await _get_user_transaction(db, user_id, transaction_id)

    if manual_category_id is not None:
        cat = await _verify_category_access(db, user_id, manual_category_id)
        tx.category_id = cat.id
        tx.needs_manual = False
        tx.categorization_source = "manual"
        tx.category_confidence = Decimal("1.000")
    else:
        categories = await list_categories(db, user_id)
        merchant_normalized = None
        if tx.merchant_id:
            m_result = await db.execute(
                select(Merchant.name_normalized).where(Merchant.id == tx.merchant_id)
            )
            row = m_result.first()
            if row:
                merchant_normalized = row[0]

        desc_norm = tx.description_normalized or _normalize(tx.description or "")
        winner = _run_rules_engine(categories, desc_norm, merchant_normalized)
        if winner:
            tx.category_id = winner.id
            tx.needs_manual = False
            tx.categorization_source = "rule"
            tx.category_confidence = Decimal("1.000")
        else:
            tx.category_id = None
            tx.needs_manual = True
            tx.categorization_source = None
            tx.category_confidence = None

    await db.commit()
    await db.refresh(tx)
    return tx


async def _verify_category_access(
    db: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID,
) -> Category:
    """Category must be system-owned or owned by user."""
    result = await db.execute(
        select(Category).where(Category.id == category_id)
    )
    cat = result.scalars().first()
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    if cat.user_id is not None and cat.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found.")
    return cat


# ---------------------------------------------------------------------------
# Transaction listing
# ---------------------------------------------------------------------------

async def list_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    account_id: Optional[uuid.UUID] = None,
    category_id: Optional[uuid.UUID] = None,
    date_from: Optional[str] = None,
    date_to: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
) -> List[Transaction]:
    from datetime import datetime as _dt

    stmt = (
        select(Transaction)
        .join(FinancialAccount, FinancialAccount.id == Transaction.account_id)
        .where(FinancialAccount.user_id == user_id)
    )
    if account_id:
        stmt = stmt.where(Transaction.account_id == account_id)
    if category_id:
        stmt = stmt.where(Transaction.category_id == category_id)
    if date_from:
        stmt = stmt.where(Transaction.posted_date >= _dt.strptime(date_from, "%Y-%m-%d").date())
    if date_to:
        stmt = stmt.where(Transaction.posted_date <= _dt.strptime(date_to, "%Y-%m-%d").date())

    stmt = stmt.order_by(Transaction.posted_date.desc()).limit(limit).offset(offset)
    result = await db.execute(stmt)
    return list(result.scalars().all())
