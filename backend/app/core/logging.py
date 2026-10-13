
import logging

from app.core.config import settings
from app.core.request_context import request_id_var


class RequestIdFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_var.get()
        return True


def get_logger(name: str) -> logging.Logger:
    """Return a configured application logger."""

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)
    logger.propagate = False

    handler = logging.StreamHandler()
    handler.addFilter(RequestIdFilter())

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s "
        "| request_id=%(request_id)s | %(message)s"
    )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    return logger
