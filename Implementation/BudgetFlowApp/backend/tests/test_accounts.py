"""UC02 Manage Accounts: API tests including user isolation."""

import uuid

import pytest
from httpx import AsyncClient

API = "/api/v1/accounts"


async def _signup_and_login(async_client: AsyncClient, email: str, password: str, name: str = "Test User"):
    """Create a user and return auth headers."""
    await async_client.post(
        "/api/v1/auth/signup",
        json={"email": email, "name": name, "password": password},
    )
    resp = await async_client.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )
    assert resp.status_code == 200
    token = resp.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.mark.asyncio
async def test_create_account_and_list_only_user_accounts(async_client: AsyncClient):
    """Create accounts as one user and list returns only that user's accounts."""
    email = f"user_list_{uuid.uuid4().hex[:12]}@example.com"
    headers = await _signup_and_login(async_client, email, "SecurePass123!")

    r1 = await async_client.post(
        API, json={"type": "bank", "name": "Checking", "currency": "USD"}, headers=headers,
    )
    assert r1.status_code == 201

    r2 = await async_client.post(
        API, json={"type": "credit", "name": "Credit Card", "credit_limit": 5000}, headers=headers,
    )
    assert r2.status_code == 201

    list_resp = await async_client.get(API, headers=headers)
    assert list_resp.status_code == 200
    data = list_resp.json()
    assert len(data) == 2
    names = {a["name"] for a in data}
    assert names == {"Checking", "Credit Card"}


@pytest.mark.asyncio
async def test_user_isolation_user_a_cannot_access_user_b_account(async_client: AsyncClient):
    """User A creates an account; User B cannot GET, PATCH, or DELETE it (404)."""
    email_a = f"user_a_{uuid.uuid4().hex[:12]}@example.com"
    email_b = f"user_b_{uuid.uuid4().hex[:12]}@example.com"
    headers_a = await _signup_and_login(async_client, email_a, "SecurePass123!")
    headers_b = await _signup_and_login(async_client, email_b, "SecurePass123!")

    create_resp = await async_client.post(
        API, json={"type": "bank", "name": "A's Account"}, headers=headers_a,
    )
    assert create_resp.status_code == 201
    account_id = create_resp.json()["id"]

    assert (await async_client.get(f"{API}/{account_id}", headers=headers_b)).status_code == 404
    assert (await async_client.patch(f"{API}/{account_id}", json={"name": "Hacked"}, headers=headers_b)).status_code == 404
    assert (await async_client.delete(f"{API}/{account_id}", headers=headers_b)).status_code == 404

    list_a = await async_client.get(API, headers=headers_a)
    assert list_a.status_code == 200
    assert len(list_a.json()) == 1


@pytest.mark.asyncio
async def test_invalid_account_type_rejected(async_client: AsyncClient):
    """Creating an account with invalid type returns 422."""
    email = f"user_invalid_{uuid.uuid4().hex[:12]}@example.com"
    headers = await _signup_and_login(async_client, email, "SecurePass123!")
    r = await async_client.post(
        API, json={"type": "invalid_type", "name": "Bad Account"}, headers=headers,
    )
    assert r.status_code == 422


@pytest.mark.asyncio
async def test_update_account(async_client: AsyncClient):
    """Update an account and verify changes."""
    email = f"user_upd_{uuid.uuid4().hex[:12]}@example.com"
    headers = await _signup_and_login(async_client, email, "SecurePass123!")
    create_resp = await async_client.post(
        API, json={"type": "bank", "name": "Original Name", "currency": "USD"}, headers=headers,
    )
    assert create_resp.status_code == 201
    account_id = create_resp.json()["id"]

    patch_resp = await async_client.patch(
        f"{API}/{account_id}", json={"name": "Updated Name", "balance": "100.50"}, headers=headers,
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["name"] == "Updated Name"
    assert float(data["balance"]) == 100.50


@pytest.mark.asyncio
async def test_delete_account(async_client: AsyncClient):
    """Delete an account and verify it is gone."""
    email = f"user_del_{uuid.uuid4().hex[:12]}@example.com"
    headers = await _signup_and_login(async_client, email, "SecurePass123!")
    create_resp = await async_client.post(
        API, json={"type": "investment", "name": "To Delete", "broker_name": "Acme"}, headers=headers,
    )
    assert create_resp.status_code == 201
    account_id = create_resp.json()["id"]

    assert (await async_client.delete(f"{API}/{account_id}", headers=headers)).status_code == 204
    assert (await async_client.get(f"{API}/{account_id}", headers=headers)).status_code == 404
