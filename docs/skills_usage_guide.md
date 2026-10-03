# Atlas — When to Use Which Skill

> Playbook for the priority skills installed for this project.  
> Companions: [`../PRD.md`](../PRD.md) · [`../TECH_STACK.md`](../TECH_STACK.md) · [`code_explain_loop.md`](code_explain_loop.md)

Skills live under `~/.agents/skills/<name>/`. Invoke by name / `@skill` in Cursor when the task matches the **Use when** column.

---

## Quick matrix (by milestone)

| Milestone | Primary skills | Optional |
|-----------|----------------|----------|
| **M0** Foundations | `fastapi`, `fastapi-templates`, `multi-stage-dockerfile`, `tdd` | `async-python-patterns` |
| **M1** Naive RAG | `rag-implementation`, `langgraph-fundamentals`, `fastapi` | `langgraph-persistence` |
| **M2** Ingest | `fastapi`, `async-python-patterns`, `tdd` | `upstash` (if QStash mode) |
| **M3** Indexes | `qdrant-clients-sdk`, `rag-implementation` | `upstash` (Vector mode) |
| **M4** Hybrid + rerank | `rag-implementation`, `langgraph-fundamentals` | `qdrant-clients-sdk` |
| **M5** Context + gen | `rag-implementation`, `langgraph-fundamentals` | — |
| **M6** Evals | `llm-evaluation`, `python-testing-patterns`, `tdd` | — |
| **M7** Security + prod | `async-python-patterns`, `python-testing-patterns`, `multi-stage-dockerfile` | `upstash` (Redis cache) |
| **M8** Agentic / design | `langgraph-persistence`, `langgraph-fundamentals`, `rag-implementation` | — |
| **Next.js UI anytime** | Context7 + your Next/React skills (not in this priority pack) | Playwright skills later |
| **Docs / APIs** | **Context7 MCP** (always prefer for library truth) | — |

---

## Skill catalog

### 1. `fastapi` (official FastAPI)

| | |
|--|--|
| **Path** | `~/.agents/skills/fastapi` |
| **Use when** | Designing or implementing routes, dependencies, request/response models, lifespan, status codes, OpenAPI quirks |
| **Atlas paths** | `apps/api/src/atlas_api/**` |
| **Don’t use for** | RAG retrieval math, LangGraph graph design, Dockerfiles |
| **Pair with** | `fastapi-templates`, Context7 for latest FastAPI docs |

---

### 2. `fastapi-templates`

| | |
|--|--|
| **Path** | `~/.agents/skills/fastapi-templates` |
| **Use when** | Scaffolding API layout, project structure patterns, routers/services split |
| **Atlas paths** | `apps/api/`, aligning with [`STRUCTURE.md`](../STRUCTURE.md) |
| **Don’t use for** | Overriding Atlas monorepo layout — STRUCTURE.md wins |
| **Pair with** | `fastapi` |

---

### 3. `async-python-patterns`

| | |
|--|--|
| **Path** | `~/.agents/skills/async-python-patterns` |
| **Use when** | Concurrent dense+sparse retrieve, async DB/Redis/httpx, worker concurrency, avoiding blocking the event loop |
| **Atlas paths** | `apps/api`, `apps/worker`, `packages/retrieval`, `packages/persistence` |
| **Don’t use for** | Sync CPU-heavy embedding/rerank internals (use thread/process pools carefully) |
| **Pair with** | `fastapi`, `python-testing-patterns` |

---

### 4. `langgraph-fundamentals` (LangChain AI)

| | |
|--|--|
| **Path** | `~/.agents/skills/langgraph-fundamentals` |
| **Use when** | Building/editing the ask graph: nodes, edges, state shape, rewrite→retrieve→rerank→generate |
| **Atlas paths** | `packages/orchestration/**` |
| **Don’t use for** | Putting business logic only in API routers — keep logic in packages |
| **Pair with** | `langgraph-persistence`, `rag-implementation`, Context7 LangGraph docs |

---

### 5. `langgraph-persistence`

| | |
|--|--|
| **Path** | `~/.agents/skills/langgraph-persistence` |
| **Use when** | Checkpoints, resumable runs, multi-turn / agentic state, HITL pauses (M8 / Phase 2) |
| **Atlas paths** | `packages/orchestration/graphs/agentic_rag.py`, durable ask later |
| **Don’t use for** | Stateless single-shot ask in M1 unless you already need checkpoints |
| **Pair with** | `langgraph-fundamentals` |

---

### 6. `rag-implementation`

| | |
|--|--|
| **Path** | `~/.agents/skills/rag-implementation` |
| **Use when** | Chunking, indexing, retrieval, hybrid/rerank patterns, grounded generation design |
| **Atlas paths** | `packages/ingestion`, `packages/retrieval`, `packages/generation` |
| **Don’t use for** | Blindly adopting LangChain/LlamaIndex as the whole app — Atlas owns packages |
| **Pair with** | `qdrant-clients-sdk`, `llm-evaluation`, [`Questions_RAG_120.md`](../../Questions_RAG_120.md) |

---

### 7. `llm-evaluation`

