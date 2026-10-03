"""Environment + YAML configuration for Atlas.

Apps and packages read settings through this module. Do not scatter ``os.environ``
reads through domain packages.
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

import yaml
from pydantic_settings import BaseSettings, SettingsConfigDict

from atlas_common.types import JsonDict

DataPlane = Literal["local", "upstash"]
ObjectStoreBackend = Literal["local", "s3"]


def resolve_configs_dir(explicit: Path | None = None) -> Path:
    """Find the ``configs/`` directory (cwd, then walk up from this file)."""
    if explicit is not None:
        return explicit
    cwd_candidate = Path.cwd() / "configs"
    if cwd_candidate.is_dir():
        return cwd_candidate
    for parent in Path(__file__).resolve().parents:
        candidate = parent / "configs"
        if candidate.is_dir():
            return candidate
    return Path.cwd() / "configs"


class Settings(BaseSettings):
    """Process settings loaded from environment (and optional ``.env``)."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=False,
    )

    atlas_env: str = "development"
    # Cloud-native Neon + Upstash is the default runtime path.
    atlas_data_plane: DataPlane = "upstash"
    atlas_log_level: str = "INFO"
    atlas_api_host: str = "0.0.0.0"
    atlas_api_port: int = 8000

    atlas_jwt_secret: str = "change-me-in-local-only"
    atlas_jwt_algorithm: str = "HS256"
    atlas_jwt_expire_minutes: int = 1440
    atlas_demo_api_keys: str | None = None
    atlas_api_key: str | None = None

    atlas_max_upload_bytes: int = 20 * 1024 * 1024
    atlas_max_pdf_pages: int = 50
    atlas_max_documents: int = 10
    atlas_ingest_stale_seconds: int = 900
    atlas_rate_limit_upload_per_min: int = 5
    atlas_rate_limit_ask_per_min: int = 20

    database_url: str = "postgresql+psycopg://atlas:atlas@localhost:5432/atlas"
    # Neon pooled URL (PgBouncer) — prefer for SQLAlchemy runtime when set.
    database_url_pooled: str | None = None
    postgres_user: str = "atlas"
    postgres_password: str = "atlas"
    postgres_db: str = "atlas"
    postgres_host: str = "localhost"
    postgres_port: int = 5432

    qdrant_url: str = "http://localhost:6333"
    qdrant_api_key: str | None = None
    qdrant_collection: str = "atlas_chunks"

    redis_url: str = "redis://localhost:6379/0"
    redis_queue_name: str = "atlas:ingest"
    redis_cache_ttl_seconds: int = 3600

    # Upstash Redis (REST) — required when atlas_data_plane=upstash
    upstash_redis_rest_url: str | None = None
    upstash_redis_rest_token: str | None = None
    upstash_redis_rest_read_only_token: str | None = None

    # Upstash Vector — required when atlas_data_plane=upstash
    upstash_vector_rest_url: str | None = None
    upstash_vector_rest_token: str | None = None
    upstash_vector_rest_read_only_token: str | None = None

    # QStash — required when atlas_data_plane=upstash
    qstash_url: str | None = None
    qstash_token: str | None = None
    qstash_read_only_token: str | None = None
    qstash_current_signing_key: str | None = None
    qstash_next_signing_key: str | None = None
    # Public HTTPS base URL QStash can reach (tunnel in local cloud-mode dev).
    atlas_worker_public_url: str | None = None

    object_store_backend: ObjectStoreBackend = "local"
    object_store_path: str = "./data/raw"

    llm_provider: str = "groq"
    llm_base_url: str = "https://api.groq.com/openai/v1"
    openai_api_key: str | None = None
    llm_model: str = "openai/gpt-oss-20b"
    llm_timeout_seconds: int = 60
    llm_max_retries: int = 2
    llm_temperature: float = 0.1

    embedding_model: str = "sentence-transformers/all-MiniLM-L6-v2"
    embedding_dims: int = 384
    embedding_model_version: str = "st-all-minilm-l6-v2@1"
    embedding_device: str = "cpu"
    cross_encoder_model: str = "cross-encoder/ms-marco-MiniLM-L-6-v2"

    enable_query_rewrite: bool = True
    enable_multi_query: bool = False
    enable_mmr: bool = False
    enable_xgb_rerank: bool = False
    enable_agentic: bool = False
    enable_semantic_chunking: bool = False
    enable_response_cache: bool = True

    otel_service_name: str = "atlas-api"
    otel_exporter_otlp_endpoint: str | None = None

    worker_concurrency: int = 2
    worker_max_retries: int = 3
    worker_job_timeout_seconds: int = 600
    worker_heartbeat_seconds: int = 10

    atlas_configs_dir: Path | None = None

    @property
    def configs_dir(self) -> Path:
        return resolve_configs_dir(self.atlas_configs_dir)

    @property
    def is_test(self) -> bool:
        return self.atlas_env.lower() in {"test", "testing"}

    @property
    def is_upstash_plane(self) -> bool:
        return self.atlas_data_plane == "upstash"

    @property
    def sqlalchemy_database_url(self) -> str:
        """URL for SQLAlchemy runtime (prefer Neon pooled when configured)."""
        if self.database_url_pooled:
            return self.database_url_pooled
        return self.database_url

    @property
    def alembic_database_url(self) -> str:
        """URL for Alembic migrations (prefer direct Neon URL, not pooler)."""
        return self.database_url

    @property
    def psycopg_dsn(self) -> str:
        """DSN suitable for the psycopg3 driver (no SQLAlchemy dialect suffix)."""
        return self.sqlalchemy_database_url.replace(
            "postgresql+psycopg://", "postgresql://", 1
        )

    def validate_data_plane(self) -> None:
        """Fail fast when cloud mode is selected but required env vars are missing.

        Skipped when ``atlas_env`` is test/testing so unit tests can mock adapters.
        """
        if self.is_test or not self.is_upstash_plane:
            return
        missing: list[str] = []
        required: dict[str, str | None] = {
            "DATABASE_URL": self.database_url if self.database_url else None,
            "UPSTASH_REDIS_REST_URL": self.upstash_redis_rest_url,
            "UPSTASH_REDIS_REST_TOKEN": self.upstash_redis_rest_token,
            "UPSTASH_VECTOR_REST_URL": self.upstash_vector_rest_url,
            "UPSTASH_VECTOR_REST_TOKEN": self.upstash_vector_rest_token,
            "QSTASH_TOKEN": self.qstash_token,
            "QSTASH_CURRENT_SIGNING_KEY": self.qstash_current_signing_key,
            "QSTASH_NEXT_SIGNING_KEY": self.qstash_next_signing_key,
            "ATLAS_WORKER_PUBLIC_URL": self.atlas_worker_public_url,
        }
        for name, value in required.items():
            if name == "DATABASE_URL":
                # Default localhost URL is not a valid cloud Neon DSN.
                if not value or "localhost" in value or "127.0.0.1" in value:
                    missing.append(name)
                continue
            if value is None or (isinstance(value, str) and not value.strip()):
                missing.append(name)
        if missing:
            joined = ", ".join(missing)
            msg = (
                "ATLAS_DATA_PLANE=upstash requires cloud credentials; "
                f"missing or invalid: {joined}. "
                "See docs/upstash_integration.md and .env.example."
            )
            raise RuntimeError(msg)


