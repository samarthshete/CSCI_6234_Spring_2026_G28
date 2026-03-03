"""UC07 Analytics: summary, trends, budget-vs-actual, user isolation, filters."""

import io
import uuid

import pytest
from httpx import AsyncClient

API_ACCOUNTS = "/api/v1/accounts"
API_CATEGORIES = "/api/v1/categories"
API_TRANSACTIONS = "/api/v1/transactions"
API_IMPORT = "/api/v1/transactions/import"
API_BUDGETS = "/api/v1/budgets"
API_ANALYTICS = "/api/v1/analytics"


async def _signup_and_login(client: AsyncClient, email: str) -> dict:
    await client.post("/api/v1/auth/signup", json={"email": email, "name": "T", "password": "SecurePass123!"})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": "SecurePass123!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _create_account(client: AsyncClient, headers: dict) -> str:
    resp = await client.post(API_ACCOUNTS, json={"type": "bank", "name": "Checking"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


async def _create_category(client: AsyncClient, headers: dict, name: str = "Food") -> str:
    resp = await client.post(API_CATEGORIES, json={"name": name, "type": "expense"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


def _csv_file(content: str, filename: str = "import.csv"):
    return {"file": (filename, io.BytesIO(content.encode()), "text/csv")}


async def _import_and_categorize(client, headers, acct_id, cat_id, csv_content):
    resp = await client.post(
        API_IMPORT,
        data={"account_id": acct_id},
        files=_csv_file(csv_content),
        headers=headers,
    )
    assert resp.status_code == 202
    tx_resp = await client.get(API_TRANSACTIONS, params={"account_id": acct_id}, headers=headers)
    for tx in tx_resp.json():
        if tx["category_id"] is None:
            await client.post(
                f"{API_TRANSACTIONS}/{tx['id']}/categorize",
                json={"category_id": cat_id},
                headers=headers,
            )


async def _setup_user_with_data(client: AsyncClient, email_prefix: str):
    """Create user, account, category, import 3 transactions across 2 months, categorize them."""
    email = f"{email_prefix}_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(client, email)
    acct_id = await _create_account(client, headers)
    cat_id = await _create_category(client, headers)

    csv = (
        "posted_date,amount,description\n"
        "2026-03-05,-50.00,Lunch\n"
        "2026-03-20,-30.00,Snacks\n"
        "2026-04-10,-20.00,Coffee\n"
    )
    await _import_and_categorize(client, headers, acct_id, cat_id, csv)
    return headers, acct_id, cat_id


# ---- Tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_summary_returns_correct_totals(async_client: AsyncClient):
    headers, acct_id, cat_id = await _setup_user_with_data(async_client, "an_sum")

    resp = await async_client.get(f"{API_ANALYTICS}/summary", headers=headers)
    assert resp.status_code == 200
    body = resp.json()
    assert float(body["total_spending"]) == 100.0
    assert len(body["by_category"]) >= 1
    cat_total = next(c for c in body["by_category"] if c["category_id"] == cat_id)
    assert float(cat_total["total"]) == 100.0
    assert len(body["by_account"]) == 1
    assert float(body["by_account"][0]["total"]) == 100.0


@pytest.mark.asyncio
async def test_trends_group_by_month(async_client: AsyncClient):
    headers, _, _ = await _setup_user_with_data(async_client, "an_trend")

    resp = await async_client.get(
        f"{API_ANALYTICS}/trends",
        params={"date_from": "2026-03-01", "date_to": "2026-04-30", "group_by": "month"},
        headers=headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 2
    march = next(d for d in data if d["period"].startswith("2026-03"))
    april = next(d for d in data if d["period"].startswith("2026-04"))
    assert float(march["total"]) == 80.0
    assert float(april["total"]) == 20.0


@pytest.mark.asyncio
async def test_budget_vs_actual_percent_correct(async_client: AsyncClient):
    headers, acct_id, cat_id = await _setup_user_with_data(async_client, "an_bva")

    budget_resp = await async_client.post(API_BUDGETS, json={
        "name": "March",
        "period_start": "2026-03-01",
        "period_end": "2026-03-31",
        "thresholds": [0.8, 1.0],
        "items": [{"category_id": cat_id, "limit_amount": 100}],
    }, headers=headers)
    assert budget_resp.status_code == 201
    budget_id = budget_resp.json()["id"]

    resp = await async_client.get(
        f"{API_ANALYTICS}/budget-vs-actual",
        params={"budget_id": budget_id},
        headers=headers,
    )
    assert resp.status_code == 200
    rows = resp.json()
    assert len(rows) == 1
    assert rows[0]["category_id"] == cat_id
    assert float(rows[0]["limit_amount"]) == 100.0
    assert float(rows[0]["spent_amount"]) == 80.0
    assert float(rows[0]["percent"]) == 0.8


@pytest.mark.asyncio
async def test_user_isolation(async_client: AsyncClient):
    headers_a, _, _ = await _setup_user_with_data(async_client, "an_iso_a")

    email_b = f"an_iso_b_{uuid.uuid4().hex[:8]}@test.com"
    headers_b = await _signup_and_login(async_client, email_b)

    resp_a = await async_client.get(f"{API_ANALYTICS}/summary", headers=headers_a)
    assert float(resp_a.json()["total_spending"]) == 100.0

    resp_b = await async_client.get(f"{API_ANALYTICS}/summary", headers=headers_b)
    assert float(resp_b.json()["total_spending"]) == 0


@pytest.mark.asyncio
async def test_filters_work(async_client: AsyncClient):
    headers, acct_id, cat_id = await _setup_user_with_data(async_client, "an_filt")

    resp = await async_client.get(
        f"{API_ANALYTICS}/summary",
        params={"date_from": "2026-03-01", "date_to": "2026-03-31"},
        headers=headers,
    )
    assert resp.status_code == 200
    assert float(resp.json()["total_spending"]) == 80.0

    resp2 = await async_client.get(
        f"{API_ANALYTICS}/summary",
        params={"date_from": "2026-04-01", "date_to": "2026-04-30"},
        headers=headers,
    )
    assert float(resp2.json()["total_spending"]) == 20.0

    resp3 = await async_client.get(
        f"{API_ANALYTICS}/summary",
        params={"category_ids": cat_id},
        headers=headers,
    )
    assert float(resp3.json()["total_spending"]) == 100.0

    resp4 = await async_client.get(
        f"{API_ANALYTICS}/summary",
        params={"account_ids": acct_id},
        headers=headers,
    )
    assert float(resp4.json()["total_spending"]) == 100.0
