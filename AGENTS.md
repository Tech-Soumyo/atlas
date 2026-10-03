# Atlas

## Stack

- **Language / Runtime**: Python 3.12+ (API, worker, packages); TypeScript / Node (`apps/web`)
- **Framework**: FastAPI + Pydantic + Uvicorn; Next.js App Router; LangGraph ask graphs
- **Key dependencies**: PostgreSQL, Qdrant, Redis or Upstash, Sentence Transformers, Groq/Gemini/Ollama
- **Package manager**: uv/pip (Python); npm (`apps/web`)
- **Layout**: Monorepo — `apps/api`, `apps/worker`, `apps/web`; logic in `packages/*`

## Build approach

Skateboard (ship the smallest usable product, then grow it).

## Commands

```bash
make install          # uv sync workspace + dev tools
make install-web      # npm install in apps/web
make up               # docker compose up --build (forces ATLAS_DATA_PLANE=local)
make down
make test-unit        # pytest tests/unit (health + config smoke)
make test
make lint
make typecheck
make format            # Ruff format + Prettier
make pre-commit-install
make ci               # lint + types + tests + web lint/tsc

# Host API — cloud plane (default .env: Neon + Upstash)
# Tunnel worker HTTP first; set ATLAS_WORKER_PUBLIC_URL to the public HTTPS base
uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000
uv run uvicorn atlas_worker.http_app:app --host 0.0.0.0 --port 8001

# Host API — local plane (override when .env is cloud oriented)
ATLAS_DATA_PLANE=local DATABASE_URL=… REDIS_URL=… QDRANT_URL=… \
  uv run uvicorn atlas_api.main:app --host 0.0.0.0 --port 8000
uv run atlas-worker   # arq consumer (local Redis only)
cd apps/web && npm run dev
cd apps/web && npm run test:e2e
```

## Specs & docs workflow

Artifact base: `docs/` (see [`docs/README.md`](docs/README.md)).

| Path | Role |
|------|------|
| `docs/scope/` | Living feature plan (`/scope` → `scope.md`) |
| `docs/specs/` | Build specs (`/architect` → `NNNN-title.md` or `NNNN-title/`) |
| `docs/adr/` | Short ADRs for non-obvious trade-offs |
| `docs/releases/` | Release notes (`/document release-note`) |
| `docs/postmortems/` | Incident writeups (`/document postmortem`) |

Suggested loop: `/scope` → `/audit` → `/architect` → `/develop` → `/check verify` → `/test` → `/check review` → `/document` → `/sync`.

Current pass: M1 Naive RAG (see `docs/scope/_root/scope.md`). Workflow default there is GA.

## Tooling

For `/develop tooling`: Ruff + mypy strict; ESLint + Prettier (ESLint already in `apps/web`); pre-commit lint/format/typecheck; pytest (`tests/unit`, `tests/integration`); Playwright shell smoke in `apps/web` (`npm run test:e2e`); CI lint/typecheck/test on push.

## Git

- integration: on
- branch: stay on the current branch (usually `main`); do not create feature branches
- commit: per-milestone (offer commits; push only when asked)

## Rules

- Clean Architecture here: `packages/*` = domain/application; `apps/*` = presentation/I/O; persistence/clients = infrastructure. Apps → packages only; packages never import apps; no FastAPI/Next inside domain packages.
- Use cases behind package `service.py` façades. Cross boundary via Pydantic DTOs/plain objects. Unit test pure packages; integration test infrastructure.
- Strict types (mypy/TS `strict`, no `any`). Match scaffold folders. Document public APIs; consistent errors; validate env at startup.
- Naming: `atlas_*` under `src/`; snake_case Python; camelCase TS. Conventional commits.
- Config: read env and YAML only through `atlas_common.config` (`Settings`, `load_yaml_configs`); do not scatter `os.environ` in domain packages.
- API health: `/health` is liveness; `/ready` probes match `ATLAS_DATA_PLANE` (local: postgres/redis/qdrant; upstash: postgres/upstash_redis/upstash_vector/qstash). Network probes skipped when `ATLAS_ENV=test`.
- API lifespan: `ensure_data_plane()` / `validate_data_plane()` fail-fast in upstash; no arq pool; vector façade ensure; close Upstash Redis RL (+ QStash client cache) on shutdown.
- QStash ingest handlers: `atlas_worker.http_app` + `/internal/jobs/*` (not mounted on the API). Tunnel `ATLAS_WORKER_PUBLIC_URL` to that process.
- Compose: force `ATLAS_DATA_PLANE=local` and service DNS URLs in `docker-compose.yml` so a host cloud `.env` does not break the local data plane. Host default remains upstash via `.env`.
- Web → API: browser uses `NEXT_PUBLIC_ATLAS_API_URL`; server side (Compose) prefers `ATLAS_API_INTERNAL_URL` via `apps/web/lib/atlas_api.ts`.
- Atlas docs win over skill layouts; Context7 wins over stale snippets. Skill pick order: [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md).

## Agent skills

- [fastapi](~/.agents/skills/fastapi/): `fastapi/fastapi`, routes, deps, OpenAPI
- [fastapi-templates](~/.agents/skills/fastapi-templates/): `wshobson/agents`, API layout (STRUCTURE.md wins)
- [async-python-patterns](~/.agents/skills/async-python-patterns/): `wshobson/agents`, async API/worker/retrieve
- [langgraph-fundamentals](~/.agents/skills/langgraph-fundamentals/): `langchain-ai/langchain-skills`, ask graph
- [langgraph-persistence](~/.agents/skills/langgraph-persistence/): `langchain-ai/langchain-skills`, checkpoints/HITL
- [rag-implementation](~/.agents/skills/rag-implementation/): `wshobson/agents`, RAG pipeline design
- [llm-evaluation](~/.agents/skills/llm-evaluation/): `wshobson/agents`, eval harness / judges
- [python-testing-patterns](~/.agents/skills/python-testing-patterns/): `wshobson/agents`, pytest patterns
- [tdd](~/.agents/skills/tdd/): `mattpocock/skills`, red-green-refactor for pure logic
- [qdrant-clients-sdk](~/.agents/skills/qdrant-clients-sdk/): `qdrant/skills`, Qdrant client ops
- [upstash](~/.agents/skills/upstash/): `upstash/skills`, Upstash data plane mode
- [multi-stage-dockerfile](~/.agents/skills/multi-stage-dockerfile/): `github/awesome-copilot`, image hardening

MCP servers: context7 (connected)
Declined: arq, Playwright, PyMuPDF / sentence-transformers skill discovery (M1 sync; engineer chose skip)

## Context files

- [apps/web/AGENTS.md](apps/web/AGENTS.md): Next.js generated web UI agent rules (M1 has no upload/ask UI)
- [apps/api/AGENTS.md](apps/api/AGENTS.md): FastAPI HTTP edge (health, documents, jobs, ask)
- [apps/worker/AGENTS.md](apps/worker/AGENTS.md): arq ingest worker + stale job reconcile
- [packages/common/AGENTS.md](packages/common/AGENTS.md): Shared Settings, YAML, logging, types

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
