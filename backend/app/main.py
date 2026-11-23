import asyncio
import logging
from app.core.logging import get_logger
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
from app.storage.database.connection import (
    dispose_database_engines,
    get_document_connection,
)
from app.repositories.document_repository import DocumentRepository
from app.services.document.document_index_recovery_service import (
    DocumentIndexRecoveryService,
)
from app.storage.database.providers.sqlite_provider import (
    dispose_sqlite_engine,
)
from app.storage.redis_client import dispose_redis_client

logger = get_logger(__name__)
def _run_document_index_recovery() -> None:
    """Run stale document recovery using a dedicated database session."""

    connection = None

    try:
        connection = get_document_connection()
        repository = DocumentRepository(connection)
        service = DocumentIndexRecoveryService(repository)
        report = service.recover_stale_documents()

        logger.info(
            "Document indexing recovery completed: %s",
            report,
        )
    except Exception:
        logger.exception(
            "Document indexing recovery failed; application startup will continue."
        )
    finally:
        if connection is not None:
            try:
                connection.close()
            except Exception:
                logger.exception(
                    "Failed to close the document recovery database session."
                )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    """Manage shared application resource lifecycle."""

    try:
        await asyncio.to_thread(_run_document_index_recovery)
        yield
    finally:
        EmbeddingFactory.reset()
        dispose_redis_client()
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
