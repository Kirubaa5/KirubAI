import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import field_validator
from typing import List


def _normalize_database_url(url: str) -> str:
    """Normalize database URL for SQLAlchemy compatibility.

    Supabase and some providers use 'postgres://' which SQLAlchemy 2.x
    does not accept; it must be 'postgresql://'.
    """
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


class Settings(BaseSettings):
    # App
    APP_NAME: str = "KirubAI API"
    DEBUG: bool = False
    ENVIRONMENT: str = "production"  # development | testing | production

    # Database
    DATABASE_URL: str = "postgresql://kirubai:kirubai@localhost:5432/kirubai"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production-use-strong-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS — accepts a JSON list or comma-separated string from env
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM
    LLM_PROVIDER: str = "mock"  # mock | openai | gemini | openrouter
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    GEMINI_MODEL: str = "gemini-2.0-flash"
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors_origins(cls, v):  # noqa: N805
        """Accept comma-separated string from environment variables."""
        if isinstance(v, str):
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v

    @field_validator("DATABASE_URL", mode="after")
    @classmethod
    def normalize_db_url(cls, v):  # noqa: N805
        return _normalize_database_url(v)

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production" and not self.DEBUG

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()

# Runtime safety check: warn (but don't crash) if the default JWT secret is
# used outside of development/testing.
if settings.is_production and settings.JWT_SECRET_KEY == "dev-secret-change-in-production-use-strong-random-key":
    import warnings
    warnings.warn(
        "SECURITY WARNING: Using default JWT_SECRET_KEY in production. "
        "Set a strong, random JWT_SECRET_KEY environment variable.",
        stacklevel=1,
    )
