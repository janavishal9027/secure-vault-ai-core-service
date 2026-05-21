from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    chat_provider: Literal["gemini", "openai"] = "openai"
    embed_provider: Literal["gemini", "openai"] = "gemini"

    gemini_api_key: str = ""
    gemini_chat_model: str = "gemini-2.5-flash"
    gemini_embed_model: str = "gemini-embedding-001"

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    openai_chat_model: str = "gpt-4o-mini"
    openai_embed_model: str = "text-embedding-3-small"
    openai_app_title: str = "secure-vault"

    embed_dimensions: int = 768

    postgres_host: str
    postgres_port: int
    postgres_db: str
    postgres_user: str
    postgres_password: str
    postgres_schema: str

    app_host: str = "0.0.0.0"
    app_port: int = 8001

    jwt_secret: str = ""
    jwt_algorithm: str = "HS256"
    cors_allowed_origins: str = "http://localhost:3000"

    search_default_top_k: int = 5
    search_max_top_k: int = 20
    chat_history_window: int = 10
    embed_chunk_size_chars: int = 1500

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+asyncpg://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )


settings = Settings()
