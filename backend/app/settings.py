from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    ai_provider: str = Field(default="mock", alias="AI_PROVIDER")
    ai_api_key: str | None = Field(default=None, alias="AI_API_KEY")
    ai_base_url: str | None = Field(default=None, alias="AI_BASE_URL")
    ai_model: str | None = Field(default=None, alias="AI_MODEL")
    allowed_origins: str = Field(default="http://localhost:5173", alias="ALLOWED_ORIGINS")
    atlas_whatsapp_number: str = Field(default="51999999999", alias="ATLAS_WHATSAPP_NUMBER")
    max_upload_mb: int = Field(default=8, ge=1, le=20, alias="MAX_UPLOAD_MB")
    rate_limit_per_minute: int = Field(default=12, ge=1, le=120, alias="RATE_LIMIT_PER_MINUTE")

    @property
    def origins(self) -> list[str]:
        return [origin.strip() for origin in self.allowed_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()
