"""Application settings, loaded from environment / .env."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+asyncpg://homeenergy:homeenergy@db:5432/homeenergy"
    ingest_api_key: str = "dev-ingest-key"
    query_api_key: str = "dev-query-key"


settings = Settings()
