# Atlas

Production-oriented multi-tenant hybrid RAG platform (Phase 1: RAG + thin Next.js).

| Doc | Purpose |
|-----|---------|
| [`PRD.md`](PRD.md) | Product requirements & milestones |
| [`TASKLIST.md`](TASKLIST.md) | High-level end-to-end task checklist |
| [`TECH_STACK.md`](TECH_STACK.md) | Stack, libs, package inventory |
| [`STRUCTURE.md`](STRUCTURE.md) | File/folder layout & boundaries |
| [`docs/zero_cost_showcase.md`](docs/zero_cost_showcase.md) | ₹0 showcase (Groq/Gemini + local infra) |
| [`docs/upstash_integration.md`](docs/upstash_integration.md) | Optional Upstash Redis / Vector / QStash |
| [`docs/code_explain_loop.md`](docs/code_explain_loop.md) | Code → interview explain ritual |
| [`docs/skills_usage_guide.md`](docs/skills_usage_guide.md) | When to use which installed agent skill |
| [`../topics.md`](../topics.md) | 120 RAG topics |
| [`../Questions_RAG_120.md`](../Questions_RAG_120.md) | 120 interview questions |

## Layout (short)

```text
apps/api       FastAPI edge
apps/worker    Async ingest
apps/web       Next.js E2E UI
packages/*     Domain logic (independently testable)
configs/       Non-secret tunables
tests/         Unit / integration / security
evals/         Golden data + reports
deploy/docker  Containerfiles
```

See [`STRUCTURE.md`](STRUCTURE.md) for the full tree and dependency rules.

## Tooling (quick)

```bash
# Python workspace (uv) + Ruff / mypy / pytest / pre-commit
make install
make pre-commit-install

# Next.js deps + Prettier
make install-web

# Local CI gate
make ci
```

Useful targets: `make lint`, `make format`, `make typecheck`, `make test`.

## Status

Scaffolded for **M0**. Tooling is wired; next is Compose + health + package wiring.
