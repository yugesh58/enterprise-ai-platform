
import re
import time
from uuid import uuid4

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger
from app.core.request_context import request_id_var
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest

from app.core.metrics import (
    HTTP_REQUESTS_TOTAL,
    HTTP_REQUEST_DURATION_SECONDS,
)

logger = get_logger(__name__)

# Restrict IDs to a safe, bounded character set.
_REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,128}$")


def _get_request_id(scope: Scope) -> str:
    """Accept a safe incoming request ID or generate a UUID."""
    headers = dict(scope.get("headers", []))
    incoming = headers.get(b"x-request-id", b"")

    try:
        candidate = incoming.decode("ascii")
    except UnicodeDecodeError:
        candidate = ""

    if candidate and _REQUEST_ID_PATTERN.fullmatch(candidate):
        return candidate

    return str(uuid4())

def _get_route_template(scope: Scope) -> str:
    """Return a bounded route label, never the raw URL."""
    route = scope.get("route")
    path = getattr(route, "path", None)

    if isinstance(path, str) and path:
        return path

    return "__unmatched__"

class RequestContextMiddleware:
    """Attach a correlation ID and log completion for each HTTP request."""

    def __init__(self, app: ASGIApp) -> None:
        self.app = app

    async def __call__(
        self,
        scope: Scope,
        receive: Receive,
        send: Send,
    ) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request_id = _get_request_id(scope)
        context_token = request_id_var.set(request_id)

        start_time = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]

                # Replace any existing value rather than append a duplicate.
                headers = [
                    (name, value)
                    for name, value in message.get("headers", [])
                    if name.lower() != b"x-request-id"
                ]
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message = {**message, "headers": headers}

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)

        except Exception:
            if response_started:
                # A response has already started; a new HTTP response
                # cannot safely be sent.
                raise

            logger.exception(
                "Unhandled request exception: method=%s path=%s",
                scope.get("method"),
                scope.get("path"),
            )

            status_code = 500

            response = JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                        "request_id": request_id,
                    }
                },
                headers={"X-Request-ID": request_id},
            )

            await response(scope, receive, send)

        finally:
            duration_ms = round(
                (time.perf_counter() - start_time) * 1000,
                2,
            )
            route = _get_route_template(scope)
            method = scope.get("method", "UNKNOWN")

            HTTP_REQUESTS_TOTAL.labels(
            method=method,
            route=route,
            status_code=str(status_code),
            ).inc()

            HTTP_REQUEST_DURATION_SECONDS.labels(
                method=method,
                route=route,
                ).observe(duration_ms / 1000)

            logger.info(
                "Request completed",
                extra={
                    "method": scope.get("method"),
                    "path": scope.get("path"),
                    "status_code": status_code,
                    "duration_ms": duration_ms,
                },
            )

            request_id_var.reset(context_token)
