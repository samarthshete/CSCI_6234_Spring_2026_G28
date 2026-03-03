import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.category import CategorizeRequest
from app.schemas.transaction import ImportSessionRead, RowError, TransactionRead
from app.services import import_service, categorization_service

router = APIRouter(redirect_slashes=False)


# ---------------------------------------------------------------------------
# Transaction listing
# ---------------------------------------------------------------------------

@router.get("", response_model=List[TransactionRead])
async def list_transactions(
    account_id: Optional[uuid.UUID] = Query(None),
    category_id: Optional[uuid.UUID] = Query(None),
    date_from: Optional[str] = Query(None),
    date_to: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await categorization_service.list_transactions(
        db, current_user.id,
        account_id=account_id,
        category_id=category_id,
        date_from=date_from,
        date_to=date_to,
        limit=limit,
        offset=offset,
    )


# ---------------------------------------------------------------------------
# Categorize a single transaction
# ---------------------------------------------------------------------------

@router.post("/{transaction_id}/categorize", response_model=TransactionRead)
async def categorize_transaction(
    transaction_id: uuid.UUID,
    body: Optional[CategorizeRequest] = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    manual_id = body.category_id if body else None
    tx = await categorization_service.categorize_transaction(
        db, current_user.id, transaction_id, manual_id,
    )
    return tx


# ---------------------------------------------------------------------------
# CSV Import (UC03)
# ---------------------------------------------------------------------------

@router.post("/import", response_model=ImportSessionRead, status_code=status.HTTP_202_ACCEPTED)
async def import_csv(
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith(".csv"):
        from fastapi import HTTPException
        raise HTTPException(status_code=400, detail="File must be a .csv file.")

    contents = await file.read()
    session, row_errors = await import_service.import_transactions(
        db, current_user.id, account_id, contents,
    )
    return ImportSessionRead(
        id=session.id,
        user_id=session.user_id,
        account_id=session.account_id,
        status=session.status,
        total_rows=session.total_rows,
        imported_count=session.imported_count,
        duplicate_count=session.duplicate_count,
        failed_count=session.failed_count,
        started_at=session.started_at,
        completed_at=session.completed_at,
        row_errors=[RowError(**e) for e in row_errors] if row_errors else None,
    )


@router.get("/import/sessions", response_model=List[ImportSessionRead])
async def list_import_sessions(
    limit: int = 20,
    offset: int = 0,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sessions = await import_service.list_sessions(db, current_user.id, limit, offset)
    return sessions


@router.get("/import/sessions/{session_id}", response_model=ImportSessionRead)
async def get_import_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return await import_service.get_session(db, current_user.id, session_id)
