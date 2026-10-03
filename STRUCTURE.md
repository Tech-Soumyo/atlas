# Atlas — Production File & Folder Structure

> Secured, scalable, maintainable monorepo layout for Phase 1 (RAG + thin Next.js) with room for Phase 2 layer upgrades.  
> Companions: [`PRD.md`](PRD.md) · [`TECH_STACK.md`](TECH_STACK.md)

| Principle | How this tree enforces it |
|-----------|---------------------------|
| **Secure** | Secrets only via env; `security` package; no credentials in git; ACL logic not buried in routes |
| **Scalable** | API / worker / web split; packages reusable; Compose → later K8s without rewrite |
| **Maintainable** | Domain packages own business logic; apps only wire I/O; tests mirror packages; ADRs for decisions |
| **Testable** | `packages/*` importable without Next.js or full Compose; evals isolated |

---

## 0. Scaffold in one command (Linux)

From the `atlas/` directory (idempotent; won’t wipe existing file contents):

```bash
bash scripts/scaffold_structure.sh
```

Or one-liner from anywhere:

```bash
bash /home/soumyo/Study/Docs/AI_Engineering_Interview/project_rag_end_to_end/atlas/scripts/scaffold_structure.sh
```

If you cloned elsewhere, replace the path with your `atlas` root:

```bash
cd /path/to/atlas && bash scripts/scaffold_structure.sh
```

---

## 1. Full tree

