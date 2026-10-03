# apps/api

## Overview

FastAPI HTTP edge for Atlas. Live routes cover health, document upload/list/get, job poll, and ask (plus ask history). App code stays thin and calls into `packages/*` and `atlas_api.services`.

## Key files

| File | Owns |
|---|---|
| `src/atlas_api/main.py` | `create_app()` factory, lifespan (`ensure_data_plane`), CORS, router mount |
| `src/atlas_api/routers/health.py` | `/health` liveness and plane-aware `/ready` probes |
| `src/atlas_api/routers/documents.py` | `POST/GET /v1/documents` (upload status from service code) |
| `src/atlas_api/routers/jobs.py` | `GET /v1/jobs/{job_id}` |
| `src/atlas_api/routers/ask.py` | `POST /v1/ask`, `GET /v1/asks/{ask_id}` |
| `src/atlas_api/services/documents.py` | Upload use case (sha256 branches, `enqueue_ingest_document`) |
| `src/atlas_api/dependencies.py` | Settings, DB session, `X-API-Key`, client IP |
| `src/atlas_api/schemas/` | Request/response models |
| `pyproject.toml` | `atlas-api` package and workspace deps |

## Commands

```bash
# Cloud plane (default .env): Neon + Upstash. Worker QStash targets are separate.
uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000

# Local plane against Compose/services on localhost
ATLAS_DATA_PLANE=local uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000

make test-unit
```

## Conventions

- Prefer `create_app()` for uvicorn and tests; do not grow a second app entry.
- Keep RAG logic out of routers; call package façades or `atlas_api.services`.
- Ask list length caps return HTTP 400 from the route (not Pydantic 422).
- Document POST sets `response.status_code` from the service (200 ready reupload, 202 accept).
- Read settings through `atlas_common.config`, never scatter `os.environ`.
- Upload enqueue goes through `atlas_persistence.redis.queue.enqueue_ingest_document` (arq local / QStash upstash).

## Gotchas

- Lifespan calls `ensure_data_plane()` — missing Upstash/Neon/QStash env fails startup (not in `ATLAS_ENV=test`).
- Upstash mode: no arq pool; `/ready` checks postgres + Upstash Redis/Vector + QStash; rate-limit client closed on shutdown.
- Local mode: `/ready` checks postgres + Redis TCP + Qdrant; arq pool closed on shutdown.
- QStash `/internal/jobs/*` is **not** on this app — see `atlas_worker.http_app` and tunnel `ATLAS_WORKER_PUBLIC_URL`.
- Compose forces local data plane URLs; a host cloud `.env` must not leak into the container data plane.
- Host cloud runs: leave `ATLAS_DATA_PLANE=upstash` in `.env`; do not point Compose containers at Neon unless you intend to.

## Related specs

- [0001 Naive PDF to answer loop](../../docs/specs/0001-naive-pdf-answer-loop/index.md)

_Drafted by /audit from the repo, corrected by /sync for M1 routes + cloud-plane wiring. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
