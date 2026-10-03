# Atlas

## Stack

- **Language / Runtime**: Python 3.12+ (API, worker, packages); TypeScript / Node (`apps/web`)
- **Framework**: FastAPI + Pydantic + Uvicorn; Next.js App Router; LangGraph ask graphs
- **Key dependencies**: PostgreSQL, Qdrant, Redis or Upstash, Sentence Transformers, Groq/Gemini/Ollama
- **Package manager**: uv/pip (Python); npm (`apps/web`)
- **Layout**: Monorepo — `apps/api`, `apps/worker`, `apps/web`; logic in `packages/*`

## Build approach

<TBD, set by /scope>

## Commands

```bash
# Install (wired by /develop tooling)
# uv sync   # or pip install -e …
cd apps/web && npm install

# Dev
docker compose up --build
cd apps/web && npm run dev

# Test / lint (Makefile targets via /develop tooling)
pytest
ruff check . && ruff format --check . && mypy .
cd apps/web && npm run lint
```

## Specs

Stored in `docs/specs/`. Format: `docs/specs/NNNN-title.md`.

## Tooling

For `/develop tooling`: Ruff + mypy strict; ESLint + Prettier (ESLint already in `apps/web`); pre-commit lint/format/typecheck; pytest + later Playwright smoke; CI lint/typecheck/test on push.

## Git

- integration: on
- branch: stay on the current branch (usually `main`); do not create feature branches
- commit: per-milestone (offer commits; push only when asked)

## Rules

- Clean Architecture here: `packages/*` = domain/application; `apps/*` = presentation/I/O; persistence/clients = infrastructure. Apps → packages only; packages never import apps; no FastAPI/Next inside domain packages.
- Use cases behind package `service.py` façades. Cross boundary via Pydantic DTOs/plain objects. Unit test pure packages; integration test infrastructure.
- Strict types (mypy/TS `strict`, no `any`). Match scaffold folders. Document public APIs; consistent errors; validate env at startup.
- Naming: `atlas_*` under `src/`; snake_case Python; camelCase TS. Conventional commits.
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

## Context files

- [apps/web/AGENTS.md](apps/web/AGENTS.md): Next.js generated web UI agent rules

_Drafted by /audit from the repo, worth a quick human pass. Edit freely: once a line stops matching this draft, later runs treat it as curated and will flag rather than overwrite it._
