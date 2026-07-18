from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Loads configuration from environment variables and the .env file.
    """

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "Enterprise AI Platform"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # ==========================================================
    # AI Configuration
    # ==========================================================
    LLM_PROVIDER: str = "openai"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"
    OPENAI_EMBEDDING_MODEL: str = "text-embedding-3-small"

    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"

    TEMPERATURE: float = 0.0
    MAX_TOKENS: int = 4000

    # ==========================================================
    # Storage
    # ==========================================================
    DATABASE_URL: str = "sqlite:///./enterprise.db"
    VECTOR_DB_PATH: str = "./app/storage/vectorstore/faiss_index"

    # ==========================================================
    # Logging
    # ==========================================================
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    The settings object is created only once during the application's
    lifetime and reused everywhere.
    """
    return Settings()


settings = get_settings()
