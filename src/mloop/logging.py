"""Logging configuration for MLOOP."""

import logging
import sys


def setup_logging(level: int = logging.INFO) -> logging.Logger:
    """Set up logging for MLOOP.

    Args:
        level: Logging level.

    Returns:
        Configured logger instance.
    """
    logger = logging.getLogger("mloop")
    logger.setLevel(level)

    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)

    formatter = logging.Formatter(
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    handler.setFormatter(formatter)

    if not logger.handlers:
        logger.addHandler(handler)

    return logger
