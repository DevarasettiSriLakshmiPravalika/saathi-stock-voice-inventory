"""
API test fixtures for Saathi backend — Phases 2-16.

Uses httpx AsyncClient with ASGITransport for in-process testing.
Uses a separate saathi_api_test_db PostgreSQL database.
Test isolation via table truncation between tests.
"""
import asyncio
import os
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker

# Override env before importing app — must happen before any app imports
os.environ["DATABASE_URL"] = "postgresql+asyncpg://saathi:saathi@localhost:5432/saathi_api_test_db"
os.environ["SECRET_KEY"] = "test-secret-key-32-chars-minimum-!!"
os.environ["SAATHI_OTP_DEV_MODE"] = "true"
os.environ["SAATHI_OTP_DEV_CODE"] = "123456"
os.environ["SAATHI_ASR_PROVIDER"] = "mock"
os.environ["SAATHI_LLM_PROVIDER"] = "mock"
os.environ["SAATHI_SPEAKER_PROVIDER"] = "mock"

# Must import after env is set
from app.config import get_settings  # noqa: E402
from app.database import get_db  # noqa: E402
import app.models  # noqa: F401, E402 — register all models
from app.models.base import Base  # noqa: E402


TEST_DB_URL = "postgresql+asyncpg://saathi:saathi@localhost:5432/saathi_api_test_db"

# Tables to truncate between tests (leaf tables first to respect FK constraints)
_TRUNCATE_TABLES = [
    "audit_logs",
    "trust_history",
    "statement_processing",
    "reviews",
    "statements",
    "vocabulary_entries",
    "baselines",
    "voice_profiles",
    "shop_members",
    "products",
    "shops",
    "users",
]


async def _setup_schema(url: str) -> None:
    """Create test schema from models."""
    eng = create_async_engine(url, echo=False)
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await eng.dispose()


async def _truncate_all(url: str) -> None:
    """Truncate all tables for test isolation."""
    eng = create_async_engine(url, echo=False)
    async with eng.begin() as conn:
        for table in _TRUNCATE_TABLES:
            await conn.execute(text(f'TRUNCATE TABLE "{table}" RESTART IDENTITY CASCADE'))
    await eng.dispose()


def pytest_configure(config):
    """Set up the test database schema once at session start (sync hook)."""
    asyncio.run(_setup_schema(TEST_DB_URL))


@pytest_asyncio.fixture(scope="function")
async def client():
    """Provide an async test client wired to the test database."""
    from app.main import app

    # Create a fresh engine per test to avoid event loop conflicts
    eng = create_async_engine(TEST_DB_URL, echo=False)
    session_factory = async_sessionmaker(eng, class_=AsyncSession, expire_on_commit=False)

    async def override_get_db():
        async with session_factory() as session:
            try:
                yield session
            finally:
                await session.close()

    app.dependency_overrides[get_db] = override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()
    await eng.dispose()

    # Truncate all tables after each test for clean state
    await _truncate_all(TEST_DB_URL)


# ---- Shared helpers ----------------------------------------------------------

async def register_and_login(client: AsyncClient, name: str, phone: str) -> dict:
    """Register a user, verify OTP, and return auth data."""
    r = await client.post("/api/v1/auth/register", json={"name": name, "phone": phone})
    assert r.status_code == 200, r.text
    otp = r.json()["data"].get("dev_otp", "123456")

    r = await client.post("/api/v1/auth/verify", json={"phone": phone, "otp": otp})
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    return {
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "user": data["user"],
        "headers": {"Authorization": f"Bearer {data['access_token']}"},
    }


async def create_shop_for_user(client: AsyncClient, headers: dict, name: str = "Test Shop") -> dict:
    """Create a shop and return its data."""
    r = await client.post("/api/v1/shops", json={"name": name}, headers=headers)
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def create_product_for_shop(
    client: AsyncClient, headers: dict, shop_id: str,
    name: str = "Rice", default_unit: str = "bag"
) -> dict:
    """Create a product in a shop and return its data."""
    r = await client.post(
        f"/api/v1/shops/{shop_id}/products",
        json={"name": name, "default_unit": default_unit},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]


async def set_baseline_for_product(
    client: AsyncClient, headers: dict, shop_id: str,
    product_id: str, quantity: float = 100.0, unit: str = "bag"
) -> dict:
    """Set baseline stock for a product."""
    r = await client.post(
        f"/api/v1/shops/{shop_id}/baseline",
        json={"product_id": product_id, "quantity": quantity, "unit": unit},
        headers=headers,
    )
    assert r.status_code == 200, r.text
    return r.json()["data"]
