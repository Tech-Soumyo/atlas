"""FastAPI dependency providers."""

from __future__ import annotations

from collections.abc import AsyncIterator
from typing import Annotated

from atlas_common.config import Settings, get_settings
from atlas_persistence.postgres.engine import get_session_factory, init_engine
from atlas_persistence.redis.rate_limit import check_rate_limit
from atlas_security.api_key import ApiKeyError, verify_api_key
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

SettingsDep = Annotated[Settings, Depends(get_settings)]


async def get_db_session(settings: SettingsDep) -> AsyncIterator[AsyncSession]:
    init_engine(settings)
    factory = get_session_factory(settings)
    session = factory()
    try:
        yield session
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    finally:
        await session.close()


SessionDep = Annotated[AsyncSession, Depends(get_db_session)]


async def require_api_key(
    settings: SettingsDep,
    x_api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> None:
    try:
        verify_api_key(x_api_key, settings=settings)
    except ApiKeyError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc


ApiKeyDep = Annotated[None, Depends(require_api_key)]


def client_ip(request: Request) -> str:
    """Use the direct connection IP only (no X-Forwarded-For trust in M1)."""
    if request.client is None:
        return "unknown"
    return request.client.host


async def enforce_rate_limit(
    *,
    kind: str,
    client_ip: str,
    limit: int,
    settings: Settings,
) -> None:
    """Fail-closed IP rate limit. Skipped when settings.is_test is True."""
    if settings.is_test:
        return
    result = await check_rate_limit(
        kind=kind,
        client_ip=client_ip,
        limit=limit,
        settings=settings,
    )
    if result.redis_unavailable:
        raise HTTPException(status_code=503, detail="rate limit store unavailable")
    if not result.allowed:
        raise HTTPException(status_code=429, detail=f"{kind} rate limit exceeded")
