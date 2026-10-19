"""Integration tests using an isolated PostgreSQL database."""

import asyncio
import os
from math import sqrt

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import text
from sqlalchemy.engine import make_url
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

import app.main as main_module
from app import database


@pytest.fixture(scope="module")
def test_database_url() -> str:
    """Require an explicitly configured isolated test database."""

    raw_url = os.environ.get("TEST_DATABASE_URL")

    if not raw_url:
        pytest.skip("Set TEST_DATABASE_URL to enable PostgreSQL integration tests.")

    parsed_url = make_url(raw_url)

    if parsed_url.drivername != "postgresql+asyncpg" or parsed_url.database != "support_agent_test":
        pytest.fail("Integration tests require a PostgreSQL database named support_agent_test.")

    return raw_url


@pytest.mark.integration
def test_pgvector_extension_and_migration(
    test_database_url: str,
) -> None:
    """Confirm pgvector and the initial Alembic migration exist."""

    async def verify() -> tuple[bool, str | None]:
        engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
        )

        try:
            async with engine.connect() as connection:
                extension_enabled = await connection.scalar(
                    text("SELECT EXISTS (SELECT 1 FROM pg_extension WHERE extname = 'vector')")
                )

                revision = await connection.scalar(text("SELECT version_num FROM alembic_version"))

                return bool(extension_enabled), revision

        finally:
            await engine.dispose()

    extension_enabled, revision = asyncio.run(verify())

    assert extension_enabled is True
    assert revision == "0002_knowledge"


@pytest.mark.integration
def test_pgvector_distance_query(
    test_database_url: str,
) -> None:
    """Confirm PostgreSQL can execute vector distance queries."""

    async def verify() -> float:
        engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
        )

        try:
            async with engine.connect() as connection:
                result = await connection.scalar(
                    text("SELECT CAST('[1,0,0]' AS vector) <-> CAST('[0,1,0]' AS vector)")
                )

                assert result is not None
                return float(result)

        finally:
            await engine.dispose()

    distance = asyncio.run(verify())

    assert distance == pytest.approx(sqrt(2))


@pytest.mark.integration
def test_database_session_against_postgres(
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirm the application session dependency works."""

    async def verify() -> None:
        engine = create_async_engine(
            test_database_url,
            poolclass=NullPool,
        )

        session_factory = async_sessionmaker(
            bind=engine,
            expire_on_commit=False,
        )

        monkeypatch.setattr(
            database,
            "async_session_factory",
            session_factory,
        )

        try:
            async for session in database.get_database_session():
                result = await session.scalar(text("SELECT 1"))
                assert result == 1

        finally:
            await engine.dispose()

    asyncio.run(verify())


@pytest.mark.integration
def test_readiness_against_real_postgres(
    test_database_url: str,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Confirm readiness succeeds with real PostgreSQL."""

    test_engine = create_async_engine(
        test_database_url,
        poolclass=NullPool,
    )

    monkeypatch.setattr(
        database,
        "engine",
        test_engine,
    )

    monkeypatch.setattr(
        main_module,
        "check_database_connection",
        database.check_database_connection,
    )

    try:
        with TestClient(main_module.app) as client:
            health_response = client.get("/health")
            ready_response = client.get("/ready")

    finally:
        asyncio.run(test_engine.dispose())

    assert health_response.status_code == 200
    assert health_response.json() == {"status": "ok"}

    assert ready_response.status_code == 200
    assert ready_response.json() == {"status": "ready"}
