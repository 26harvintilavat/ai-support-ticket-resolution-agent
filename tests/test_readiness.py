from fastapi.testclient import TestClient

import app.main as main_module


def test_readiness_returns_ready_when_database_is_available(monkeypatch) -> None:
    async def database_available() -> bool:
        return True

    monkeypatch.setattr(
        main_module,
        "check_database_connection",
        database_available,
    )

    with TestClient(main_module.app) as client:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}


def test_readiness_returns_503_when_database_is_unavailable(monkeypatch) -> None:
    async def database_unavailable() -> bool:
        return False

    monkeypatch.setattr(
        main_module,
        "check_database_connection",
        database_unavailable,
    )

    with TestClient(main_module.app) as client:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json() == {"status": "not_ready"}
