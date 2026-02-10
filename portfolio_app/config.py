"""Application configuration using Pydantic BaseSettings."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):  # type: ignore[misc]
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Database
    database_url: str = "postgresql://portfolio:portfolio_dev@localhost:5432/portfolio"
    postgres_user: str = "portfolio"
    postgres_password: str = "portfolio_dev"
    postgres_db: str = "portfolio"

    # Application
    dash_debug: bool = True
    secret_key: str = "change-me-in-production"

    # Logging
    log_level: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
