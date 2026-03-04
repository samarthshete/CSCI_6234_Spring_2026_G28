"""
UC09 Worker: polls pending jobs, executes handlers.
Run as: python -m app.worker.worker
"""
import asyncio
import traceback
import uuid
from datetime import datetime, timezone
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import AsyncSessionLocal
from app.models.job import Job
from app.services import job_service
from app.worker.registry import get_handler
from app.storage.s3_storage import S3Storage


POLL_INTERVAL = 0.75
BATCH_SIZE = 5


def _get_storage():
    return S3Storage()


async def _claim_next_job() -> Optional[uuid.UUID]:
    """
    Atomically claim the next pending job:
    - SELECT ... FOR UPDATE SKIP LOCKED
    - set status='running', started_at/updated_at=now()
    - commit and return job.id (UUID)
    """
    async with AsyncSessionLocal() as session:
        async with session.begin():
            stmt = (
                select(Job)
                .where(Job.status == "pending")
                .order_by(Job.created_at.asc())
                .limit(1)
                .with_for_update(skip_locked=True)
            )
            result = await session.execute(stmt)
            job = result.scalars().first()
            if not job:
                return None
            now = datetime.now(timezone.utc)
            job.status = "running"
            job.started_at = now
            job.updated_at = now
        return job.id


async def _execute_job(session: AsyncSession, job: Job, storage) -> bool:
    """Execute one job. Returns True if a job was processed."""
    handler = get_handler(job.type)
    if not handler:
        await job_service.mark_failed(
            session, job,
            error_message=f"Unknown job type: {job.type}",
        )
        return True

    # job is already marked running in _claim_next_job
    try:
        result = await handler(session, job, storage)
        await job_service.mark_succeeded(session, job, result)
        return True
    except Exception as exc:
        await job_service.mark_failed(
            session, job,
            error_message=str(exc)[:2000],
            error_trace=traceback.format_exc(),
        )
        return True


async def run_once(storage=None) -> bool:
    """
    Process up to BATCH_SIZE jobs.
    Each iteration:
      - claims a job in a short transaction
      - opens a fresh AsyncSessionLocal() to load and execute the job
    All awaits are sequential; no asyncio.gather.
    """
    storage = storage or _get_storage()
    processed_any = False

    for _ in range(BATCH_SIZE):
        job_id = await _claim_next_job()
        if not job_id:
            break

        async with AsyncSessionLocal() as session:
            job = await session.get(Job, job_id)
            if not job or job.status != "running":
                continue
            await _execute_job(session, job, storage)
            processed_any = True

    return processed_any


async def run_loop() -> None:
    """Infinite poll loop for worker process."""
    storage = _get_storage()
    print("Worker started, polling for jobs...")
    while True:
        try:
            await run_once(storage)
        except Exception as exc:
            print(f"Worker error: {exc}")
        await asyncio.sleep(POLL_INTERVAL)


def main() -> None:
    asyncio.run(run_loop())


if __name__ == "__main__":
    main()
