import asyncio

from app import database


class FakeConnection:
    async def execute(self, statement) -> None:
        assert str(statement) == "SELECT 1"


class SuccessfulConnectionContext:
    async def __aenter__(self) -> FakeConnection:
        return FakeConnection()

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


class SuccessfulEngine:
    def connect(self) -> SuccessfulConnectionContext:
        return SuccessfulConnectionContext()


class FailedConnectionContext:
    async def __aenter__(self) -> None:
        raise OSError("PostgreSQL unavailable")

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        return None


class FailedEngine:
    def connect(self) -> FailedConnectionContext:
        return FailedConnectionContext()


def test_database_connection_returns_true_when_query_succeeds(monkeypatch) -> None:
    monkeypatch.setattr(database, "engine", SuccessfulEngine())

    result = asyncio.run(database.check_database_connection())

    assert result is True


def test_database_connection_returns_false_when_database_is_unavailable(
    monkeypatch,
) -> None:
    monkeypatch.setattr(database, "engine", FailedEngine())

    result = asyncio.run(database.check_database_connection())

    assert result is False