```text
atlas/
├── README.md
├── PRD.md
├── TECH_STACK.md
├── STRUCTURE.md                 ← this file
├── LICENSE
├── .gitignore
├── .env.example                 # no secrets — names + dummy values only
├── .dockerignore
├── Makefile                     # common targets: up, test, eval, lint
├── pyproject.toml               # workspace / shared Python tooling
├── package.json                 # optional root scripts for web
├── docker-compose.yml           # local prod-like stack
├── docker-compose.override.yml  # local-only overrides (gitignored optional)
│
├── .github/
│   └── workflows/
│       ├── ci.yml               # lint + pytest + eval gate
│       └── web-smoke.yml        # optional Playwright
│
├── deploy/
│   ├── docker/
│   │   ├── api.Dockerfile
│   │   ├── worker.Dockerfile
│   │   └── web.Dockerfile
│   └── k8s/                     # Phase 2 placeholders
│       └── README.md
│
├── configs/                     # versioned runtime config (non-secret)
│   ├── chunking.yaml
│   ├── retrieval.yaml
│   ├── models.yaml
│   ├── security.yaml
│   ├── observability.yaml
│   └── feature_flags.yaml
│
├── apps/
│   ├── api/                     # FastAPI — HTTP edge
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_api/
│   │           ├── __init__.py
│   │           ├── main.py              # app factory + lifespan
│   │           ├── dependencies.py      # auth, db, clients
│   │           ├── middleware/
│   │           │   ├── __init__.py
│   │           │   ├── request_context.py
│   │           │   ├── rate_limit.py
│   │           │   └── security_headers.py
│   │           ├── routers/
│   │           │   ├── __init__.py
│   │           │   ├── health.py
│   │           │   ├── documents.py
│   │           │   ├── jobs.py
│   │           │   ├── ask.py
│   │           │   ├── feedback.py
│   │           │   └── admin_evals.py
│   │           ├── schemas/             # API-layer DTOs (Pydantic)
│   │           │   ├── __init__.py
│   │           │   ├── documents.py
│   │           │   ├── ask.py
│   │           │   └── common.py
│   │           └── error_handlers.py
│   │
│   ├── worker/                  # Async ingest & maintenance jobs
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_worker/
│   │           ├── __init__.py
│   │           ├── main.py              # consumer entrypoint
│   │           ├── settings.py
│   │           ├── handlers/
│   │           │   ├── __init__.py
│   │           │   ├── ingest_document.py
│   │           │   ├── delete_document.py
│   │           │   ├── reembed.py
│   │           │   └── invalidate_cache.py
│   │           └── dlq.py
│   │
│   └── web/                     # Next.js — thin E2E UI
│       ├── package.json
│       ├── tsconfig.json
│       ├── next.config.ts
│       ├── .env.example
│       ├── README.md
│       ├── public/
│       ├── src/
│       │   ├── app/
│       │   │   ├── layout.tsx
│       │   │   ├── page.tsx             # redirect → /ask
│       │   │   ├── ask/page.tsx
│       │   │   ├── ingest/page.tsx
│       │   │   ├── jobs/[jobId]/page.tsx
│       │   │   └── api/                 # optional BFF proxies only if needed
│       │   ├── components/
│       │   │   ├── ask_panel.tsx
│       │   │   ├── citation_list.tsx
│       │   │   ├── upload_form.tsx
│       │   │   └── diagnostics_drawer.tsx
│       │   ├── lib/
│       │   │   ├── atlas_client.ts      # typed fetch to FastAPI
│       │   │   ├── auth.ts              # token/tenant session helpers
│       │   │   └── types.ts             # mirror API contracts
│       │   └── styles/
│       │       └── globals.css
│       └── tests/
│           └── e2e/
│               └── smoke_ask.spec.ts    # Playwright (optional)
│
├── packages/                    # Domain logic — no FastAPI/Next imports
│   ├── common/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_common/
│   │           ├── __init__.py
│   │           ├── config.py            # load YAML + env
│   │           ├── logging.py
│   │           ├── telemetry.py         # OpenTelemetry helpers
│   │           ├── types.py
│   │           ├── ids.py
│   │           └── clock.py
│   │
│   ├── security/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_security/
│   │           ├── __init__.py
│   │           ├── auth_context.py      # tenant_id, user_id, roles
│   │           ├── acl.py               # filter builders + enforce
│   │           ├── injection.py         # input / retrieved-text checks
│   │           ├── pii.py
│   │           └── audit.py
│   │
│   ├── ingestion/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_ingestion/
│   │           ├── __init__.py
│   │           ├── pipeline.py          # orchestrates stages
│   │           ├── loaders/
│   │           ├── parsers/
│   │           ├── cleaning.py
│   │           ├── chunking/
│   │           │   ├── fixed.py
│   │           │   ├── recursive.py
│   │           │   ├── semantic.py
│   │           │   └── parent_child.py
│   │           ├── metadata.py
│   │           └── versioning.py
│   │
│   ├── retrieval/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_retrieval/
│   │           ├── __init__.py
│   │           ├── models.py            # Hit, Candidate, QueryContext
│   │           ├── dense/
│   │           │   ├── embedder.py
│   │           │   └── qdrant_store.py
│   │           ├── sparse/
│   │           │   └── postgres_bm25.py
│   │           ├── hybrid/
│   │           │   ├── rrf.py
│   │           │   ├── weighted.py
│   │           │   └── mmr.py
│   │           ├── rerank/
│   │           │   ├── cross_encoder.py
│   │           │   └── xgboost_ranker.py  # M4+ gated
│   │           ├── query/
│   │           │   ├── rewrite.py
│   │           │   └── multi_query.py
│   │           └── service.py           # public façade for ask graph
│   │
│   ├── generation/
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_generation/
│   │           ├── __init__.py
│   │           ├── llm_client.py        # OpenAI-compatible adapter (gateway thin)
│   │           ├── prompts/
│   │           ├── context_budget.py
│   │           ├── ordering.py
│   │           ├── citations.py
│   │           ├── abstain.py
│   │           └── service.py
│   │
│   ├── orchestration/           # LangGraph graphs (ask / agentic)
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_orchestration/
│   │           ├── __init__.py
│   │           ├── state.py
│   │           ├── graphs/
│   │           │   ├── ask_graph.py     # Phase 1 linear/hybrid ask
│   │           │   └── agentic_rag.py   # M8 / Phase 2
│   │           └── nodes/
│   │               ├── rewrite.py
│   │               ├── retrieve.py
│   │               ├── rerank.py
│   │               ├── generate.py
│   │               └── guardrails.py
│   │
│   ├── persistence/             # DB / object store adapters
│   │   ├── pyproject.toml
│   │   ├── README.md
│   │   └── src/
│   │       └── atlas_persistence/
│   │           ├── __init__.py
│   │           ├── postgres/
│   │           │   ├── engine.py
│   │           │   ├── models.py        # SQLAlchemy / tables
│   │           │   ├── repositories/
│   │           │   └── migrations/      # alembic lives here or /migrations
│   │           ├── redis/
│   │           │   ├── client.py
│   │           │   ├── cache.py
│   │           │   └── queue.py
│   │           └── object_store/
│   │               └── local.py         # later: s3.py
│   │
│   └── evals/
│       ├── pyproject.toml
│       ├── README.md
│       └── src/
│           └── atlas_evals/
│               ├── __init__.py
│               ├── metrics/
│               │   ├── retrieval.py     # Recall@K, MRR, nDCG
│               │   └── generation.py    # Ragas wrappers + custom
│               ├── golden.py
│               ├── ablations.py
│               ├── attribution.py
│               └── runner.py
│
├── migrations/                  # Alembic root (Postgres schema)
│   ├── alembic.ini
│   ├── env.py
│   └── versions/
│
├── evals/                       # Data + runnable suites (not library code)
│   ├── golden/
│   │   ├── README.md
│   │   ├── corpus_manifest.json
│   │   └── qrels/
│   ├── adversarial/
│   │   └── injection_cases.json
│   ├── baselines/
│   │   └── .gitkeep             # committed metric snapshots
│   └── reports/                 # gitignored generated reports
│
├── tests/
│   ├── conftest.py
│   ├── unit/
│   │   ├── ingestion/
│   │   ├── retrieval/
│   │   ├── generation/
│   │   ├── security/
│   │   └── orchestration/
│   ├── integration/
│   │   ├── test_ask_api.py
│   │   ├── test_ingest_job.py
│   │   └── conftest.py          # Compose fixtures
│   ├── security/
│   │   ├── test_cross_tenant.py
│   │   └── test_filter_bypass.py
│   └── contract/
│       └── test_openapi_snapshots.py
│
├── scripts/
│   ├── bootstrap_dev.sh
│   ├── seed_demo_corpus.py
│   ├── run_evals.py
│   └── check_no_secrets.sh
│
├── docs/
│   ├── architecture.md
│   ├── code_explain_loop.md
│   ├── interview_talk_track.md
│   ├── security_model.md
│   ├── runbooks/
│   │   ├── ingest_failures.md
│   │   └── bad_answer_debug.md
│   └── adr/
│       ├── 0001_hybrid_rrf.md
│       └── README.md
│
└── data/                        # local runtime data — gitignored
    ├── raw/
    ├── processed/
    └── .gitkeep
```

