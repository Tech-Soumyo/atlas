"""Liveness and readiness endpoints."""

from __future__ import annotations

import asyncio
import logging

import httpx
import psycopg
import redis.asyncio as redis
from atlas_common.config import Settings
from fastapi import APIRouter, Response, status

from atlas_api import __version__
from atlas_api.dependencies import SettingsDep
from atlas_api.schemas.common import DependencyCheck, HealthResponse, ReadyResponse

logger = logging.getLogger(__name__)

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    """Liveness: process is up."""
    return HealthResponse(status="ok", service="atlas-api", version=__version__)


def _ping_postgres(dsn: str) -> None:
    with psycopg.connect(dsn, connect_timeout=3) as conn, conn.cursor() as cur:
        cur.execute("SELECT 1")
        cur.fetchone()


async def check_postgres(settings: Settings) -> DependencyCheck:
    try:
        await asyncio.to_thread(_ping_postgres, settings.psycopg_dsn)
        return DependencyCheck(name="postgres", ok=True)
    except Exception as exc:
        logger.warning("postgres ready check failed: %s", exc)
        return DependencyCheck(name="postgres", ok=False, detail=str(exc))


async def check_redis(settings: Settings) -> DependencyCheck:
    client: redis.Redis | None = None
    try:
        client = redis.from_url(settings.redis_url, socket_connect_timeout=3)
        pong = await client.ping()
        if pong is True:
            return DependencyCheck(name="redis", ok=True)
        return DependencyCheck(name="redis", ok=False, detail="unexpected ping response")
    except Exception as exc:
        logger.warning("redis ready check failed: %s", exc)
        return DependencyCheck(name="redis", ok=False, detail=str(exc))
    finally:
        if client is not None:
            await client.aclose()


async def check_qdrant(settings: Settings) -> DependencyCheck:
    url = settings.qdrant_url.rstrip("/") + "/readyz"
    headers: dict[str, str] = {}
    if settings.qdrant_api_key:
        headers["api-key"] = settings.qdrant_api_key
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code < 400:
                return DependencyCheck(name="qdrant", ok=True)
            return DependencyCheck(
                name="qdrant",
                ok=False,
                detail=f"HTTP {response.status_code}",
            )
    except Exception as exc:
        logger.warning("qdrant ready check failed: %s", exc)
        return DependencyCheck(name="qdrant", ok=False, detail=str(exc))


async def collect_ready_checks(settings: Settings) -> list[DependencyCheck]:
    """Run dependency probes. In test env, skip network I/O."""
    if settings.is_test:
        return [
            DependencyCheck(name="postgres", ok=True, detail="skipped in test"),
            DependencyCheck(name="redis", ok=True, detail="skipped in test"),
            DependencyCheck(name="qdrant", ok=True, detail="skipped in test"),
        ]
    return [
        await check_postgres(settings),
        await check_redis(settings),
        await check_qdrant(settings),
    ]


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: SettingsDep, response: Response) -> ReadyResponse:
    """Readiness: postgres, redis, and qdrant accept connections."""
    checks = await collect_ready_checks(settings)
    is_ready = all(check.ok for check in checks)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if is_ready else "not_ready",
        checks=checks,
    )