def load_yaml_file(path: Path) -> JsonDict:
    """Load a single YAML file into a dict. Missing or empty files yield ``{}``."""
    if not path.exists() or path.stat().st_size == 0:
        return {}
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        msg = f"YAML root must be a mapping: {path}"
        raise ValueError(msg)
    return raw


def load_yaml_configs(configs_dir: Path | None = None) -> dict[str, JsonDict]:
    """Load all ``configs/*.yaml`` files keyed by stem name."""
    directory = resolve_configs_dir(configs_dir)
    result: dict[str, JsonDict] = {}
    if not directory.is_dir():
        return result
    for path in sorted(directory.glob("*.yaml")):
        result[path.stem] = load_yaml_file(path)
    return result


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    """Return cached process settings."""
    return Settings()


def ensure_data_plane(settings: Settings | None = None) -> Settings:
    """Return settings after ``validate_data_plane()`` (call from app lifespan).

    Fixer E / API lifespan should invoke this at startup. Skipped automatically
    when ``atlas_env`` is test/testing or ``atlas_data_plane`` is ``local``.
    """
    cfg = settings or get_settings()
    cfg.validate_data_plane()
    return cfg


def clear_settings_cache() -> None:
    """Drop the settings cache (tests and process reloads)."""
    get_settings.cache_clear()


def get_yaml_config(name: str, *, settings: Settings | None = None) -> JsonDict:
    """Return one YAML config document by stem (e.g. ``retrieval``)."""
    cfg = settings or get_settings()
    return load_yaml_file(cfg.configs_dir / f"{name}.yaml")


def merge_feature_flags(settings: Settings | None = None) -> dict[str, Any]:
    """Merge YAML feature flags with env overrides from Settings."""
    cfg = settings or get_settings()
    flags = dict(get_yaml_config("feature_flags", settings=cfg))
    env_flags = {
        "enable_query_rewrite": cfg.enable_query_rewrite,
        "enable_multi_query": cfg.enable_multi_query,
        "enable_mmr": cfg.enable_mmr,
        "enable_xgb_rerank": cfg.enable_xgb_rerank,
        "enable_agentic": cfg.enable_agentic,
        "enable_semantic_chunking": cfg.enable_semantic_chunking,
        "enable_response_cache": cfg.enable_response_cache,
    }
    flags.update(env_flags)
    return flags