---

## 2. Responsibility boundaries

| Path | May contain | Must NOT contain |
|------|-------------|------------------|
| `apps/api` | HTTP, auth wiring, DTO validation, status codes | Chunking math, RRF, prompts, SQL details |
| `apps/worker` | Queue consume, retries, job status updates | Next.js, HTTP route handlers |
| `apps/web` | UI + typed API client | Direct DB/Qdrant/Redis access |
| `packages/*` | Domain logic, pure-ish services | `os.environ` sprawl (use `common.config`), FastAPI `Request` |
| `configs/` | Tunables | API keys, passwords |
| `tests/unit` | Fast tests, no network | Live LLM calls |
| `evals/` | Golden data + reports | Application import cycles from `web` |

**Dependency direction (enforce in reviews):**

```text
apps/web        → FastAPI only (HTTP)
apps/api        → packages/* , persistence
apps/worker     → packages/* , persistence
packages/orchestration → retrieval, generation, security, common
packages/retrieval|ingestion|generation → common, security (ACL), persistence adapters
packages/*      ↛ apps/*
```

---

## 3. Security layout rules

1. **Never commit** `.env`, `*.pem`, service-account JSON, real API keys.  
2. **`.env.example`** lists variable *names* only; real values via local env / secret manager.  
3. **ACL enforcement** lives in `packages/security` + applied inside `packages/retrieval` (both sparse and dense paths) — not only in Next.js or a single router.  
4. **Audit events** written via `atlas_security.audit`, called from api/worker.  
5. **Retrieved text** treated as untrusted in `packages/security/injection.py` before tool use / sensitive prompts.  
6. `scripts/check_no_secrets.sh` runnable in CI.  
7. Next.js uses `NEXT_PUBLIC_ATLAS_API_URL` only for public API base; **no** embedding of server secrets in client bundles.

---

## 4. Scalability layout rules

| Concern | Structure choice |
|---------|------------------|
| Horizontal ask scale | Stateless `apps/api`; shared Redis/Postgres/Qdrant |
| Ingest spikes | `apps/worker` N replicas; Redis queue + DLQ module |
| Index growth | `retrieval/dense` + `sparse` isolated; reembed job handler |
| Phase 2 gateway | Add `packages/llm_gateway` later without moving ask routers |
| Phase 2 K8s | `deploy/k8s` consumes same Docker images from `deploy/docker` |

---

## 5. Maintainability conventions

| Convention | Standard |
|------------|----------|
| Python package import | `atlas_*` under `src/` layout |
| Modules | `snake_case.py` |
| Next components | `snake_case.tsx` or `kebab` folders; keep thin |
| Config keys | `snake_case` in YAML |
| Env vars | `UPPER_SNAKE` |
| ADRs | `docs/adr/NNNN_title.md` for every non-obvious trade-off |
| Feature flags | `configs/feature_flags.yaml` — no silent hard forks |
| Milestone code | Prefer vertical slice + tests; don’t invent `v2/` folders |

---

## 6. Mapping to milestones (what fills when)

| Milestone | Primary paths touched |
|-----------|----------------------|
| **M0** | `apps/*` skeletons, `packages/common`, `deploy/docker`, Compose, `tests/unit` smoke, `apps/web` shell |
| **M1** | `orchestration/graphs/ask_graph.py`, `generation/llm_client.py`, `routers/ask.py`, web ask page |
| **M2** | `packages/ingestion/**`, `worker/handlers/ingest_*`, web ingest |
| **M3** | `retrieval/dense`, `retrieval/sparse`, persistence repos |
| **M4** | `retrieval/hybrid`, `rerank`, query rewrite |
| **M5** | `generation/*` budget/cite/abstain; web citations |
| **M6** | `packages/evals`, `evals/golden`, CI workflow |
| **M7** | `packages/security`, cache invalidation, security tests |
| **M8** | `orchestration/graphs/agentic_rag.py`, docs talk track |

---

## 7. What stays out of the repo root

Avoid dumping notebooks, random scripts, or model weights at `atlas/` root.  
Put experiments under `docs/` or a future `experiments/` only if needed — prefer production paths above.

---

## 8. Quick commands (Makefile targets — planned)

```text
make up          # docker compose up --build
make down
make test        # unit + security
make test-int    # integration (Compose)
make eval        # golden suite
make lint
make migrate
make seed
```

---

## 9. Approval

Use this tree as the **source of truth** for scaffolding. PRD §12 should link here; do not invent parallel top-level layouts.
