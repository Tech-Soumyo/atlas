# apps/worker

## Overview

Async ingest worker for Atlas. Runs an `arq` worker against Redis, handles `ingest_document`, and reconciles stale processing/running jobs on startup.

## Key files

| File | Owns |
|---|---|
| `src/atlas_worker/main.py` | `WorkerSettings`, startup/shutdown, Redis settings |
| `src/atlas_worker/handlers/ingest_document.py` | Ingest job handler |
| `src/atlas_worker/reconcile.py` | Stale Document/Job fail + artifact cleanup |
| `src/atlas_worker/settings.py` | Worker facing settings re export |
| `src/atlas_worker/handlers/` | Other job stubs (delete, reembed, cache invalidate) |
| `src/atlas_worker/dlq.py` | Dead letter path stub |
| `pyproject.toml` | `atlas-worker` package and `atlas-worker` script |

## Commands

```bash
# From repo root (same data plane env as the API)
uv run atlas-worker
```

## Conventions

- Keep handlers thin; call `packages/ingestion` and `packages/persistence` for real work.
- Startup must call `reconcile_stale_jobs` before consuming new work.
- Log with `atlas_common.logging` so API and worker share one shape.
- Enqueue payload is `{ "document_id" }` only; job row holds status and result.

## Gotchas

- Worker refuses start outside test when `ATLAS_API_KEY` is empty (same gate as the API).
- Empty extractable text fails the Job and Document (not an upload 4xx).
- Host `.env` cloud plane values need local overrides when Compose only runs postgres/redis/qdrant.

## Related specs

- [0001 Naive PDF to answer loop](../../docs/specs/0001-naive-pdf-answer-loop/index.md)

_Drafted by /audit from the repo, corrected by /sync for arq ingest. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
