"""Pytest fixtures shared across the suite."""

from __future__ import annotations

import os

import pytest

# Force a safe test profile before Settings / app imports.
# Override host cloud .env values so unit/integration tests hit local Compose.
os.environ["ATLAS_ENV"] = "test"
os.environ["ATLAS_DATA_PLANE"] = "local"
os.environ["DATABASE_URL"] = "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"
os.environ["QDRANT_URL"] = "http://localhost:6333"
os.environ.setdefault("ATLAS_API_KEY", "test-key")
os.environ.setdefault("OBJECT_STORE_PATH", "./data/raw-test")


@pytest.fixture(autouse=True)
def _clear_settings_cache() -> None:
    from atlas_common.config import clear_settings_cache

    clear_settings_cache()
    yield
    clear_settings_cache()


@pytest.fixture
def api_client():
    from atlas_api.main import create_app
    from fastapi.testclient import TestClient

    with TestClient(create_app()) as client:
        yield client
