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
    name = "postgres"
    try:
        await asyncio.to_thread(_ping_postgres, settings.psycopg_dsn)
        return DependencyCheck(name=name, ok=True)
    except Exception as exc:
        logger.warning("postgres ready check failed: %s", exc)
        return DependencyCheck(name=name, ok=False, detail=str(exc))


async def check_redis_tcp(settings: Settings) -> DependencyCheck:
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


async def check_upstash_redis(settings: Settings) -> DependencyCheck:
    name = "upstash_redis"
    url = settings.upstash_redis_rest_url
    token = settings.upstash_redis_rest_token
    if not url or not token:
        return DependencyCheck(name=name, ok=False, detail="missing REST credentials")
    client = None
    try:
        from upstash_redis.asyncio import Redis as UpstashRedis

        client = UpstashRedis(url=url, token=token)
        pong = await client.ping()
        if pong is True or pong == "PONG":
            return DependencyCheck(name=name, ok=True)
        return DependencyCheck(name=name, ok=False, detail=f"unexpected ping: {pong!r}")
    except Exception as exc:
        logger.warning("upstash redis ready check failed: %s", exc)
        return DependencyCheck(name=name, ok=False, detail=str(exc))
    finally:
        if client is not None:
            await client.close()


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


def _ping_upstash_vector(settings: Settings) -> None:
    from atlas_persistence.vector.upstash_client import get_upstash_index

    index = get_upstash_index(settings)
    info = index.info()
    # Touch fields so a broken index surfaces as not ready.
    _ = int(info.dimension)


async def check_upstash_vector(settings: Settings) -> DependencyCheck:
    name = "upstash_vector"
    try:
        await asyncio.to_thread(_ping_upstash_vector, settings)
        return DependencyCheck(name=name, ok=True)
    except Exception as exc:
        logger.warning("upstash vector ready check failed: %s", exc)
        return DependencyCheck(name=name, ok=False, detail=str(exc))


async def check_qstash(settings: Settings) -> DependencyCheck:
    """Reachability probe: authenticated GET against QStash schedules API."""
    name = "qstash"
    token = settings.qstash_token
    if not token:
        return DependencyCheck(name=name, ok=False, detail="missing QSTASH_TOKEN")
    base = (settings.qstash_url or "https://qstash.upstash.io").rstrip("/")
    url = f"{base}/v2/schedules"
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            response = await client.get(
                url,
                headers={"Authorization": f"Bearer {token}"},
            )
            # 2xx/4xx means the control plane answered; 5xx / transport = down.
            if response.status_code < 500:
                return DependencyCheck(name=name, ok=True)
            return DependencyCheck(
                name=name,
                ok=False,
                detail=f"HTTP {response.status_code}",
            )
    except Exception as exc:
        logger.warning("qstash ready check failed: %s", exc)
        return DependencyCheck(name=name, ok=False, detail=str(exc))


async def collect_ready_checks(settings: Settings) -> list[DependencyCheck]:
    """Run dependency probes for the active data plane. Test env skips network I/O."""
    if settings.is_test:
        if settings.is_upstash_plane:
            return [
                DependencyCheck(name="postgres", ok=True, detail="skipped in test"),
                DependencyCheck(name="upstash_redis", ok=True, detail="skipped in test"),
                DependencyCheck(name="upstash_vector", ok=True, detail="skipped in test"),
                DependencyCheck(name="qstash", ok=True, detail="skipped in test"),
            ]
        return [
            DependencyCheck(name="postgres", ok=True, detail="skipped in test"),
            DependencyCheck(name="redis", ok=True, detail="skipped in test"),
            DependencyCheck(name="qdrant", ok=True, detail="skipped in test"),
        ]

    if settings.is_upstash_plane:
        return [
            await check_postgres(settings),
            await check_upstash_redis(settings),
            await check_upstash_vector(settings),
            await check_qstash(settings),
        ]
    return [
        await check_postgres(settings),
        await check_redis_tcp(settings),
        await check_qdrant(settings),
    ]


@router.get("/ready", response_model=ReadyResponse)
async def ready(settings: SettingsDep, response: Response) -> ReadyResponse:
    """Readiness: probes match ``ATLAS_DATA_PLANE`` (local Redis/Qdrant or Upstash)."""
    checks = await collect_ready_checks(settings)
    is_ready = all(check.ok for check in checks)
    if not is_ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    return ReadyResponse(
        status="ready" if is_ready else "not_ready",
        checks=checks,
    )
