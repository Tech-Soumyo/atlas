"""Worker entrypoint: arq (local) or uvicorn HTTP (upstash / QStash).

Upstash mode
------------
Jobs are delivered by QStash to this process's HTTP app
(``atlas_worker.http_app:app``):

* ``POST /internal/jobs/ingest``
* ``POST /internal/jobs/ingest-failed``

Run (point ``ATLAS_WORKER_PUBLIC_URL`` / a tunnel at this port)::

    uv run atlas-worker
    # or: uv run uvicorn atlas_worker.http_app:app --host 0.0.0.0 --port 8001

Local mode
----------
Classic arq consumer against TCP ``REDIS_URL``::

    uv run atlas-worker
    # or: arq atlas_worker.main.WorkerSettings

arq is not on the critical path when ``ATLAS_DATA_PLANE=upstash``.
"""

from __future__ import annotations

import os
import sys
from typing import Any, ClassVar

from arq.connections import RedisSettings
from atlas_common.config import ensure_data_plane, get_settings
from atlas_common.logging import configure_logging, get_logger
from atlas_common.telemetry import setup_telemetry
from atlas_persistence.postgres.engine import dispose_engine, init_engine
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
        from atlas_persistence.vector.store import ensure_chunks_collection

        ensure_chunks_collection(settings)
    except Exception as exc:
        logger.warning("vector collection ensure skipped: %s", exc)
    await reconcile_stale_jobs(settings)
    logger.info(
        "atlas-worker (arq) started version=%s concurrency=%s",
        __version__,
        settings.worker_concurrency,
    )
    ctx["settings"] = settings


async def on_shutdown(ctx: dict[str, Any]) -> None:
    await dispose_engine()
    logger.info("atlas-worker shutting down")


class WorkerSettings:
    """arq worker settings (local data plane only; unused when upstash)."""

    functions: ClassVar[list[Any]] = [ingest_document]
    on_startup = on_startup
    on_shutdown = on_shutdown
    max_jobs = get_settings().worker_concurrency
    job_timeout = get_settings().worker_job_timeout_seconds
    redis_settings = RedisSettings.from_dsn(get_settings().redis_url)


def _run_arq() -> None:
    from arq.worker import run_worker

    run_worker(WorkerSettings)  # type: ignore[arg-type]


def _run_http() -> None:
    import uvicorn

    settings = get_settings()
    host = settings.atlas_api_host
    port = int(os.environ.get("ATLAS_WORKER_PORT", "8001"))
    logger.info(
        "starting QStash HTTP worker host=%s port=%s public_url=%s",
        host,
        port,
        settings.atlas_worker_public_url,
    )
    uvicorn.run(
        "atlas_worker.http_app:app",
        host=host,
        port=port,
        log_level=settings.atlas_log_level.lower(),
    )


def main() -> None:
    settings = get_settings()
    configure_logging(settings.atlas_log_level, service_name="atlas-worker")
    if settings.is_upstash_plane:
        try:
            ensure_data_plane(settings)
        except RuntimeError as exc:
            logger.error("%s", exc)
            sys.exit(1)
        _run_http()
        return
    _run_arq()


if __name__ == "__main__":
    main()
