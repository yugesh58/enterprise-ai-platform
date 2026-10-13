from uuid import uuid4

from starlette.datastructures import Headers
from starlette.types import ASGIApp, Message, Receive, Scope, Send

from app.core.request_context import request_id_var


class RequestContextMiddleware:
    """Attach a correlation ID to each HTTP request."""

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

        # Generate our own ID instead of blindly trusting client input.
        request_id = str(uuid4())
        token = request_id_var.set(request_id)

        async def send_with_request_id(message: Message) -> None:
            if message["type"] == "http.response.start":
                headers = Headers(raw=message.get("headers", []))
                response_headers = list(headers.raw)
                response_headers.append(
                    (b"x-request-id", request_id.encode("ascii"))
                )
                message = {
                    **message,
                    "headers": response_headers,
                }

            await send(message)

        try:
            await self.app(scope, receive, send_with_request_id)
        finally:
            request_id_var.reset(token)