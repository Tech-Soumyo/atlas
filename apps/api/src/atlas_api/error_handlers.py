"""Global exception handlers (expanded in later milestones)."""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)


def register_error_handlers(app: FastAPI) -> None:
    """Attach baseline unhandled exception logging."""

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        _request: Request,
        _exc: Exception,
    ) -> JSONResponse:
        logger.exception("unhandled error path=%s", _request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "internal server error"},
        )
