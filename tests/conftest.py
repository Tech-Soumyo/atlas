"""Pytest fixtures shared across the suite."""

from __future__ import annotations

import os

import pytest

# Force a safe test profile before Settings / app imports.
# ATLAS_ENV=test skips validate_data_plane(); dummy cloud vars keep Upstash/Neon
# code paths constructible without live network or host .env secrets.
os.environ["ATLAS_ENV"] = "test"
os.environ["ATLAS_DATA_PLANE"] = "upstash"
os.environ["DATABASE_URL"] = (
    "postgresql+psycopg://atlas:atlas@ep-test.neon.tech/neondb?sslmode=require"
)
os.environ["DATABASE_URL_POOLED"] = (
    "postgresql+psycopg://atlas:atlas@ep-test-pooler.neon.tech/neondb?sslmode=require"
)
# Local-plane fallbacks still available when a test sets atlas_data_plane=local.
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("QDRANT_URL", "http://localhost:6333")
os.environ["UPSTASH_REDIS_REST_URL"] = "https://example-redis.upstash.io"
os.environ["UPSTASH_REDIS_REST_TOKEN"] = "test-upstash-redis-token"
os.environ["UPSTASH_VECTOR_REST_URL"] = "https://example-vector.upstash.io"
os.environ["UPSTASH_VECTOR_REST_TOKEN"] = "test-upstash-vector-token"
os.environ["QSTASH_TOKEN"] = "test-qstash-token"
os.environ["QSTASH_CURRENT_SIGNING_KEY"] = "test-qstash-current-signing-key"
os.environ["QSTASH_NEXT_SIGNING_KEY"] = "test-qstash-next-signing-key"
os.environ["ATLAS_WORKER_PUBLIC_URL"] = "https://example-worker.test"
os.environ.setdefault("ATLAS_API_KEY", "test-key")
os.environ.setdefault("OBJECT_STORE_PATH", "./data/raw-test")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from atlas_common.config import clear_settings_cache

    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture(autouse=True)
def _reset_persistence_singletons() -> None:
    """Drop process-wide Redis/QStash/Vector clients between tests."""
    import atlas_persistence.redis.queue as queue_mod
    import atlas_persistence.redis.rate_limit as rate_limit_mod
    import atlas_persistence.vector.upstash_client as vector_mod

    rate_limit_mod._tcp_client = None
    rate_limit_mod._upstash_client = None
    queue_mod._pool = None
    queue_mod._qstash = None
    vector_mod._index = None
    vector_mod._index_key = None
    yield
    rate_limit_mod._tcp_client = None
    rate_limit_mod._upstash_client = None
    queue_mod._pool = None
    queue_mod._qstash = None
    vector_mod._index = None
    vector_mod._index_key = None


@pytest.fixture
def api_client():
    from atlas_api.main import create_app
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as client:
        yield client
