import base64
import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.import_session import ImportSession
from app.models.user import User
from app.schemas.category import CategorizeRequest
from app.schemas.transaction import ImportQueuedResponse, ImportSessionRead, RowError, TransactionRead
from app.services import import_service, categorization_service, job_service

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
# CSV Import (UC03) - Async via UC09 job framework
# ---------------------------------------------------------------------------

@router.post("/import", response_model=ImportQueuedResponse, status_code=status.HTTP_202_ACCEPTED)
async def import_csv(
    account_id: uuid.UUID = Form(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="File must be a .csv file.")

    contents = await file.read()
    if len(contents) > import_service.MAX_FILE_SIZE_BYTES:
        raise HTTPException(status_code=413, detail="File too large. Maximum size is 2MB.")

    await import_service.verify_account_ownership(db, current_user.id, account_id)

    header_error = import_service.validate_csv_headers(contents)
    if header_error:
        raise HTTPException(status_code=422, detail=header_error)

    session = ImportSession(
        user_id=current_user.id,
        account_id=account_id,
        status="queued",
        total_rows=0,
    )
    db.add(session)
    await db.flush()

    file_base64 = base64.b64encode(contents).decode("ascii")
    job = await job_service.create_job_in_session(
        db, current_user.id,
        "transactions.import_csv",
        {
            "user_id": str(current_user.id),
            "account_id": str(account_id),
            "import_session_id": str(session.id),
            "file_base64": file_base64,
            "filename": file.filename or "import.csv",
        },
    )
    await db.commit()
    await db.refresh(session)
    await db.refresh(job)

    return ImportQueuedResponse(
        import_session_id=session.id,
        job_id=job.id,
        status="queued",
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
