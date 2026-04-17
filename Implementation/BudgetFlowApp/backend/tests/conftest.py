import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from app.storage.memory_storage import MemoryStorage
from app.worker.worker import run_once
from sqlalchemy.pool import NullPool


_worker_storage = MemoryStorage()


@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def _shared_engine():
    """One AsyncEngine for the entire test session.

    Creating and disposing a fresh engine for every test (and again in autouse
    cleanup) meant many asyncpg connect/disconnect cycles per test. Combined
    with pytest-asyncio's per-test event loops, that occasionally surfaced as
    ``RuntimeError: Event loop is closed`` during connection teardown in
    unrelated tests.

    A single session-scoped engine is disposed exactly once after all tests
    finish, which keeps connection lifecycle deterministic.
    """
    engine = create_async_engine(
        settings.effective_database_url,
        echo=False,
        poolclass=NullPool,
    )
    yield engine
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def test_engine(_shared_engine):
    """Expose the shared engine as a function-scoped fixture (dependency hook)."""
    yield _shared_engine


@pytest_asyncio.fixture(autouse=True)
async def _empty_jobs_queue_before_test(test_engine) -> AsyncGenerator[None, None]:
    """Jobs are processed by a global worker query (pending, FIFO).

    Without clearing between tests, ``run_once`` in one test can claim jobs
    enqueued by another test that shares the same Postgres database, causing
    order-dependent failures (e.g. Jobs API pending counts).
    """
    async with test_engine.begin() as conn:
        await conn.execute(text("DELETE FROM jobs"))
    yield


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session(test_engine) -> AsyncGenerator[AsyncSession, None]:
    TestingSessionLocal = async_sessionmaker(bind=test_engine, class_=AsyncSession, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def run_worker_until_done(db_session: AsyncSession, max_iterations: int = 10) -> None:
    """Drain pending jobs using the *same* AsyncEngine as the test API session.

    A fresh AsyncSession is opened per worker batch via *session_factory* so we
    never share the long-lived ``db_session`` with the worker (FOR UPDATE / TX).

    Roll back the API session first: after httpx calls, it may be *idle in
    transaction* (SQLAlchemy autobegin). That can interact with the worker's
    ``FOR UPDATE SKIP LOCKED`` claim in the same DB session under heavy suites,
    occasionally leaving jobs unprocessed while the test session still holds
    snapshot/locks — reports then stay ``queued``.
    """
    await db_session.rollback()
    factory = async_sessionmaker(
        bind=db_session.bind,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    for _ in range(max_iterations):
        processed = await run_once(_worker_storage, session_factory=factory)
        if not processed:
            break
    # Worker commits in a separate session; expire cached instances on the API
    # session so follow-up requests see updated rows (expire_on_commit=False).
    db_session.expire_all()
