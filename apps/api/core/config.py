from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_env: str = "development"
    demo_auth_enabled: bool = False
    demo_user_id: str = "demo-student"
    database_url: str = "postgresql+psycopg://postgres:postgres@db:5432/maie6000c"
    upload_dir: str = "/tmp/nourishloop-photo-reviews"
    cors_origin: str = "http://localhost:3000"
    explanation_provider: Literal["deterministic", "openrouter"] = "deterministic"
    openrouter_api_key: SecretStr | None = None
    openrouter_model: str = "nvidia/nemotron-3.5-super-vl:free"
    openrouter_timeout_seconds: float = Field(default=20.0, gt=0, le=120)
    deepseek_api_key: SecretStr | None = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-chat"
    deepseek_timeout_seconds: float = Field(default=25.0, gt=0, le=120)
    usda_api_key: SecretStr = SecretStr("DEMO_KEY")
    usda_timeout_seconds: float = Field(default=12.0, gt=0, le=60)
    worker_poll_seconds: float = Field(default=2.0, gt=0, le=60)
    worker_lease_seconds: int = Field(default=120, ge=10, le=3600)

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
