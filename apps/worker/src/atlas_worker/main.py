"""Async ingest worker entrypoint (arq)."""

from __future__ import annotations

from typing import Any, ClassVar

from arq.connections import RedisSettings
from atlas_common.config import get_settings
from atlas_common.logging import configure_logging, get_logger
from atlas_common.telemetry import setup_telemetry
from atlas_persistence.postgres.engine import dispose_engine, init_engine
from atlas_persistence.qdrant.client import ensure_chunks_collection
from atlas_security.api_key import require_api_key_configured

from atlas_worker import __version__
from atlas_worker.handlers.ingest_document import ingest_document
from atlas_worker.reconcile import reconcile_stale_jobs

logger = get_logger(__name__)


async def on_startup(ctx: dict[str, Any]) -> None:
    settings = get_settings()
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
        logger.warning("qdrant collection ensure skipped: %s", exc)
    await reconcile_stale_jobs(settings)
    logger.info(
        "atlas-worker started version=%s concurrency=%s",
        __version__,
        settings.worker_concurrency,
    )
    ctx["settings"] = settings


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await dispose_engine()
    logger.info("atlas-worker shutting down")


class WorkerSettings:
    """arq worker settings (also usable as ``arq atlas_worker.main.WorkerSettings``)."""

    functions: ClassVar[list[Any]] = [ingest_document]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = get_settings().worker_concurrency
    job_timeout = get_settings().worker_job_timeout_seconds
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)


def main() -> None:
    from arq.worker import run_worker

    settings = get_settings()
    configure_logging(settings.atlas_log_level, service_name="atlas-worker")
    run_worker(WorkerSettings)  # type: ignore[arg-type]


if __name__ == "__main__":
    main()
