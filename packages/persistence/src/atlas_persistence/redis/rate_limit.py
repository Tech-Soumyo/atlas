"""Fixed window IP rate limits for upload and ask."""

from __future__ import annotations

from dataclasses import dataclass

import redis.asyncio as redis
from atlas_common.config import Settings, get_settings

_pool: redis.Redis | None = None


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    redis_unavailable: bool = False


async def get_rate_limit_redis(settings: Settings | None = None) -> redis.Redis:
    """Return a process-wide Redis client for rate limiting."""
    global _pool
    if _pool is not None:
        return _pool
    cfg = settings or get_settings()
    _pool = redis.from_url(cfg.redis_url, socket_connect_timeout=3)  # type: ignore[no-untyped-call]
    return _pool


async def close_rate_limit_redis() -> None:
    """Close the shared rate-limit Redis client (API lifespan shutdown)."""
    global _pool
    if _pool is not None:
        await _pool.aclose()
        _pool = None


async def check_rate_limit(
    *,
    kind: str,
    client_ip: str,
    limit: int,
    settings: Settings | None = None,
    window_seconds: int = 60,
) -> RateLimitResult:
    """Increment a fixed window counter. Fail closed if Redis is down."""
    key = f"atlas:rl:{kind}:{client_ip}"
    try:
        client = await get_rate_limit_redis(settings)
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return RateLimitResult(allowed=int(count) <= limit)
    except Exception:
        return RateLimitResult(allowed=False, redis_unavailable=True)
