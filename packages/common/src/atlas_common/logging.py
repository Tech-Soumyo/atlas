"""Structured logging setup for API and worker processes."""

from __future__ import annotations

import logging
import sys


def configure_logging(level: str = "INFO", *, service_name: str = "atlas") -> None:
    """Configure root logging once for a process.

    Idempotent enough for M0: calling again resets handlers on the root logger.
    """
    root = logging.getLogger()
    root.handlers.clear()
    root.setLevel(level.upper())

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(
        logging.Formatter(
            fmt=(f"%(asctime)s %(levelname)s service={service_name} logger=%(name)s %(message)s"),
            datefmt="%Y-%m-%dT%H:%M:%S%z",
        )
    )
    root.addHandler(handler)

    # Quiet noisy clients until M7 observability work lands.
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)


def get_logger(name: str) -> logging.Logger:
    """Return a named logger."""
    return logging.getLogger(name)
