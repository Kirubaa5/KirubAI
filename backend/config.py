from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    # App
    APP_NAME: str = "KirubAI API"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str = "postgresql://kirubai:kirubai@localhost:5432/kirubai"

    # JWT
    JWT_SECRET_KEY: str = "dev-secret-change-in-production-use-strong-random-key"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:5173", "http://localhost:3000"]

    # LLM
    LLM_PROVIDER: str = "mock"  # mock | openai | gemini | openrouter
    OPENAI_API_KEY: str = ""
    GEMINI_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=True, extra="ignore")


settings = Settings()
