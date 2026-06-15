"""Structured logging via structlog.

Usage:
    from .logger import get_logger
    LOG = get_logger(__name__)
    log = LOG.child("fetch")   # hierarchical child loggers for sub-contexts
"""

# Builtin imports
import logging
import sys
from typing import Any

# Project specific imports
import structlog

_configured = False


def _configure() -> None:
    global _configured
    if _configured:
        return
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.dev.ConsoleRenderer(),
        ],
        wrapper_class=structlog.make_filtering_bound_logger(logging.INFO),
        logger_factory=structlog.PrintLoggerFactory(file=sys.stderr),
        cache_logger_on_first_use=True,
    )
    _configured = True


class Logger:
    """Thin typed wrapper over a structlog bound logger."""

    def __init__(self, logger: Any) -> None:
        self._logger = logger

    def child(self, context: str) -> "Logger":
        """Return a child logger that tags every record with `context`."""
        return Logger(self._logger.bind(context=context))

    def debug(self, event: str, **kwargs: Any) -> None:
        self._logger.debug(event, **kwargs)

    def info(self, event: str, **kwargs: Any) -> None:
        self._logger.info(event, **kwargs)

    def warning(self, event: str, **kwargs: Any) -> None:
        self._logger.warning(event, **kwargs)

    def error(self, event: str, **kwargs: Any) -> None:
        self._logger.error(event, **kwargs)


def get_logger(name: str) -> Logger:
    _configure()
    return Logger(structlog.get_logger(name))
