# apps/worker

## Overview

Async ingest worker for Atlas.

- **Local plane** (`ATLAS_DATA_PLANE=local`): `arq` worker against Redis; handles `ingest_document`; reconciles stale jobs on startup.
- **Upstash plane** (`ATLAS_DATA_PLANE=upstash`): FastAPI HTTP app (`http_app.py`) receives QStash deliveries at `/internal/jobs/ingest` (+ failure callback), with signature verification.

## Key files

| File | Owns |
|---|---|
| `src/atlas_worker/main.py` | arq `WorkerSettings`, startup/shutdown (local Redis) |
| `src/atlas_worker/http_app.py` | QStash HTTP worker (`create_app`, lifespan, mounts internal routers) |
| `src/atlas_worker/routers/internal_jobs.py` | `POST /internal/jobs/ingest` + `/ingest-failed` |
| `src/atlas_worker/qstash_verify.py` | `Receiver` signature verify helper |
| `src/atlas_worker/handlers/ingest_document.py` | Ingest job handler (shared by arq + QStash) |
| `src/atlas_worker/reconcile.py` | Stale Document/Job fail + artifact cleanup |
| `src/atlas_worker/settings.py` | Worker facing settings re export |
| `src/atlas_worker/handlers/` | Other job stubs (delete, reembed, cache invalidate) |
| `src/atlas_worker/dlq.py` | Dead letter path stub |
| `pyproject.toml` | `atlas-worker` package; scripts `atlas-worker`, `atlas-worker-http` |

## Commands

```bash
# Local plane (Redis arq)
ATLAS_DATA_PLANE=local uv run atlas-worker

# Upstash / QStash plane — atlas-worker gates to uvicorn HTTP automatically
# Tunnel this port as ATLAS_WORKER_PUBLIC_URL, e.g.:
#   cloudflared tunnel --url http://localhost:8001
ATLAS_DATA_PLANE=upstash ATLAS_WORKER_PORT=8001 uv run atlas-worker
# equivalent:
uv run uvicorn atlas_worker.http_app:app --host 0.0.0.0 --port 8001
```

## Conventions

- Keep handlers thin; call `packages/ingestion` and `packages/persistence` for real work.
- Startup must call `reconcile_stale_jobs` before consuming new work.
- Log with `atlas_common.logging` so API and worker share one shape.
- Enqueue payload is `{ "document_id" }` (+ optional `job_id`); job row holds status and result.
- Always verify `Upstash-Signature` on internal routes (current + next signing keys).

## Gotchas

- Worker refuses start outside test when `ATLAS_API_KEY` is empty (same gate as the API).
- Empty extractable text fails the Job and Document (not an upload 4xx).
- Do not run `atlas-worker` (arq) against Upstash Redis REST — use `http_app` + QStash.
- `ATLAS_WORKER_PUBLIC_URL` must be the public HTTPS base QStash can reach (tunnel in local cloud-mode dev).
- Compose forces local plane; host cloud `.env` is for uv host processes, not container overrides.

## Related specs

- [0001 Naive PDF to answer loop](../../docs/specs/0001-naive-pdf-answer-loop/index.md)

_Drafted by /audit from the repo, corrected by /sync for arq + QStash HTTP ingest. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
