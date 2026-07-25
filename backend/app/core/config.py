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
    # Database
    # ==========================================================

    DATABASE_PROVIDER: str = "postgres"

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "enterprise_ai"
    DATABASE_USER: str = "enterprise_user"
    DATABASE_PASSWORD: str = "enterprise_password"

    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False

    # ==========================================================
    # Qdrant
    # ==========================================================

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_COLLECTION: str = "enterprise_ai"

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    # ==========================================================
    # Azure Blob Storage
    # ==========================================================

    AZURE_STORAGE_CONNECTION_STRING: str = ""
    AZURE_STORAGE_CONTAINER: str = "documents"

    # ==========================================================
    # Logging
    # ==========================================================

    LOG_LEVEL: str = "INFO"

    UPLOAD_DIRECTORY: str = "uploads"

    # ==========================================================
    # Vector Store
    # ==========================================================

    VECTOR_DB_PATH: str = "storage/vectorstore/faiss_index"

    @property
    def DATABASE_URL(self) -> str:
        return (
        f"postgresql+psycopg://"
        f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
        f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
        f"/{self.DATABASE_NAME}"
    )

@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    The settings object is created only once during the application's
    lifetime and reused everywhere.
    """
    return Settings()


settings = get_settings()
