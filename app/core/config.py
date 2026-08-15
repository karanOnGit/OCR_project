from functools import lru_cache
from pathlib import Path
from typing import List, Any
from pydantic import field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "CaptureBackend OCR API"
    APP_ENV: str = "development"
    DEBUG: bool = True
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Storage settings
    UPLOAD_DIR: str = "uploads"
    MAX_FILE_SIZE_MB: int = 10
    ALLOWED_EXTENSIONS: set = {"jpg", "jpeg", "png", "webp"}
    ALLOWED_MIME_TYPES: set = {
        "image/jpeg",
        "image/png",
        "image/webp",
    }

    # Database settings
    DATABASE_URL: str = "sqlite:///./jobs.db"

    # Supabase settings
    SUPABASE_URL: str = ""
    SUPABASE_KEY: str = ""

    # OCR Settings
    OCR_ENGINE: str = "tesseract"
    TESSERACT_CMD: str = ""

    # Google Docs Settings
    GOOGLE_APPLICATION_CREDENTIALS: str = ""
    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""
    GOOGLE_REDIRECT_URI: str = ""
    GOOGLE_CLIENT_SECRETS_FILE: str = ""
    DEFAULT_GOOGLE_DOC_ID: str = "1Fv5GiS0iK3KJOQSHQB5gbASmaHEMZTUZo2TC_Fx14Hk"

    # CORS Settings
    CORS_ORIGINS: List[str] = ["*"]

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Any) -> List[str]:
        if isinstance(v, str):
            if v.strip() == "*":
                return ["*"]
            return [i.strip() for i in v.split(",") if i.strip()]
        elif isinstance(v, (list, tuple)):
            return list(v)
        return ["*"]

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def max_file_size_bytes(self) -> int:
        return self.MAX_FILE_SIZE_MB * 1024 * 1024

    @property
    def upload_path(self) -> Path:
        path = Path(self.UPLOAD_DIR)
        path.mkdir(parents=True, exist_ok=True)
        return path


@lru_cache()
def get_settings() -> Settings:
    return Settings()
