"""
Test configuration for Saathi database tests.

Uses synchronous SQLAlchemy (psycopg2) for test simplicity.
Each test function gets a transactional session that is rolled back on teardown
— this provides perfect test isolation without needing to truncate tables.

Required env var: TEST_DATABASE_URL
Default: postgresql+psycopg2://saathi:saathi@localhost:5432/saathi_test_db
"""
import pytest
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.models.base import Base

# Import all models to register them with Base.metadata
import app.models  # noqa: F401

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL",
    "postgresql+psycopg2://saathi:saathi@localhost:5432/saathi_test_db",
)


@pytest.fixture(scope="session")
def engine():
    """Create the test database schema once per test session."""
    eng = create_engine(TEST_DATABASE_URL, echo=False)
    Base.metadata.create_all(eng)
    yield eng
    Base.metadata.drop_all(eng)
    eng.dispose()


@pytest.fixture(scope="function")
def db(engine) -> Session:
    """
    Provide a transactional test session.
    Each test runs inside a transaction that is rolled back at teardown,
    keeping tests fully isolated without truncating tables.
    """
    connection = engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection, autocommit=False, autoflush=True)
    session = SessionLocal()
    yield session
    session.close()
    transaction.rollback()
    connection.close()
