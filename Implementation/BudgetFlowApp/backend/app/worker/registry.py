"""
Job type -> handler registry. Handlers receive (db, job, storage).
"""
import base64
import uuid
from typing import Callable, Awaitable, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job
from app.models.import_session import ImportSession
from app.services import import_service
from app.storage import ReportStorage


Handler = Callable[[AsyncSession, Job, ReportStorage], Awaitable[dict]]


async def _handle_report_generate(
    db: AsyncSession,
    job: Job,
    storage: ReportStorage,
) -> dict:
    report_id = job.payload.get("report_id")
    if not report_id:
        raise ValueError("report_id required in payload")
    from app.services import report_service
    return await report_service.generate_report_by_id(db, uuid.UUID(report_id), storage)


async def _handle_transactions_import_csv(
    db: AsyncSession,
    job: Job,
    storage: ReportStorage,
) -> dict:
    user_id = job.payload.get("user_id")
    account_id = job.payload.get("account_id")
    import_session_id = job.payload.get("import_session_id")
    file_base64 = job.payload.get("file_base64")
    if not all([user_id, account_id, import_session_id, file_base64]):
        raise ValueError("user_id, account_id, import_session_id, file_base64 required in payload")

    file_bytes = base64.b64decode(file_base64)
    user_id_uuid = uuid.UUID(user_id)
    account_id_uuid = uuid.UUID(account_id)
    session_id_uuid = uuid.UUID(import_session_id)

    result = await db.execute(
        select(ImportSession).where(
            ImportSession.id == session_id_uuid,
            ImportSession.user_id == user_id_uuid,
        )
    )
    session = result.scalars().first()
    if not session:
        raise ValueError(f"Import session {import_session_id} not found or not owned by user")

    try:
        session, row_errors = await import_service.process_import_file(db, session, file_bytes)
        return {
            "import_session_id": str(session.id),
            "inserted_count": session.imported_count,
            "skipped_duplicates": session.duplicate_count,
            "failed_rows": session.failed_count,
            "row_errors_count": len(row_errors) if row_errors else 0,
        }
    except Exception as exc:
        from datetime import datetime, timezone
        session.status = "failed"
        session.completed_at = datetime.now(timezone.utc)
        session.metadata_json = (session.metadata_json or {}) | {"error": str(exc)[:500]}
        await db.commit()
        raise


JOB_HANDLERS: dict[str, Handler] = {
    "report.generate": _handle_report_generate,
    "transactions.import_csv": _handle_transactions_import_csv,
}


def get_handler(job_type: str) -> Optional[Handler]:
    return JOB_HANDLERS.get(job_type)
