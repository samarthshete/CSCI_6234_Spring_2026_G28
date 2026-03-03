import pytest
from httpx import AsyncClient
import uuid

@pytest.mark.asyncio
async def test_signup_and_login(async_client: AsyncClient):
    unique_email = f"testuser_{uuid.uuid4().hex[:8]}@example.com"
    password = "SecurePassword123!"
    name = "Test User"
    
    # 1. Test Signup
    signup_data = {
        "email": unique_email,
        "name": name,
        "password": password
    }
    signup_resp = await async_client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_resp.status_code == 200, signup_resp.text
    user_data = signup_resp.json()
    assert user_data["email"] == unique_email
    assert user_data["name"] == name
    assert "id" in user_data
    
    # 2. Test Login
    login_data = {"username": unique_email, "password": password}
    login_resp = await async_client.post("/api/v1/auth/login", data=login_data)
    assert login_resp.status_code == 200, login_resp.text
    token_data = login_resp.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"
    
    # 3. Test duplicate signup fails
    signup_dup_resp = await async_client.post("/api/v1/auth/signup", json=signup_data)
    assert signup_dup_resp.status_code == 400
