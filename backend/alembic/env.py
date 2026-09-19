"""Alembic migration environment for Saathi.

Uses a SYNCHRONOUS psycopg2 connection for running migrations.
This avoids asyncpg DDL limitations (especially around enum type creation).
The application itself still uses async SQLAlchemy + asyncpg at runtime.

DATABASE_URL is read from the DATABASE_URL environment variable.
No credentials are hardcoded here.
"""
import os
import re
from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# Import all models so SQLAlchemy metadata is fully populated.
import app.models  # noqa: F401
from app.models.base import Base

from dotenv import load_dotenv

load_dotenv()
config = context.config
database_url = os.environ.get("DATABASE_URL")
if not database_url:
    try:
        from app.config import get_settings
        database_url = get_settings().DATABASE_URL
    except Exception:
        pass
if not database_url:
    raise RuntimeError(
        "DATABASE_URL environment variable is not set. "
        "Set it before running alembic commands."
    )
# Replace asyncpg driver with psycopg2 for synchronous Alembic use
sync_url = re.sub(r"^postgresql\+asyncpg://", "postgresql+psycopg2://", database_url)
config.set_main_option("sqlalchemy.url", sync_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live database using psycopg2."""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
