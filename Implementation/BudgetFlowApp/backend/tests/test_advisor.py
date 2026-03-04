"""Advisor chat: sessions, messages, tool calling, isolation."""
import uuid
from decimal import Decimal

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
from app.models.account import FinancialAccount
from app.models.transaction import Transaction
from app.api.v1.advisor import get_llm
from app.services.advisor.llm_provider import FakeLLM


@pytest_asyncio.fixture(scope="function")
async def db():
    engine = create_async_engine(settings.effective_database_url, echo=False, poolclass=NullPool)
    factory = async_sessionmaker(bind=engine, class_=AsyncSession, expire_on_commit=False)
    async with factory() as session:
        yield session
    await engine.dispose()


async def _make_user(db: AsyncSession, email: str) -> User:
    user = User(email=email, name="Test", hashed_password=security.get_password_hash("Pass1234!"))
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


def _headers(user_id) -> dict:
    return {"Authorization": f"Bearer {security.create_access_token(user_id)}"}


@pytest_asyncio.fixture(scope="function")
async def client_and_llm(db):
    fake = FakeLLM()

    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db
    app.dependency_overrides[get_llm] = lambda: fake

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac, fake

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_create_session_and_user_isolation(client_and_llm, db):
    client, _ = client_and_llm
    user_a = await _make_user(db, f"adv_a_{uuid.uuid4().hex[:6]}@test.com")
    user_b = await _make_user(db, f"adv_b_{uuid.uuid4().hex[:6]}@test.com")

    res = await client.post("/api/v1/advisor/sessions", json={"title": "My chat"}, headers=_headers(user_a.id))
    assert res.status_code == 201
    sid = res.json()["id"]

    list_a = await client.get("/api/v1/advisor/sessions", headers=_headers(user_a.id))
    assert any(s["id"] == sid for s in list_a.json())

    list_b = await client.get("/api/v1/advisor/sessions", headers=_headers(user_b.id))
    assert not any(s["id"] == sid for s in list_b.json())

    get_b = await client.get(f"/api/v1/advisor/sessions/{sid}", headers=_headers(user_b.id))
    assert get_b.status_code == 404


