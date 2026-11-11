from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from app.ai.embedding_factory import EmbeddingFactory
from fastapi import FastAPI
from app.core.config import settings
from app.api.chat import router as chat_router
from app.api.exception_handlers import register_exception_handlers
from app.api.middleware import RequestContextMiddleware
from app.api.routes.document import router as document_router
from app.api.routes.health import router as health_router
from app.api.routes.metrics import router as metrics_router
from app.api.routes.usage_analytics import router as usage_analytics_router
from app.storage.database.connection import dispose_database_engines
from app.storage.database.providers.sqlite_provider import (
    dispose_sqlite_engine,
)
@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage shared application resource lifecycle."""

    try:
        yield
    finally:
        EmbeddingFactory.reset()
        dispose_database_engines()
        dispose_sqlite_engine()

is_production = settings.ENVIRONMENT.lower() == "production"

app = FastAPI(
    lifespan=lifespan,
    docs_url=None if is_production else "/docs",
    redoc_url=None if is_production else "/redoc",
    openapi_url=None if is_production else "/openapi.json",
)

app.include_router(health_router)
app.include_router(chat_router)
app.include_router(document_router)
app.add_middleware(RequestContextMiddleware)
register_exception_handlers(app)
app.include_router(usage_analytics_router)
app.include_router(metrics_router)


@app.get("/")
def home():
    return {"message": "Enterprise AI Platform Running"}
