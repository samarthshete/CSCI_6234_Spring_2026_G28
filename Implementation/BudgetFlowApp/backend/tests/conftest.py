import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from typing import AsyncGenerator

from app.main import app
from app.core.config import settings
from app.core.database import get_db
from sqlalchemy.pool import NullPool


@pytest_asyncio.fixture(scope="session")
def anyio_backend():
    return "asyncio"


@pytest_asyncio.fixture(scope="function")
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    # Use NullPool to avoid issues with connection sharing across asyncio loops
    engine = create_async_engine(settings.effective_database_url, echo=False, poolclass=NullPool)
    TestingSessionLocal = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with TestingSessionLocal() as session:
        yield session
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def async_client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def run_worker_until_done(max_iterations: int = 10) -> None:
    """Run worker until no pending jobs. Use in tests after async import."""
    from app.worker.worker import run_once
    from app.storage.memory_storage import MemoryStorage

    storage = MemoryStorage()
    for _ in range(max_iterations):
        processed = await run_once(storage)
        if not processed:
            break
