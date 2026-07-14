import logging

from app.core.config import settings


def get_logger(name: str) -> logging.Logger:
    """
    Returns a configured logger instance.

    The logger is created only once per module and reused
    throughout the application's lifetime.
    """

    logger = logging.getLogger(name)

    if logger.handlers:
        return logger

    logger.setLevel(settings.LOG_LEVEL)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
    )

    handler = logging.StreamHandler()
    handler.setFormatter(formatter)

    logger.addHandler(handler)

    # Prevent duplicate logs from the root logger
    logger.propagate = False

    return logger