| | |
|--|--|
| **Path** | `~/.agents/skills/llm-evaluation` |
| **Use when** | Golden sets, faithfulness/relevance judges, eval harness design, CI gates (M6) |
| **Atlas paths** | `packages/evals`, `evals/golden`, CI workflow |
| **Don’t use for** | Replacing nDCG/MRR/Recall@K — keep retrieval metrics custom; use this for gen-side + methodology |
| **Pair with** | `python-testing-patterns`, Ragas (TECH_STACK), free-tier quota rules in `zero_cost_showcase.md` |

---

### 8. `python-testing-patterns`

| | |
|--|--|
| **Path** | `~/.agents/skills/python-testing-patterns` |
| **Use when** | pytest layout, fixtures, unit vs integration, mocking external APIs |
| **Atlas paths** | `tests/unit`, `tests/integration`, `tests/security` |
| **Don’t use for** | Skipping ACL/security tests — those stay mandatory |
| **Pair with** | `tdd` |

---

### 9. `tdd`

| | |
|--|--|
| **Path** | `~/.agents/skills/tdd` |
| **Use when** | Starting a new package function (RRF, ACL filter, budgeter, citation parse) — red→green→refactor |
| **Atlas paths** | Any `packages/*` pure logic |
| **Don’t use for** | Exploratory spikes where you’re still learning an API (spike first, then TDD the settled interface) |
| **Pair with** | `python-testing-patterns`, [`code_explain_loop.md`](code_explain_loop.md) |

---

### 10. `qdrant-clients-sdk` (official Qdrant)

| | |
|--|--|
| **Path** | `~/.agents/skills/qdrant-clients-sdk` |
| **Use when** | Collections, upsert, filtered search, payload schema, local Compose Qdrant |
| **Atlas paths** | `packages/retrieval/dense/qdrant_store.py` |
| **Don’t use for** | Upstash Vector mode — use `upstash` + Context7 instead |
| **Pair with** | `rag-implementation` |

---

### 11. `upstash` (official)

| | |
|--|--|
| **Path** | `~/.agents/skills/upstash` |
| **Use when** | `ATLAS_DATA_PLANE=upstash`: Redis cache, Vector, QStash wiring |
| **Atlas paths** | adapters in `packages/persistence`, `packages/retrieval`, worker enqueue |
| **Don’t use for** | Default local Compose path — keep Redis/Qdrant containers |
| **Pair with** | [`upstash_integration.md`](upstash_integration.md), Context7 |

---

### 12. `multi-stage-dockerfile`

| | |
|--|--|
| **Path** | `~/.agents/skills/multi-stage-dockerfile` |
| **Use when** | Writing/hardening `deploy/docker/api.Dockerfile`, `worker.Dockerfile`, `web.Dockerfile` |
| **Atlas paths** | `deploy/docker/**`, Compose build contexts |
| **Don’t use for** | Application business logic |
| **Pair with** | Compose file, `.dockerignore` |

---

## Always-on tools (not in the priority pack, but required)

| Tool / skill | Use when |
|--------------|----------|
| **Context7 MCP** | Any library API question (FastAPI, LangGraph, Qdrant, Upstash, Ragas, Next.js) — prefer over memory |
| **Atlas PRD / STRUCTURE / TECH_STACK** | Architecture and scope conflicts — docs beat generic skill advice |
| **code_explain_loop + Questions_RAG_120** | After each slice — interview explain step |

---

## Decision rules (resolve conflicts)

1. **Atlas docs win** over a skill’s default folder layout.  
2. **Context7 wins** over a skill’s outdated API snippets.  
3. **Thin packages > framework takeover** — skills may suggest LangChain/LlamaIndex everywhere; keep logic in `packages/*`.  
4. **One skill per task** — don’t stack `rag-implementation` + three LangGraph skills for a one-line fix.  
5. **TDD for pure functions**; integration tests for Compose boundaries.

---

## Example session recipes

### “Add health + settings for M0”
1. `fastapi-templates` (structure check)  
2. `fastapi` (route + lifespan)  
3. `multi-stage-dockerfile` (api image)  
4. `tdd` + `python-testing-patterns` (health test)

### “Implement hybrid retrieve node”
1. `rag-implementation` (pattern)  
2. `qdrant-clients-sdk` (dense filtered query)  
3. `async-python-patterns` (parallel sparse+dense)  
4. `langgraph-fundamentals` (wire node)  
5. `tdd` (RRF unit tests)  
6. Explain with `Questions_RAG_120` Q41–Q43

### “Eval CI gate”
1. `llm-evaluation` (methodology)  
2. `python-testing-patterns` (pytest suite)  
3. Keep retrieval metrics in `atlas_evals` (custom)  
4. Watch Groq/Gemini quotas (`zero_cost_showcase.md`)

### “Switch cache to Upstash Redis”
1. Read `upstash_integration.md`  
2. `upstash` skill  
3. Context7 for Python REST client  
4. Adapter behind `packages/persistence/redis`

---

## Install reminder

If a skill is missing from `~/.agents/skills/`:

```bash
npx skills add <owner/repo@skill> -g -y
```

Priority set is listed in the project chat history / skills install session (fastapi, langgraph-*, rag-implementation, etc.).

---

## Changelog

| Date | Note |
|------|------|
| 2026-10-03 | Initial guide for 12 priority Atlas skills |
