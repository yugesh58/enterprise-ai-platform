import json
import logging
from datetime import datetime, timezone
from typing import Any

from app.core.config import settings
from app.core.request_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


class JsonFormatter(logging.Formatter):
    """Format logs as structured JSON."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(
                record.created,
                tz=timezone.utc,
            ).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": getattr(record, "request_id", "-"),
        }

        # Include only explicitly supported structured fields.
        structured_fields = (
            "method",
            "path",
            "status_code",
            "duration_ms",
            "operation",
            "provider",
            "model",
            "outcome",
            "input_tokens",
            "output_tokens",
            "total_tokens",
            "chunk_count",
            "estimated_cost_usd",
        )

        for key in structured_fields:
            value = getattr(record, key, None)
            if value is not None:
                payload[key] = value

        # Include exception details when available.
        if record.exc_info:
            payload["exception"] = self.formatException(
                record.exc_info
            )

        return json.dumps(
            payload,
            ensure_ascii=False,
            default=str,
        )


def get_logger(name: str) -> logging.Logger:
    """Return a configured application logger."""

    logger = logging.getLogger(name)

    # Avoid attaching duplicate handlers.
    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())
    handler.setFormatter(JsonFormatter())

    logger.addHandler(handler)

    return logger
