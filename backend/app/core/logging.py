import logging

from app.core.config import settings


def get_logger(name: str):

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

    return logger