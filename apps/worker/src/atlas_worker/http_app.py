"""FastAPI app for QStash HTTP worker mode (``ATLAS_DATA_PLANE=upstash``)."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_common.config import ensure_data_plane, get_settings
from atlas_common.logging import configure_logging, get_logger
from atlas_common.telemetry import setup_telemetry
from atlas_persistence.postgres.engine import dispose_engine, init_engine
from atlas_persistence.vector.store import ensure_chunks_collection
from atlas_security.api_key import require_api_key_configured
from fastapi import FastAPI

from atlas_worker import __version__
from atlas_worker.reconcile import reconcile_stale_jobs
from atlas_worker.routers import internal_jobs_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = ensure_data_plane(get_settings())
    require_api_key_configured(settings)
    configure_logging(settings.atlas_log_level, service_name="atlas-worker")
    setup_telemetry(
        service_name="atlas-worker",
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
    )
    init_engine(settings)
    try:
        ensure_chunks_collection(settings)
    except Exception as exc:
        logger.warning("vector collection ensure skipped: %s", exc)
    await reconcile_stale_jobs(settings)
    logger.info(
        "atlas-worker HTTP (QStash) started version=%s public_url=%s",
        __version__,
        settings.atlas_worker_public_url,
    )
    yield
    await dispose_engine()
    logger.info("atlas-worker HTTP shutting down")


def create_app() -> FastAPI:
    """Application factory for uvicorn (QStash delivery targets)."""
    application = FastAPI(
        title="Atlas Worker",
        version=__version__,
        lifespan=lifespan,
    )
    application.include_router(internal_jobs_router)

    @application.get("/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "atlas-worker", "version": __version__}

    return application


app = create_app()
