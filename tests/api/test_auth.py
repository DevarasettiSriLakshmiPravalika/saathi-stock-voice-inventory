"""
Authentication API tests — Phase 2.

Tests:
- Registration (POST /api/v1/auth/register)
- OTP verification (POST /api/v1/auth/verify)
- Token refresh (POST /api/v1/auth/refresh)
- Current user (GET /api/v1/users/me)
- Invalid token rejection
- Role enforcement
"""
import pytest
from httpx import AsyncClient

from tests.api.conftest import register_and_login


class TestRegistration:

    @pytest.mark.asyncio
    async def test_register_new_owner(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/register",
            json={"name": "Test Owner", "phone": "+911111111001"},
        )
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "dev_otp" in data["data"]  # dev mode returns OTP

    @pytest.mark.asyncio
    async def test_register_invalid_phone_format(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/register",
            json={"name": "Bad Phone", "phone": "9876543210"},
        )
        assert r.status_code == 422  # Pydantic validation error

    @pytest.mark.asyncio
    async def test_register_duplicate_verified_phone(self, client: AsyncClient):
        phone = "+911111111002"
        # Register and verify
        await register_and_login(client, "User One", phone)
        # Try to register same phone again
        r = await client.post(
            "/api/v1/auth/register",
            json={"name": "User Two", "phone": phone},
        )
        assert r.status_code == 409
        assert r.json()["error"]["code"] == "DUPLICATE_PHONE"


class TestLoginEndpoint:

    @pytest.mark.asyncio
    async def test_login_existing_user(self, client: AsyncClient):
        phone = "+911111111050"
        # First register
        await register_and_login(client, "Login User", phone)
        # Now request login OTP
        r = await client.post("/api/v1/auth/login", json={"phone": phone})
        assert r.status_code == 200
        data = r.json()
        assert data["success"] is True
        assert "dev_otp" in data["data"]
        assert data["data"]["name"] == "Login User"

    @pytest.mark.asyncio
    async def test_login_unregistered_user(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/login", json={"phone": "+919999999999"})
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "USER_NOT_FOUND"

    @pytest.mark.asyncio
    async def test_login_invalid_phone_format(self, client: AsyncClient):
        r = await client.post("/api/v1/auth/login", json={"phone": "12345"})
        assert r.status_code == 422


class TestVerification:

    @pytest.mark.asyncio
    async def test_verify_correct_otp(self, client: AsyncClient):
        phone = "+911111111003"
        r = await client.post(
            "/api/v1/auth/register",
            json={"name": "Verify Test", "phone": phone},
        )
        otp = r.json()["data"]["dev_otp"]

        r = await client.post(
            "/api/v1/auth/verify",
            json={"phone": phone, "otp": otp},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["is_phone_verified"] is True

    @pytest.mark.asyncio
    async def test_verify_wrong_otp(self, client: AsyncClient):
        phone = "+911111111004"
        await client.post(
            "/api/v1/auth/register",
            json={"name": "Wrong OTP Test", "phone": phone},
        )

        r = await client.post(
            "/api/v1/auth/verify",
            json={"phone": phone, "otp": "999999"},
        )
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "AUTH_INVALID"

    @pytest.mark.asyncio
    async def test_verify_unregistered_phone(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/verify",
            json={"phone": "+919000000000", "otp": "123456"},
        )
        assert r.status_code == 404
        assert r.json()["error"]["code"] == "NOT_FOUND"


class TestTokenRefresh:

    @pytest.mark.asyncio
    async def test_refresh_valid_token(self, client: AsyncClient):
        auth = await register_and_login(client, "Refresh User", "+911111111005")
        r = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth["refresh_token"]},
        )
        assert r.status_code == 200
        data = r.json()["data"]
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Token must be a valid JWT (three dot-separated parts)
        assert data["access_token"].count(".") == 2

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client: AsyncClient):
        r = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"},
        )
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "AUTH_INVALID"

    @pytest.mark.asyncio
    async def test_refresh_using_access_token_fails(self, client: AsyncClient):
        auth = await register_and_login(client, "Refresh Test 2", "+911111111006")
        # Try to use access token as refresh token — should fail
        r = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": auth["access_token"]},
        )
        assert r.status_code == 401


class TestCurrentUser:

    @pytest.mark.asyncio
    async def test_get_current_user(self, client: AsyncClient):
        auth = await register_and_login(client, "Me Test", "+911111111007")
        r = await client.get("/api/v1/users/me", headers=auth["headers"])
        assert r.status_code == 200
        data = r.json()["data"]
        assert data["phone"] == "+911111111007"
        assert data["name"] == "Me Test"
        assert data["is_phone_verified"] is True

    @pytest.mark.asyncio
    async def test_get_current_user_without_token(self, client: AsyncClient):
        r = await client.get("/api/v1/users/me")
        assert r.status_code == 401  # No credentials provided

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token(self, client: AsyncClient):
        r = await client.get(
            "/api/v1/users/me",
            headers={"Authorization": "Bearer invalid.token.xyz"},
        )
        assert r.status_code == 401
        assert r.json()["error"]["code"] == "AUTH_INVALID"

    @pytest.mark.asyncio
    async def test_health_check(self, client: AsyncClient):
        r = await client.get("/api/v1/health")
        assert r.status_code == 200
        assert r.json() == {"success": True, "status": "healthy"}
