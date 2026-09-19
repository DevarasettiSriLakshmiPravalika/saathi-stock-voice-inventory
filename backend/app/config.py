"""
Saathi application configuration — all settings from environment variables.
No secrets are hardcoded here.
"""
from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str

    # Security — do not expose via API
    SECRET_KEY: str

    # Application
    DEBUG: bool = False
    ALLOWED_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    # JWT
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # OTP
    SAATHI_OTP_DEV_MODE: bool = True
    SAATHI_OTP_DEV_CODE: str = "123456"

    # Provider selection
    SAATHI_ASR_PROVIDER: str = "mock"
    SAATHI_LLM_PROVIDER: str = "mock"
    SAATHI_SPEAKER_PROVIDER: str = "mock"

    # AI Credentials (optional, for real providers)
    OPENAI_API_KEY: Optional[str] = None
    GROQ_API_KEY: Optional[str] = None
    GROQ_ASR_MODEL: str = "whisper-large-v3-turbo"
    HUGGINGFACE_TOKEN: Optional[str] = None

    # Audio limits
    MAX_AUDIO_SIZE_MB: int = 10

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def allowed_origins_list(self) -> List[str]:
        """Return ALLOWED_ORIGINS as a parsed list."""
        return [origin.strip() for origin in self.ALLOWED_ORIGINS.split(",") if origin.strip()]


@lru_cache()
def get_settings() -> Settings:
    return Settings()