@pytest.mark.asyncio
async def test_send_message_stores_in_db(client_and_llm, db):
    client, fake = client_and_llm
    fake.push(FakeLLM.make_text_response("Your total spending is $0.00 for the period."))

    user = await _make_user(db, f"adv_msg_{uuid.uuid4().hex[:6]}@test.com")
    headers = _headers(user.id)

    res = await client.post("/api/v1/advisor/message", json={
        "content": "How much did I spend?",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["message"]["role"] == "assistant"
    assert "spending" in data["message"]["content"].lower()

    session_res = await client.get(f"/api/v1/advisor/sessions/{data['session_id']}", headers=headers)
    messages = session_res.json()["messages"]
    roles = [m["role"] for m in messages]
    assert "user" in roles
    assert "assistant" in roles


@pytest.mark.asyncio
async def test_tool_calling_path(client_and_llm, db):
    client, fake = client_and_llm

    fake.push(FakeLLM.make_tool_call_response("get_summary", {
        "date_from": "2026-01-01", "date_to": "2026-01-31",
    }))
    fake.push(FakeLLM.make_text_response(
        "Your total spending from Jan 1-31 was $0.00. No transactions found for this period."
    ))

    user = await _make_user(db, f"adv_tool_{uuid.uuid4().hex[:6]}@test.com")
    headers = _headers(user.id)

    res = await client.post("/api/v1/advisor/message", json={
        "content": "How much did I spend in January 2026?",
    }, headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert "$0.00" in data["message"]["content"]

    session_res = await client.get(f"/api/v1/advisor/sessions/{data['session_id']}", headers=headers)
    messages = session_res.json()["messages"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    assert len(tool_msgs) >= 1
    assert tool_msgs[0]["tool_name"] == "get_summary"


@pytest.mark.asyncio
async def test_tool_missing_args_clarification(client_and_llm, db):
    client, fake = client_and_llm

    fake.push(FakeLLM.make_text_response(
        "Could you specify a date range? For example, 'last month' or 'January 2026'."
    ))

    user = await _make_user(db, f"adv_clar_{uuid.uuid4().hex[:6]}@test.com")
    res = await client.post("/api/v1/advisor/message", json={
        "content": "Show me trends",
    }, headers=_headers(user.id))
    assert res.status_code == 200
    assert "date" in res.json()["message"]["content"].lower()


@pytest.mark.asyncio
async def test_session_isolation_messages(client_and_llm, db):
    client, fake = client_and_llm
    fake.push(FakeLLM.make_text_response("Answer for user A"))
    fake.push(FakeLLM.make_text_response("Answer for user B"))

    user_a = await _make_user(db, f"adv_isomsg_a_{uuid.uuid4().hex[:6]}@test.com")
    user_b = await _make_user(db, f"adv_isomsg_b_{uuid.uuid4().hex[:6]}@test.com")

    res_a = await client.post("/api/v1/advisor/message", json={
        "content": "Question from A",
    }, headers=_headers(user_a.id))
    assert res_a.status_code == 200
    sid_a = res_a.json()["session_id"]

    res_b = await client.post("/api/v1/advisor/message", json={
        "content": "Question from B",
    }, headers=_headers(user_b.id))
    assert res_b.status_code == 200

    get_b = await client.get(f"/api/v1/advisor/sessions/{sid_a}", headers=_headers(user_b.id))
    assert get_b.status_code == 404


# ---------------------------------------------------------------------------
# Recommendation tool integration tests
# ---------------------------------------------------------------------------

async def _seed_acct(db: AsyncSession, user_id: uuid.UUID, income=5000.0, spending=3000.0, balance=10000.0):
    import hashlib
    from datetime import date, timedelta

    acct = FinancialAccount(user_id=user_id, type="bank", name="Checking", currency="USD", balance=Decimal(str(balance)))
    db.add(acct)
    await db.flush()
    recent = date.today() - timedelta(days=15)
    fp1 = hashlib.sha256(f"inc-{user_id}-{uuid.uuid4()}".encode()).hexdigest()[:64]
    db.add(Transaction(account_id=acct.id, posted_date=recent, amount=Decimal(str(income)),
                       description="Salary", description_normalized="salary", fingerprint=fp1, currency="USD"))
    fp2 = hashlib.sha256(f"exp-{user_id}-{uuid.uuid4()}".encode()).hexdigest()[:64]
    db.add(Transaction(account_id=acct.id, posted_date=recent, amount=Decimal(str(-spending)),
                       description="Expenses", description_normalized="expenses", fingerprint=fp2, currency="USD"))
    await db.commit()


@pytest.mark.asyncio
async def test_advisor_run_recommendation_tool(client_and_llm, db):
    """Advisor calls run_recommendation tool and returns grounded answer."""
    client, fake = client_and_llm
    user = await _make_user(db, f"adv_rec_{uuid.uuid4().hex[:6]}@test.com")
    await _seed_acct(db, user.id, income=8000, spending=3000, balance=20000)

    fake.push(FakeLLM.make_tool_call_response("run_recommendation", {"horizon_months": 60}))
    fake.push(FakeLLM.make_text_response(
        "Based on your data, all safety gates pass. Your risk bucket is balanced with $4,000/mo investable."
    ))

    res = await client.post("/api/v1/advisor/message", json={
        "content": "Should I start investing?",
    }, headers=_headers(user.id))
    assert res.status_code == 200

    session_res = await client.get(f"/api/v1/advisor/sessions/{res.json()['session_id']}", headers=_headers(user.id))
    messages = session_res.json()["messages"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    assert len(tool_msgs) >= 1
    assert tool_msgs[0]["tool_name"] == "run_recommendation"
    payload = tool_msgs[0]["tool_payload"]
    assert "gates" in payload
    assert "run_id" in payload


@pytest.mark.asyncio
async def test_advisor_get_latest_recommendation_tool(client_and_llm, db):
    """Advisor calls get_latest_recommendation after a run exists."""
    client, fake = client_and_llm
    user = await _make_user(db, f"adv_latest_{uuid.uuid4().hex[:6]}@test.com")
    await _seed_acct(db, user.id, income=8000, spending=3000, balance=20000)

    # First generate a run via API
    from app.services import recommendation_service
    await recommendation_service.execute_run(db, user.id)

    fake.push(FakeLLM.make_tool_call_response("get_latest_recommendation", {}))
    fake.push(FakeLLM.make_text_response("Your latest recommendation shows a balanced portfolio."))

    res = await client.post("/api/v1/advisor/message", json={
        "content": "What was my last investment recommendation?",
    }, headers=_headers(user.id))
    assert res.status_code == 200

    session_res = await client.get(f"/api/v1/advisor/sessions/{res.json()['session_id']}", headers=_headers(user.id))
    messages = session_res.json()["messages"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    assert len(tool_msgs) >= 1
    assert tool_msgs[0]["tool_name"] == "get_latest_recommendation"
    payload = tool_msgs[0]["tool_payload"]
    assert "run_id" in payload
    assert "action_items" in payload


@pytest.mark.asyncio
async def test_advisor_blocked_user_gets_action_items(client_and_llm, db):
    """When safety gates fail, tool returns action_items not allocation."""
    client, fake = client_and_llm
    user = await _make_user(db, f"adv_blk_{uuid.uuid4().hex[:6]}@test.com")
    await _seed_acct(db, user.id, income=5000, spending=3000, balance=500)

    fake.push(FakeLLM.make_tool_call_response("run_recommendation", {"horizon_months": 60}))
    fake.push(FakeLLM.make_text_response(
        "Your emergency fund is too low. Build 3 months of expenses before investing."
    ))

    res = await client.post("/api/v1/advisor/message", json={
        "content": "I want to start investing",
    }, headers=_headers(user.id))
    assert res.status_code == 200

    session_res = await client.get(f"/api/v1/advisor/sessions/{res.json()['session_id']}", headers=_headers(user.id))
    messages = session_res.json()["messages"]
    tool_msgs = [m for m in messages if m["role"] == "tool"]
    assert len(tool_msgs) >= 1
    payload = tool_msgs[0]["tool_payload"]
    assert "allocation" not in payload
    assert "action_items" in payload
    assert len(payload["safety_warnings"]) > 0
