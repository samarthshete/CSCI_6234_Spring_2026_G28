import csv
import hashlib
import io
import re
import uuid
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.account import FinancialAccount
from app.models.import_session import ImportSession
from app.models.transaction import Merchant, Transaction


REQUIRED_COLUMNS = {"posted_date", "amount", "description"}
MAX_ROW_ERRORS = 50


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip()).lower()


def _compute_fingerprint(posted_date: date, amount: Decimal, desc_normalized: str) -> str:
    raw = f"{posted_date.isoformat()}|{amount}|{desc_normalized}"
    return hashlib.sha256(raw.encode()).hexdigest()


def _validate_csv_schema(reader: csv.DictReader) -> Optional[str]:
    if reader.fieldnames is None:
        return "CSV file is empty or has no header row."
    headers = set(reader.fieldnames)
    missing = REQUIRED_COLUMNS - headers
    if missing:
        return f"Missing required columns: {', '.join(sorted(missing))}. Required: posted_date, amount, description."
    return None


def _parse_date(value: str) -> date:
    return datetime.strptime(value.strip(), "%Y-%m-%d").date()


def _parse_amount(value: str) -> Decimal:
    d = Decimal(value.strip())
    if d != d.quantize(Decimal("0.01")):
        raise InvalidOperation("More than 2 decimal places")
    return d


async def _get_or_create_merchant(db: AsyncSession, raw_name: str) -> uuid.UUID:
    normalized = _normalize(raw_name)
    result = await db.execute(
        select(Merchant.id).where(Merchant.name_normalized == normalized)
    )
    row = result.first()
    if row:
        return row[0]
    merchant = Merchant(name=raw_name.strip(), name_normalized=normalized)
    db.add(merchant)
    await db.flush()
    return merchant.id


async def verify_account_ownership(
    db: AsyncSession, user_id: uuid.UUID, account_id: uuid.UUID,
) -> FinancialAccount:
    result = await db.execute(
        select(FinancialAccount).where(
            FinancialAccount.id == account_id,
            FinancialAccount.user_id == user_id,
        )
    )
    account = result.scalars().first()
    if not account:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Account not found.")
    return account


async def import_transactions(
    db: AsyncSession,
    user_id: uuid.UUID,
    account_id: uuid.UUID,
    file_bytes: bytes,
) -> Tuple[ImportSession, List[dict]]:
    account = await verify_account_ownership(db, user_id, account_id)

    try:
        text = file_bytes.decode("utf-8")
    except UnicodeDecodeError:
        raise HTTPException(status_code=400, detail="File must be UTF-8 encoded.")

    reader = csv.DictReader(io.StringIO(text))
    schema_error = _validate_csv_schema(reader)
    if schema_error:
        raise HTTPException(status_code=422, detail=schema_error)

    rows = list(reader)
    if not rows:
        raise HTTPException(status_code=422, detail="CSV file has no data rows.")

    session = ImportSession(
        user_id=user_id,
        account_id=account_id,
        status="processing",
        total_rows=len(rows),
    )
    db.add(session)
    await db.flush()

    imported = 0
    duplicates = 0
    failed = 0
    row_errors: List[dict] = []

    for idx, row in enumerate(rows, start=2):
        # Parse posted_date
        try:
            posted_date = _parse_date(row["posted_date"])
        except (ValueError, KeyError):
            failed += 1
            if len(row_errors) < MAX_ROW_ERRORS:
                row_errors.append({"row": idx, "message": "Invalid or missing posted_date. Use YYYY-MM-DD."})
            continue

        # Parse amount
        try:
            amount = _parse_amount(row["amount"])
        except (InvalidOperation, ValueError, KeyError):
            failed += 1
            if len(row_errors) < MAX_ROW_ERRORS:
                row_errors.append({"row": idx, "message": "Invalid or missing amount."})
            continue

        # Parse description
        description = (row.get("description") or "").strip()
        if not description:
            failed += 1
            if len(row_errors) < MAX_ROW_ERRORS:
                row_errors.append({"row": idx, "message": "description must not be empty."})
            continue

        desc_normalized = _normalize(description)
        fingerprint = _compute_fingerprint(posted_date, amount, desc_normalized)
        currency = (row.get("currency") or "").strip().upper()
        if not currency or len(currency) != 3:
            currency = account.currency

        merchant_id = None
        merchant_raw = (row.get("merchant") or "").strip()
        if merchant_raw:
            merchant_id = await _get_or_create_merchant(db, merchant_raw)

        # Attempt insert; on fingerprint conflict, count as duplicate
        stmt = (
            pg_insert(Transaction)
            .values(
                account_id=account_id,
                posted_date=posted_date,
                amount=amount,
                description=description,
                description_normalized=desc_normalized,
                currency=currency,
                merchant_id=merchant_id,
                import_session_id=session.id,
                fingerprint=fingerprint,
            )
            .on_conflict_do_nothing(constraint="uq_transactions_account_fingerprint")
        )
        result = await db.execute(stmt)
        if result.rowcount == 1:
            imported += 1
        else:
            duplicates += 1

    session.imported_count = imported
    session.duplicate_count = duplicates
    session.failed_count = failed
    session.status = "completed"
    session.completed_at = datetime.now(timezone.utc)
    if row_errors:
        session.metadata_json = {"row_errors": row_errors}

    await db.commit()
    await db.refresh(session)
    return session, row_errors


async def list_sessions(
    db: AsyncSession, user_id: uuid.UUID, limit: int = 20, offset: int = 0,
) -> List[ImportSession]:
    result = await db.execute(
        select(ImportSession)
        .where(ImportSession.user_id == user_id)
        .order_by(ImportSession.started_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())


async def get_session(
    db: AsyncSession, user_id: uuid.UUID, session_id: uuid.UUID,
) -> ImportSession:
    result = await db.execute(
        select(ImportSession).where(
            ImportSession.id == session_id,
            ImportSession.user_id == user_id,
        )
    )
    session = result.scalars().first()
    if not session:
        raise HTTPException(status_code=404, detail="Import session not found.")
    return session
