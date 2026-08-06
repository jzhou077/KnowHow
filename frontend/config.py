from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[1]      # Path(__file__) is location of config.py / .resolve() makes it absolute / .parents[2] walks up to repo root

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore")
    
    api_tokens: dict[str, str] = {}
    dev_token: str | None = None

    backend_url: str | None = None

settings = Settings()