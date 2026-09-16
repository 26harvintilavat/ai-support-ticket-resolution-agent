from app.config import Settings


def test_settings_use_expected_defaults(monkeypatch) -> None:
    for variable in ("APP_NAME", "APP_VERSION", "APP_ENVIRONMENT"):
        monkeypatch.delenv(variable, raising=False)

    settings = Settings(_env_file=None)

    assert settings.name == "AI Support Ticket Resolution Agent"
    assert settings.version == "0.1.0"
    assert settings.environment == "development"


def test_settings_support_app_prefixed_environment_variables(monkeypatch) -> None:
    monkeypatch.setenv("APP_NAME", "Test Support Agent")
    monkeypatch.setenv("APP_VERSION", "9.9.9")
    monkeypatch.setenv("APP_ENVIRONMENT", "test")

    settings = Settings(_env_file=None)

    assert settings.name == "Test Support Agent"
    assert settings.version == "9.9.9"
    assert settings.environment == "test"
