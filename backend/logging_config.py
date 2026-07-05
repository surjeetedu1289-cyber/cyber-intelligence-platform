"""Central logging configuration for the backend services."""

import logging
import os
from typing import Optional


def configure_logging(log_level: Optional[str] = None) -> logging.Logger:
    """Configure structured application logging for the backend."""
    level_name = (log_level or os.getenv("LOG_LEVEL", "INFO")).upper()
    level = getattr(logging, level_name, logging.INFO)

    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    logger = logging.getLogger("cyber_intelligence")
    logger.setLevel(level)
    return logger


LOGGER = configure_logging()
