"""Async SQLAlchemy engine and session factory."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from atlas_common.config import Settings, get_settings
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

_engine: AsyncEngine | None = None
_session_factory: async_sessionmaker[AsyncSession] | None = None


def init_engine(settings: Settings | None = None) -> AsyncEngine:
    """Create (or return) the process wide async engine.

    Uses ``Settings.sqlalchemy_database_url`` (Neon pooled / PgBouncer when
    ``DATABASE_URL_POOLED`` is set; otherwise ``DATABASE_URL``). SSL for Neon
    is expected via ``sslmode=require`` on the URL query string.
    """
    global _engine, _session_factory
    if _engine is not None:
        return _engine
    cfg = settings or get_settings()
    _engine = create_async_engine(cfg.sqlalchemy_database_url, pool_pre_ping=True)
    _session_factory = async_sessionmaker(_engine, expire_on_commit=False)
    return _engine


def get_session_factory(
    settings: Settings | None = None,
) -> async_sessionmaker[AsyncSession]:
    """Return the async session factory, initializing the engine if needed."""
    global _session_factory
    if _session_factory is None:
        init_engine(settings)
    assert _session_factory is not None
    return _session_factory


@asynccontextmanager
async def session_scope(
    settings: Settings | None = None,
) -> AsyncIterator[AsyncSession]:
    """Yield a session that commits on success and rolls back on error."""
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


async def dispose_engine() -> None:
    """Dispose the engine (tests / shutdown)."""
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
