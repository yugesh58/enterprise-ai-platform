
from concurrent.futures import ThreadPoolExecutor
from typing import Callable

import redis
from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.core.config import settings
from app.storage.database.connection import (
    document_engine,
    sql_engine,
)
from app.storage.vectorstore.factory import VectorStoreFactory

router = APIRouter(tags=["Health"])


def _check_sql_database() -> None:
    with sql_engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _check_document_database() -> None:
    with document_engine.connect() as connection:
        connection.execute(text("SELECT 1"))


def _check_redis() -> None:
    client = redis.Redis(
        host=settings.REDIS_HOST,
        port=settings.REDIS_PORT,
        db=settings.REDIS_DB,
        socket_connect_timeout=2,
        socket_timeout=2,
        decode_responses=True,
    )
    try:
        if client.ping() is not True:
            raise RuntimeError("Redis ping failed")
    finally:
        client.close()



def _check_qdrant() -> None:
    provider = VectorStoreFactory.get_provider()
    provider.health_check()



def _run_check(check: Callable[[], None]) -> str:
    try:
        check()
        return "ok"
    except Exception:
        # Do not expose exception messages or connection details.
        return "error"


@router.get("/health/live")
def liveness() -> dict:
    """Confirm the API process is running."""
    return {"status": "alive"}


@router.get("/health/ready")
def readiness() -> JSONResponse:
    """Check whether required infrastructure dependencies are reachable."""

    checks = {
        "sql_database": _check_sql_database,
        "document_database": _check_document_database,
        "redis": _check_redis,
        "qdrant": _check_qdrant,
    }

    # Bound concurrency so dependency failures cannot create
    # an unbounded number of health-check threads.
    with ThreadPoolExecutor(max_workers=len(checks)) as executor:
        futures = {
            name: executor.submit(_run_check, check)
            for name, check in checks.items()
        }
        dependencies = {
            name: future.result()
            for name, future in futures.items()
        }

    ready = all(
        status == "ok"
        for status in dependencies.values()
    )

    return JSONResponse(
        status_code=200 if ready else 503,
        content={
            "status": "ready" if ready else "not_ready",
            "dependencies": dependencies,
        },
    )
