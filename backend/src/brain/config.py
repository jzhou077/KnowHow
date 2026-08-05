from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]      # Path(__file__) is location of config.py / .resolve() makes it absolute / .parents[2] walks up to repo root

class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_file_encoding="utf-8",
        extra="ignore")

    notion_token: str

    neo4j_uri: str
    neo4j_user: str
    neo4j_password: str
    neo4j_database: str

    anthropic_api_key: str | None = None
    openai_api_key: str | None = None
    embedding_api_key: str | None = None
    notion_rate: float = 2.5
    notion_concurrency: int = 5

    graphiti_concurrency: int = 5

    tenant_id: str | None = None
    api_tokens: dict[str, str] = {}
    cors_origins: list[str] = ["http://localhost:5173"]

settings = Settings()