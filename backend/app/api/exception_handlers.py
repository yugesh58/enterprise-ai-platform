from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.logging import get_logger
from app.core.request_context import request_id_var
from app.core.exceptions import (
    AgentExecutionError,
    ApplicationValidationError,
    EnterpriseAIError,
    RouterError,
    UnauthorizedError,
)

logger = get_logger(__name__)


def _error_response(
    status_code: int,
    code: str,
    message: str,
) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id_var.get(),
            }
        },
    )


async def http_exception_handler(
    request: Request,
    exc: StarletteHTTPException,
) -> JSONResponse:
    if exc.status_code >= 500:
        code = "INTERNAL_SERVER_ERROR"
        message = "An unexpected error occurred."
    else:
        code = "HTTP_ERROR"
        message = (
            exc.detail
            if isinstance(exc.detail, str)
            else "The request could not be completed."
        )

    return _error_response(
        status_code=exc.status_code,
        code=code,
        message=message,
    )


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    logger.warning(
        "Request validation failed: method=%s path=%s",
        request.method,
        request.url.path,
    )

    return _error_response(
        status_code=422,
        code="VALIDATION_ERROR",
        message="Request validation failed.",
    )


async def unexpected_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.error(
        "Unhandled exception: method=%s path=%s",
        request.method,
        request.url.path,
        exc_info=(type(exc), exc, exc.__traceback__),
    )

    return _error_response(
        status_code=500,
        code="INTERNAL_SERVER_ERROR",
        message="An unexpected error occurred.",
    )

async def application_exception_handler(
    request: Request,
    exc: EnterpriseAIError,
) -> JSONResponse:
    mappings = {
        ApplicationValidationError: (
            422,
            "APPLICATION_VALIDATION_ERROR",
            "Application validation failed.",
        ),
        UnauthorizedError: (
            401,
            "UNAUTHORIZED",
            "Authentication is required or invalid.",
        ),
        AgentExecutionError: (
            502,
            "AGENT_EXECUTION_ERROR",
            "The agent could not complete the request.",
        ),
        RouterError: (
            500,
            "ROUTER_ERROR",
            "An internal routing error occurred.",
        ),
        EnterpriseAIError: (
            500,
            "APPLICATION_ERROR",
            "An unexpected application error occurred.",
        ),
    }

    status_code, code, message = mappings[type(exc)]

    logger.error(
        "Application exception: type=%s method=%s path=%s",
        type(exc).__name__,
        request.method,
        request.url.path,
    )

    return _error_response(
        status_code=status_code,
        code=code,
        message=message,
    )

def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(
        StarletteHTTPException,
        http_exception_handler,
    )
    app.add_exception_handler(
        RequestValidationError,
        validation_exception_handler,
    )
    app.add_exception_handler(
        Exception,
        unexpected_exception_handler,
    )
    app.add_exception_handler(
    EnterpriseAIError,
    application_exception_handler,
    )