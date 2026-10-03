"""FastAPI application entrypoint."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_common.config import get_settings, load_yaml_configs
from atlas_common.logging import configure_logging, get_logger
from atlas_common.telemetry import setup_telemetry
from atlas_persistence.postgres.engine import dispose_engine, init_engine
from atlas_persistence.qdrant.client import ensure_chunks_collection
from atlas_persistence.redis.queue import close_arq_pool
from atlas_persistence.redis.rate_limit import close_rate_limit_redis
from atlas_security.api_key import require_api_key_configured
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from atlas_api import __version__
from atlas_api.error_handlers import register_error_handlers
from atlas_api.routers import ask_router, documents_router, health_router, jobs_router

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    settings = get_settings()
    require_api_key_configured(settings)
    configure_logging(settings.atlas_log_level, service_name=settings.otel_service_name)
    setup_telemetry(
        service_name=settings.otel_service_name,
        otlp_endpoint=settings.otel_exporter_otlp_endpoint,
    )
    init_engine(settings)
    if not settings.is_test:
        try:
            ensure_chunks_collection(settings)
        except Exception as exc:
            logger.warning("qdrant collection ensure skipped: %s", exc)
    yaml_configs = load_yaml_configs(settings.configs_dir)
    logger.info(
        "atlas-api starting env=%s data_plane=%s yaml_files=%s version=%s",
        settings.atlas_env,
        settings.atlas_data_plane,
        sorted(yaml_configs.keys()),
        __version__,
    )
    yield
    await close_arq_pool()
    await close_rate_limit_redis()
    await dispose_engine()
    logger.info("atlas-api shutting down")


def create_app() -> FastAPI:
    """Application factory used by uvicorn and tests."""
    application = FastAPI(
        title="Atlas API",
        version=__version__,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://web:3000",
        ],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    register_error_handlers(application)
    application.include_router(health_router)
    application.include_router(documents_router)
    application.include_router(jobs_router)
    application.include_router(ask_router)
    return application


app = create_app()
