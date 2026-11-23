from functools import lru_cache
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field,model_validator


class Settings(BaseSettings):
    """
    Centralized application configuration.

    Loads configuration from environment variables and the .env file.
    """

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )

    # ==========================================================
    # Application
    # ==========================================================
    APP_NAME: str = "Enterprise AI Platform"
    API_VERSION: str = "v1"
    ENVIRONMENT: str = "development"
    DEBUG: bool = False
    # ==========================================================
    # API Security
    # ==========================================================
    API_AUTH_ENABLED: bool = True
    API_KEY: str = ""

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
    # LLM Cost Observability
    # Prices are in USD per one million tokens.
    # Use None when pricing is not configured.
    # ==========================================================

    OPENAI_GPT_41_MINI_INPUT_PRICE_PER_MILLION: float | None = None
    OPENAI_GPT_41_MINI_OUTPUT_PRICE_PER_MILLION: float | None = None

    AZURE_OPENAI_INPUT_PRICE_PER_MILLION: float | None = None
    AZURE_OPENAI_OUTPUT_PRICE_PER_MILLION: float | None = None
    AZURE_OPENAI_API_VERSION: str = "2024-02-01"
    LLM_TIMEOUT_SECONDS: float = 60.0
    LLM_MAX_RETRIES: int = 2


    # ==========================================================
    # Database
    # ==========================================================

    DATABASE_PROVIDER: str = "postgres"

    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_NAME: str = "enterprise_ai"
    DATABASE_USER: str = "enterprise_user"
    DATABASE_PASSWORD: str = "enterprise_password"

    SQL_AGENT_DATABASE_USER: str = ""
    SQL_AGENT_DATABASE_PASSWORD: str = ""

    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 1800
    DATABASE_ECHO: bool = False
    SQL_MAX_RESULT_ROWS: int = Field(default=100, ge=1)
    SQL_QUERY_TIMEOUT_MS: int = Field(default=10000, ge=1)

    DOCUMENT_DATABASE_HOST: str = "localhost"
    DOCUMENT_DATABASE_PORT: int = 5432
    DOCUMENT_DATABASE_NAME: str = "enterprise_ai"
    DOCUMENT_DATABASE_USER: str = "enterprise_user"
    DOCUMENT_DATABASE_PASSWORD: str = "enterprise_password"


    # ==========================================================
    # Application Runtime Database
    # ==========================================================

    APP_DATABASE_HOST: str = "localhost"
    APP_DATABASE_PORT: int = 5432
    APP_DATABASE_NAME: str = "enterprise_ai"
    APP_DATABASE_USER: str = ""
    APP_DATABASE_PASSWORD: str = ""

    @property
    def APP_DATABASE_URL(self) -> str:
        from sqlalchemy.engine import URL

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.APP_DATABASE_USER,
            password=self.APP_DATABASE_PASSWORD,
            host=self.APP_DATABASE_HOST,
            port=self.APP_DATABASE_PORT,
            database=self.APP_DATABASE_NAME,
        ).render_as_string(hide_password=False)

    @property
    def DOCUMENT_DATABASE_URL(self) -> str:
        from sqlalchemy.engine import URL

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.DOCUMENT_DATABASE_USER,
            password=self.DOCUMENT_DATABASE_PASSWORD,
            host=self.DOCUMENT_DATABASE_HOST,
            port=self.DOCUMENT_DATABASE_PORT,
            database=self.DOCUMENT_DATABASE_NAME,
        ).render_as_string(hide_password=False)

    @property
    def SQL_AGENT_DATABASE_URL(self) -> str:
        from sqlalchemy.engine import URL

        has_user = bool(self.SQL_AGENT_DATABASE_USER)
        has_password = bool(self.SQL_AGENT_DATABASE_PASSWORD)

        if has_user != has_password:
            raise ValueError(
                "SQL_AGENT_DATABASE_USER and "
                "SQL_AGENT_DATABASE_PASSWORD must be set together."
            )

        if not has_user and self.ENVIRONMENT.lower() != "development":
            raise ValueError(
                "SQL Agent database credentials must be explicitly "
                "configured outside development."
            )

        username = (
            self.SQL_AGENT_DATABASE_USER
            if has_user
            else self.DATABASE_USER
        )
        password = (
            self.SQL_AGENT_DATABASE_PASSWORD
            if has_password
            else self.DATABASE_PASSWORD
        )

        return URL.create(
            drivername="postgresql+psycopg",
            username=username,
            password=password,
            host=self.DATABASE_HOST,
            port=self.DATABASE_PORT,
            database=self.DATABASE_NAME,
        ).render_as_string(hide_password=False)

    # ==========================================================
    # Qdrant
    # ==========================================================

    QDRANT_HOST: str = "localhost"
    QDRANT_PORT: int = 6333
    QDRANT_API_KEY: str = ""
    QDRANT_COLLECTION: str = "enterprise_ai"
    QDRANT_UPSERT_MAX_RETRIES: int = Field(default=3, ge=0, le=10)
    QDRANT_UPSERT_RETRY_BASE_DELAY_SECONDS: float = Field(
    default=0.5,
    gt=0,
    )

    VECTOR_DB: str = "qdrant"

    QDRANT_VECTOR_SIZE: int = 1536
    QDRANT_DISTANCE: str = "COSINE"

    DOCUMENT_SEARCH_LIMIT: int = 20
    DOCUMENT_MIN_SCORE: float = 0.35

    # ==========================================================
    # Redis
    # ==========================================================

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_PASSWORD: str = ""
    DOCUMENT_INDEX_LOCK_TTL_SECONDS: int = 3600
    DOCUMENT_INDEX_LOCK_RENEWAL_INTERVAL_SECONDS: int = 1200
    DOCUMENT_INDEXING_STALE_TIMEOUT_SECONDS: int = Field(
        default=3600, ge=1
    )

    # ==========================================================
    # Conversation Memory
    # ==========================================================

    MEMORY_PROVIDER: str = "local"
    MEMORY_MAX_MESSAGES: int = 10
    MEMORY_TTL_SECONDS: int = 86400
    MEMORY_MAX_CONVERSATIONS: int = 1000

    # ==========================================================
    # Rate Limiting
    # ==========================================================

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 20
    RATE_LIMIT_WINDOW_SECONDS: int = 60
    RATE_LIMIT_KEY_SECRET: str = ""

    # ==========================================================
    # Embedding Resilience
    # ==========================================================
    EMBEDDING_TIMEOUT_SECONDS: float = 30.0
    EMBEDDING_MAX_RETRIES: int = 2

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
    # Document Upload Security
    # ==========================================================

    MAX_UPLOAD_SIZE_MB: int = Field(default=10, gt=0)

    # ==========================================================
    # Vector Store
    # ==========================================================



    @property
    def DATABASE_URL(self) -> str:
        return (
        f"postgresql+psycopg://"
        f"{self.DATABASE_USER}:{self.DATABASE_PASSWORD}"
        f"@{self.DATABASE_HOST}:{self.DATABASE_PORT}"
        f"/{self.DATABASE_NAME}"
    )

    @model_validator(mode="after")
    def validate_production_security(self):
        # Validate memory configuration in every environment.
        if self.MEMORY_PROVIDER.lower() not in {"local", "redis"}:
            raise ValueError(
                "MEMORY_PROVIDER must be either 'local' or 'redis'."
            )

        if self.MEMORY_MAX_CONVERSATIONS < 1:
            raise ValueError("MEMORY_MAX_CONVERSATIONS must be positive.")

        if self.MEMORY_MAX_MESSAGES < 1:
            raise ValueError(
                "MEMORY_MAX_MESSAGES must be positive."
            )

        if self.MEMORY_TTL_SECONDS < 1:
            raise ValueError(
                "MEMORY_TTL_SECONDS must be positive."
            )

        if self.ENVIRONMENT.lower() != "production":
            return self
        if not self.APP_DATABASE_USER:
            raise ValueError("Production requires APP_DATABASE_USER.")

        if len(self.APP_DATABASE_PASSWORD) < 32:
            raise ValueError(
                "Production APP_DATABASE_PASSWORD must contain "
                "at least 32 characters."
            )

        if not self.SQL_AGENT_DATABASE_USER:
            raise ValueError(
                "Production requires SQL_AGENT_DATABASE_USER."
            )

        if len(self.SQL_AGENT_DATABASE_PASSWORD) < 32:
            raise ValueError(
                "Production SQL_AGENT_DATABASE_PASSWORD must contain "
                "at least 32 characters."
            )

        if self.APP_DATABASE_USER in {
            self.DATABASE_USER,
            self.DOCUMENT_DATABASE_USER,
        }:
            raise ValueError(
                "Application runtime must use a dedicated database user."
            )

        if self.SQL_AGENT_DATABASE_USER in {
            self.APP_DATABASE_USER,
            self.DOCUMENT_DATABASE_USER,
        }:
            raise ValueError(
                "SQL Agent must use a dedicated database user."
            )


        # Production must use persistent Redis memory.
        if self.MEMORY_PROVIDER.lower() != "redis":
            raise ValueError(
                "Production requires MEMORY_PROVIDER=redis."
            )

        if self.DEBUG:
            raise ValueError(
                "DEBUG must be disabled in production."
            )

        if not self.API_AUTH_ENABLED:
            raise ValueError(
                "API authentication must be enabled in production."
            )

        if len(self.QDRANT_API_KEY) < 32:
            raise ValueError(
                "Production QDRANT_API_KEY must contain at least 32 characters."
            )

        if len(self.REDIS_PASSWORD) < 32:
            raise ValueError(
                "Production REDIS_PASSWORD must contain at least 32 characters."
            )

        if len(self.API_KEY) < 32:
            raise ValueError(
                "Production API_KEY must contain at least 32 characters."
            )

        if not self.RATE_LIMIT_ENABLED:
            raise ValueError(
                "Rate limiting must be enabled in production."
            )

        if len(self.RATE_LIMIT_KEY_SECRET) < 32:
            raise ValueError(
                "Production RATE_LIMIT_KEY_SECRET must contain "
                "at least 32 characters."
            )

        if self.API_KEY == self.RATE_LIMIT_KEY_SECRET:
            raise ValueError(
                "API_KEY and RATE_LIMIT_KEY_SECRET must be different."
            )

        return self


@lru_cache
def get_settings() -> Settings:
    """
    Returns a cached Settings instance.

    The settings object is created only once during the application's
    lifetime and reused everywhere.
    """
    return Settings()


settings = get_settings()
