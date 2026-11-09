"""Application configuration.

All runtime configuration is environment-driven. The defaults are safe for local
development and deliberately avoid requiring any paid service.
"""

from __future__ import annotations

from functools import lru_cache

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    app_name: str = "Roleprint API"
    app_version: str = "2.0.0"
    environment: str = "development"
    debug: bool = False

    # Comma-separated list. Keep local Vite origins by default.
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    database_url: str = "sqlite:///./roleprint.db"
    auto_create_tables: bool = True

    jwt_secret: str = "dev-only-change-this-secret"
    jwt_algorithm: str = "HS256"
    access_token_minutes: int = 30
    refresh_token_days: int = 14

    max_upload_bytes: int = 10 * 1024 * 1024
    max_pdf_pages: int = 60
    max_resume_chars: int = 200_000
    max_job_chars: int = 100_000

    rate_limit_requests: int = 120
    rate_limit_window_seconds: int = 60
    enable_rate_limit: bool = True

    log_level: str = "INFO"

    # Optional AI rewriting. Disabled unless a key exists AND consent is explicit.
    openai_api_key: str | None = None
    openai_model: str = "gpt-4o-mini"
    enable_openai_rewriter: bool = False
    openai_consent_default: bool = False

    # Optional local semantic model. Never downloads implicitly.
    enable_semantic_matching: bool = True

    # Optional OCR. Requires pytesseract + the tesseract binary.
    enable_ocr: bool = False

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]

    @property
    def is_production(self) -> bool:
        return self.environment.lower() in {"production", "prod"}

    @property
    def using_default_secret(self) -> bool:
        return self.jwt_secret == "dev-only-change-this-secret"

    @property
    def openai_enabled(self) -> bool:
        return bool(self.enable_openai_rewriter and self.openai_api_key)


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()


def reset_settings_cache() -> None:
    """Used by tests that need to change environment variables."""
    get_settings.cache_clear()
