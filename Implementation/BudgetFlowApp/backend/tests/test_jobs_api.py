"""Tests for Jobs API: list, get, user isolation."""
import uuid

import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.pool import NullPool

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.core import security
from app.models.user import User
from app.services import job_service

API_JOBS = "/api/v1/jobs"


async def _create_user(db: AsyncSession, email: str, name: str = "Test") -> User:
    user = User(email=email, name=name, hashed_password=security.get_password_hash("TestPass1!"))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _auth_header(user_id) -> dict:
    token = security.create_access_token(user_id)
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(settings.effective_database_url, echo=False, poolclass=NullPool)
    session_factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def client(db):
    async def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_list_jobs_user_isolation(client: AsyncClient, db: AsyncSession):
    suffix = uuid.uuid4().hex[:8]
    user_a = await _create_user(db, f"jobs_a_{suffix}@test.com", "User A")
    user_b = await _create_user(db, f"jobs_b_{suffix}@test.com", "User B")

    await job_service.enqueue_job(db, user_a.id, "report.generate", {"report_id": "00000000-0000-0000-0000-000000000001"})
    await job_service.enqueue_job(db, user_a.id, "transactions.import_csv", {"account_id": "00000000-0000-0000-0000-000000000002"})
    await job_service.enqueue_job(db, user_b.id, "report.generate", {"report_id": "00000000-0000-0000-0000-000000000003"})

    res_a = await client.get(API_JOBS, headers=_auth_header(user_a.id))
    assert res_a.status_code == 200
    jobs_a = res_a.json()
    assert len(jobs_a) == 2
    types_a = {j["type"] for j in jobs_a}
    assert types_a == {"report.generate", "transactions.import_csv"}

    res_b = await client.get(API_JOBS, headers=_auth_header(user_b.id))
    assert res_b.status_code == 200
    jobs_b = res_b.json()
    assert len(jobs_b) == 1
    assert jobs_b[0]["type"] == "report.generate"


@pytest.mark.asyncio
async def test_list_jobs_filters(client: AsyncClient, db: AsyncSession):
    user = await _create_user(db, f"jobs_filter_{uuid.uuid4().hex[:8]}@test.com")
    await job_service.enqueue_job(db, user.id, "report.generate", {"x": 1})
    await job_service.enqueue_job(db, user.id, "transactions.import_csv", {"x": 2})

    res = await client.get(f"{API_JOBS}?type=report.generate", headers=_auth_header(user.id))
    assert res.status_code == 200
    jobs = res.json()
    assert len(jobs) == 1
    assert jobs[0]["type"] == "report.generate"

    res2 = await client.get(f"{API_JOBS}?status=pending", headers=_auth_header(user.id))
    assert res2.status_code == 200
    assert len(res2.json()) == 2


@pytest.mark.asyncio
async def test_get_job_detail_isolated(client: AsyncClient, db: AsyncSession):
    suffix = uuid.uuid4().hex[:8]
    user_a = await _create_user(db, f"job_detail_a_{suffix}@test.com")
    user_b = await _create_user(db, f"job_detail_b_{suffix}@test.com")

    job = await job_service.enqueue_job(db, user_a.id, "report.generate", {"report_id": "abc"})
    job_id = str(job.id)

    res_a = await client.get(f"{API_JOBS}/{job_id}", headers=_auth_header(user_a.id))
    assert res_a.status_code == 200
    assert res_a.json()["id"] == job_id
    assert res_a.json()["payload"]["report_id"] == "abc"

    res_b = await client.get(f"{API_JOBS}/{job_id}", headers=_auth_header(user_b.id))
    assert res_b.status_code == 404
