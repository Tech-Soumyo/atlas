# apps/api

## Overview

FastAPI HTTP edge for Atlas. Live routes cover health, document upload/list/get, job poll, and ask (plus ask history). App code stays thin and calls into `packages/*` and `atlas_api.services`.

## Key files

| File | Owns |
|---|---|
| `src/atlas_api/main.py` | `create_app()` factory, lifespan, CORS, router mount |
| `src/atlas_api/routers/health.py` | `/health` liveness and `/ready` dependency probes |
| `src/atlas_api/routers/documents.py` | `POST/GET /v1/documents` (upload status from service code) |
| `src/atlas_api/routers/jobs.py` | `GET /v1/jobs/{job_id}` |
| `src/atlas_api/routers/ask.py` | `POST /v1/ask`, `GET /v1/asks/{ask_id}` |
| `src/atlas_api/services/documents.py` | Upload use case (sha256 branches, enqueue) |
| `src/atlas_api/dependencies.py` | Settings, DB session, `X-API-Key`, client IP |
| `src/atlas_api/schemas/` | Request/response models |
| `pyproject.toml` | `atlas-api` package and workspace deps |

## Commands

```bash
# From repo root (point DATABASE_URL/REDIS_URL/QDRANT_URL at a live data plane)
uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000
make test-unit
```

## Conventions

- Prefer `create_app()` for uvicorn and tests; do not grow a second app entry.
- Keep RAG logic out of routers; call package façades or `atlas_api.services`.
- Ask list length caps return HTTP 400 from the route (not Pydantic 422).
- Document POST sets `response.status_code` from the service (200 ready reupload, 202 accept).
- Read settings through `atlas_common.config`, never scatter `os.environ`.

## Gotchas

- `/ready` skips postgres, redis, and qdrant probes when `ATLAS_ENV=test`.
- Rate limits apply to upload and ask POSTs only; GETs are not limited.
- Compose forces local data plane URLs; a host cloud `.env` must not leak into the container data plane.
- Host runs need explicit local overrides when `.env` is cloud oriented (`ATLAS_DATA_PLANE=local`, local URLs).

## Related specs

- [0001 Naive PDF to answer loop](../../docs/specs/0001-naive-pdf-answer-loop/index.md)

_Drafted by /audit from the repo, corrected by /sync for M1 routes. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
