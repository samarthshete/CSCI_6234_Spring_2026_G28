import uuid
from typing import List, Optional

from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.schemas.report import ReportCreate, ReportRead
from app.services import report_service, job_service
from app.storage import ReportStorage
from app.storage.s3_storage import S3Storage

router = APIRouter(redirect_slashes=False)

_storage_instance: Optional[ReportStorage] = None

REPORT_NOT_READY = "REPORT_NOT_READY"


def get_storage() -> ReportStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = S3Storage()
    return _storage_instance


async def _enrich_report_response(report, db, user_id, storage: ReportStorage) -> dict:
    data = ReportRead.model_validate(report).model_dump()
    if report.status == "succeeded" and report.storage_key:
        data["download_url"] = await storage.get_presigned_url(report.storage_key)
    if report.job_id:
        try:
            job = await job_service.get_job(db, user_id, report.job_id)
            data["job_status"] = job.status
        except Exception:
            data["job_status"] = None
    return data


@router.post("", status_code=status.HTTP_202_ACCEPTED)
async def create_report(
    payload: ReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: ReportStorage = Depends(get_storage),
):
    filters = payload.filters.model_dump() if payload.filters else None
    report = await report_service.create_report_async(
        db, current_user.id, payload.type, payload.format,
        payload.from_date, payload.to_date, filters,
    )
    return await _enrich_report_response(report, db, current_user.id, storage)


@router.get("", response_model=List[ReportRead])
async def list_reports(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: ReportStorage = Depends(get_storage),
):
    reports = await report_service.list_reports(db, current_user.id)
    return [await _enrich_report_response(r, db, current_user.id, storage) for r in reports]


@router.get("/{report_id}")
async def get_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: ReportStorage = Depends(get_storage),
):
    report = await report_service.get_report(db, current_user.id, report_id)
    return await _enrich_report_response(report, db, current_user.id, storage)


@router.get("/{report_id}/download")
async def download_report(
    report_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    storage: ReportStorage = Depends(get_storage),
):
    report = await report_service.get_report(db, current_user.id, report_id)
    if report.status in ("queued", "running"):
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Report is not ready for download", "code": REPORT_NOT_READY},
        )
    if report.status == "failed":
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": report.error or "Report generation failed", "code": "REPORT_FAILED"},
        )
    if report.status != "succeeded" or not report.storage_key:
        return JSONResponse(
            status_code=status.HTTP_409_CONFLICT,
            content={"detail": "Report is not ready for download", "code": REPORT_NOT_READY},
        )
    url = await storage.get_presigned_url(report.storage_key)
    return {"download_url": url}
