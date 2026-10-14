
import time
from uuid import uuid4

from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.logging import get_logger
from app.core.request_context import request_id_var

logger = get_logger(__name__)


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

        request_id = str(uuid4())
        context_token = request_id_var.set(request_id)

        start_time = time.perf_counter()
        status_code = 500
        response_started = False

        async def send_with_request_id(message: Message) -> None:
            nonlocal response_started, status_code

            if message["type"] == "http.response.start":
                response_started = True
                status_code = message["status"]

                headers = list(message.get("headers", []))
                headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message = {
                    **message,
                    "headers": headers,
                }

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
