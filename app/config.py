from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from defaults, environment variables, or .env."""

    name: str = "AI Support Ticket Resolution Agent"
    version: str = "0.1.0"
    environment: str = "development"

    database_url: str = "postgresql+asyncpg://postgres:postgres@127.0.0.1:5432/support_agent"

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Return the cached application settings."""

    return Settings()
