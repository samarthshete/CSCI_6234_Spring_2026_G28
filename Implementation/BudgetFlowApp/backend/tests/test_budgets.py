"""UC05 Budgets & BudgetItems: CRUD, validation, user isolation."""

import uuid

import pytest
from httpx import AsyncClient

API_BUDGETS = "/api/v1/budgets"
API_CATEGORIES = "/api/v1/categories"


async def _signup_and_login(client: AsyncClient, email: str) -> dict:
    await client.post("/api/v1/auth/signup", json={"email": email, "name": "T", "password": "SecurePass123!"})
    resp = await client.post("/api/v1/auth/login", data={"username": email, "password": "SecurePass123!"})
    return {"Authorization": f"Bearer {resp.json()['access_token']}"}


async def _create_category(client: AsyncClient, headers: dict, name: str = "Groceries") -> str:
    resp = await client.post(API_CATEGORIES, json={"name": name, "type": "expense"}, headers=headers)
    assert resp.status_code == 201
    return resp.json()["id"]


# ---- Tests ----------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_budget_and_get_includes_items(async_client: AsyncClient):
    email = f"bud_create_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(async_client, email)
    cat_id = await _create_category(async_client, headers)

    payload = {
        "name": "March Budget",
        "period_start": "2026-03-01",
        "period_end": "2026-03-31",
        "period_type": "monthly",
        "thresholds": [0.8, 0.9, 1.0],
        "items": [{"category_id": cat_id, "limit_amount": 500}],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers)
    assert resp.status_code == 201
    body = resp.json()
    assert body["name"] == "March Budget"
    assert body["period_type"] == "monthly"
    assert len(body["items"]) == 1
    assert body["items"][0]["category_id"] == cat_id
    assert float(body["items"][0]["limit_amount"]) == 500.0

    get_resp = await async_client.get(f"{API_BUDGETS}/{body['id']}", headers=headers)
    assert get_resp.status_code == 200
    assert len(get_resp.json()["items"]) == 1


@pytest.mark.asyncio
async def test_list_budgets_only_returns_current_user(async_client: AsyncClient):
    email_a = f"bud_la_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"bud_lb_{uuid.uuid4().hex[:8]}@test.com"
    headers_a = await _signup_and_login(async_client, email_a)
    headers_b = await _signup_and_login(async_client, email_b)

    payload = {
        "name": "A Budget",
        "period_start": "2026-03-01",
        "period_end": "2026-03-31",
        "items": [],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers_a)
    assert resp.status_code == 201

    list_a = await async_client.get(API_BUDGETS, headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1

    list_b = await async_client.get(API_BUDGETS, headers=headers_b)
    assert list_b.status_code == 200
    assert len(list_b.json()) == 0


@pytest.mark.asyncio
async def test_user_isolation_user_b_cannot_get_patch_delete_user_a_budget(async_client: AsyncClient):
    email_a = f"bud_iso_a_{uuid.uuid4().hex[:8]}@test.com"
    email_b = f"bud_iso_b_{uuid.uuid4().hex[:8]}@test.com"
    headers_a = await _signup_and_login(async_client, email_a)
    headers_b = await _signup_and_login(async_client, email_b)

    payload = {
        "name": "Private Budget",
        "period_start": "2026-04-01",
        "period_end": "2026-04-30",
        "items": [],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers_a)
    assert resp.status_code == 201
    budget_id = resp.json()["id"]

    get_resp = await async_client.get(f"{API_BUDGETS}/{budget_id}", headers=headers_b)
    assert get_resp.status_code == 404

    patch_resp = await async_client.patch(
        f"{API_BUDGETS}/{budget_id}", json={"name": "Hacked"}, headers=headers_b,
    )
    assert patch_resp.status_code == 404

    del_resp = await async_client.delete(f"{API_BUDGETS}/{budget_id}", headers=headers_b)
    assert del_resp.status_code == 404


@pytest.mark.asyncio
async def test_invalid_item_category_rejected(async_client: AsyncClient):
    email = f"bud_badcat_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(async_client, email)

    fake_cat_id = str(uuid.uuid4())
    payload = {
        "name": "Bad Cat Budget",
        "period_start": "2026-05-01",
        "period_end": "2026-05-31",
        "items": [{"category_id": fake_cat_id, "limit_amount": 100}],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers)
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "CATEGORY_NOT_FOUND"


@pytest.mark.asyncio
async def test_duplicate_category_in_items_rejected(async_client: AsyncClient):
    email = f"bud_dup_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(async_client, email)
    cat_id = await _create_category(async_client, headers)

    payload = {
        "name": "Dup Budget",
        "period_start": "2026-06-01",
        "period_end": "2026-06-30",
        "items": [
            {"category_id": cat_id, "limit_amount": 100},
            {"category_id": cat_id, "limit_amount": 200},
        ],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_period_end_before_start_rejected(async_client: AsyncClient):
    email = f"bud_per_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(async_client, email)

    payload = {
        "name": "Backwards Budget",
        "period_start": "2026-07-31",
        "period_end": "2026-07-01",
        "items": [],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers)
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_thresholds_validation_rejected(async_client: AsyncClient):
    email = f"bud_thr_{uuid.uuid4().hex[:8]}@test.com"
    headers = await _signup_and_login(async_client, email)

    # Unsorted thresholds
    payload = {
        "name": "Bad Thresholds",
        "period_start": "2026-08-01",
        "period_end": "2026-08-31",
        "thresholds": [0.9, 0.8, 1.0],
        "items": [],
    }
    resp = await async_client.post(API_BUDGETS, json=payload, headers=headers)
    assert resp.status_code == 422

    # Missing 1.0
    payload2 = {
        "name": "No Full",
        "period_start": "2026-08-01",
        "period_end": "2026-08-31",
        "thresholds": [0.5, 0.8],
        "items": [],
    }
    resp2 = await async_client.post(API_BUDGETS, json=payload2, headers=headers)
    assert resp2.status_code == 422
