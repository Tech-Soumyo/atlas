"""API routers."""

from atlas_api.routers.ask import router as ask_router
from atlas_api.routers.documents import router as documents_router
from atlas_api.routers.health import router as health_router
from atlas_api.routers.jobs import router as jobs_router

__all__ = [
    "ask_router",
    "documents_router",
    "health_router",
    "jobs_router",
]
