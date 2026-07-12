from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    APP_NAME: str = "Enterprise AI Platform"

    API_VERSION: str = "v1"

    ENVIRONMENT: str = "development"

    DEBUG: bool = True

    LLM_PROVIDER: str = "openai"

    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4.1-mini"

    AZURE_OPENAI_ENDPOINT: str = ""

    AZURE_OPENAI_API_KEY: str = ""

    AZURE_OPENAI_DEPLOYMENT: str = "gpt-4o"

    AZURE_OPENAI_EMBEDDING: str = "text-embedding-3-small"

    TEMPERATURE: float = 0

    MAX_TOKENS: int = 4000

    DATABASE_URL: str = "sqlite:///./enterprise.db"

    VECTOR_DB_PATH: str = "./app/vectorstore/faiss_index"

    LOG_LEVEL: str = "INFO"

    class Config:
        env_file = ".env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()