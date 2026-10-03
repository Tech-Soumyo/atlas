"""IP rate limits for upload and ask.

Algorithm choice: **fixed window** (INCR + EXPIRE on ``atlas:rl:{kind}:{identifier}``).

Why not sliding window (as in ``@upstash/ratelimit`` defaults)?
- Over Upstash REST, fixed window is 1–2 commands per check; sliding needs ~4–5
  (EVAL + dual-window GETs + INCR + PEXPIRE) and costs more on the free tier.
- Atlas limits are coarse (per-minute upload/ask caps); boundary burst leakage is
  acceptable vs the extra Redis bill and Lua complexity.
- Semantics match the previous TCP Redis implementation and existing unit tests.

Cloud path (``atlas_data_plane=upstash``): ``upstash_redis.asyncio.Redis`` REST only.
Local path (``atlas_data_plane=local``): TCP ``redis.asyncio`` for Compose.
Both reuse a process-wide client. Fail closed on Redis errors.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, cast

import redis.asyncio as redis
from atlas_common.config import Settings, get_settings
from upstash_redis.asyncio import Redis as UpstashRedis

_tcp_client: redis.Redis | None = None
_upstash_client: UpstashRedis | None = None


class RateLimitRedis(Protocol):
    """Minimal async Redis surface used by fixed-window rate limiting."""

    async def incr(self, key: str) -> int: ...

    async def expire(self, key: str, seconds: int) -> bool | int: ...


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    redis_unavailable: bool = False


def _rate_limit_key(*, kind: str, identifier: str) -> str:
    return f"atlas:rl:{kind}:{identifier}"


async def get_rate_limit_redis(settings: Settings | None = None) -> RateLimitRedis:
    """Return a process-wide Redis client for rate limiting (REST or TCP)."""
    global _tcp_client, _upstash_client
    cfg = settings or get_settings()

    if cfg.is_upstash_plane:
        if _upstash_client is not None:
            return cast(RateLimitRedis, _upstash_client)
        url = cfg.upstash_redis_rest_url
        token = cfg.upstash_redis_rest_token
        if not url or not token:
            raise ValueError(
                "UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN are required "
                "when atlas_data_plane=upstash"
            )
        _upstash_client = UpstashRedis(url=url, token=token)
        return cast(RateLimitRedis, _upstash_client)

    if _tcp_client is not None:
        return cast(RateLimitRedis, _tcp_client)
    _tcp_client = redis.from_url(cfg.redis_url, socket_connect_timeout=3)  # type: ignore[no-untyped-call]
    return cast(RateLimitRedis, _tcp_client)


async def close_rate_limit_redis() -> None:
    """Close shared rate-limit Redis clients (API lifespan shutdown)."""
    global _tcp_client, _upstash_client
    if _tcp_client is not None:
        await _tcp_client.aclose()
        _tcp_client = None
    if _upstash_client is not None:
        await _upstash_client.close()
        _upstash_client = None


async def check_rate_limit(
    *,
    kind: str,
    client_ip: str,
    limit: int,
    settings: Settings | None = None,
    window_seconds: int = 60,
) -> RateLimitResult:
    """Increment a fixed window counter. Fail closed if Redis is down."""
    key = _rate_limit_key(kind=kind, identifier=client_ip)
    try:
        client = await get_rate_limit_redis(settings)
        count = await client.incr(key)
        if count == 1:
            await client.expire(key, window_seconds)
        return RateLimitResult(allowed=int(count) <= limit)
    except Exception:
        return RateLimitResult(allowed=False, redis_unavailable=True)
