"""
UC09 Job service: enqueue, get, list, status transitions.
All operations are user-scoped.
"""
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.job import Job


async def create_job_in_session(
    db: AsyncSession,
    user_id: uuid.UUID,
    job_type: str,
    payload: dict,
) -> Job:
    """Create job in session and flush. Caller must commit."""
    job = Job(user_id=user_id, type=job_type, payload=payload or {}, status="pending")
    db.add(job)
    await db.flush()
    return job


async def enqueue_job(
    db: AsyncSession,
    user_id: uuid.UUID,
    job_type: str,
    payload: dict,
) -> Job:
    job = await create_job_in_session(db, user_id, job_type, payload)
    await db.commit()
    return job


async def claim_pending_jobs(
    db: AsyncSession,
    batch_size: int,
) -> List[Job]:
    """
    Atomically claim a FIFO batch of pending jobs in the current transaction.
    Claimed jobs are marked running before the lock is released.
    """
    stmt = (
        select(Job)
        .where(Job.status == "pending")
        .order_by(Job.created_at.asc())
        .limit(batch_size)
        .with_for_update(skip_locked=True)
    )
    result = await db.execute(stmt)
    jobs = list(result.scalars().unique().all())
    if not jobs:
        return []

    now = datetime.now(timezone.utc)
    for job in jobs:
        job.status = "running"
        if job.started_at is None:
            job.started_at = now
        job.updated_at = now
    await db.flush()
    return jobs


async def get_job(db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    result = await db.execute(
        select(Job).where(Job.id == job_id, Job.user_id == user_id)
    )
    job = result.scalars().first()
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return job


async def get_job_owned(db: AsyncSession, user_id: uuid.UUID, job_id: uuid.UUID) -> Job:
    return await get_job(db, user_id, job_id)


async def list_jobs(
    db: AsyncSession,
    user_id: uuid.UUID,
    status_filter: Optional[str] = None,
    type_filter: Optional[str] = None,
    limit: int = 50,
) -> List[Job]:
    stmt = (
        select(Job)
        .where(Job.user_id == user_id)
        .order_by(Job.created_at.desc())
        .limit(limit)
    )
    if status_filter:
        stmt = stmt.where(Job.status == status_filter)
    if type_filter:
        stmt = stmt.where(Job.type == type_filter)
    result = await db.execute(stmt)
    return list(result.scalars().all())


async def mark_running(db: AsyncSession, job: Job) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(
            status="running",
            started_at=now,
            updated_at=now,
        )
    )
    await db.commit()


async def mark_succeeded(db: AsyncSession, job: Job, result: Optional[dict] = None) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(
            status="succeeded",
            result=result,
            finished_at=now,
            updated_at=now,
            error_message=None,
            error_trace=None,
        )
    )
    await db.commit()


async def mark_failed(
    db: AsyncSession,
    job: Job,
    error_message: str,
    error_trace: Optional[str] = None,
) -> None:
    now = datetime.now(timezone.utc)
    await db.execute(
        update(Job)
        .where(Job.id == job.id)
        .values(
            status="failed",
            error_message=(error_message or "")[:2000],
            error_trace=(error_trace or "")[:5000] if error_trace else None,
            finished_at=now,
            updated_at=now,
        )
    )
    await db.commit()
