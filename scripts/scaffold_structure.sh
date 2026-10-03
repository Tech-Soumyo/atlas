#!/usr/bin/env bash
# Scaffold Atlas tree from STRUCTURE.md (idempotent).
# Usage:
#   cd /path/to/atlas && bash scripts/scaffold_structure.sh
#   # or from anywhere:
#   bash /path/to/atlas/scripts/scaffold_structure.sh

set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

echo "Scaffolding Atlas structure under: $ROOT"

# ---------------------------------------------------------------------------
# Directories
# ---------------------------------------------------------------------------
mkdir -p \
  .github/workflows \
  deploy/docker \
  deploy/k8s \
  configs \
  apps/api/src/atlas_api/middleware \
  apps/api/src/atlas_api/routers \
  apps/api/src/atlas_api/schemas \
  apps/worker/src/atlas_worker/handlers \
  apps/web/public \
  apps/web/src/app/ask \
  apps/web/src/app/ingest \
  "apps/web/src/app/jobs/[jobId]" \
  apps/web/src/app/api \
  apps/web/src/components \
  apps/web/src/lib \
  apps/web/src/styles \
  apps/web/tests/e2e \
  packages/common/src/atlas_common \
  packages/security/src/atlas_security \
  packages/ingestion/src/atlas_ingestion/loaders \
  packages/ingestion/src/atlas_ingestion/parsers \
  packages/ingestion/src/atlas_ingestion/chunking \
  packages/retrieval/src/atlas_retrieval/dense \
  packages/retrieval/src/atlas_retrieval/sparse \
  packages/retrieval/src/atlas_retrieval/hybrid \
  packages/retrieval/src/atlas_retrieval/rerank \
  packages/retrieval/src/atlas_retrieval/query \
  packages/generation/src/atlas_generation/prompts \
  packages/orchestration/src/atlas_orchestration/graphs \
  packages/orchestration/src/atlas_orchestration/nodes \
  packages/persistence/src/atlas_persistence/postgres/repositories \
  packages/persistence/src/atlas_persistence/postgres/migrations \
  packages/persistence/src/atlas_persistence/redis \
  packages/persistence/src/atlas_persistence/object_store \
  packages/evals/src/atlas_evals/metrics \
  migrations/versions \
  evals/golden/qrels \
  evals/adversarial \
  evals/baselines \
  evals/reports \
  tests/unit/ingestion \
  tests/unit/retrieval \
  tests/unit/generation \
  tests/unit/security \
  tests/unit/orchestration \
  tests/integration \
  tests/security \
  tests/contract \
  scripts \
  docs/runbooks \
  docs/adr \
  data/raw \
  data/processed

# ---------------------------------------------------------------------------
# Python package __init__.py
# ---------------------------------------------------------------------------
while IFS= read -r d; do
  touch "$d/__init__.py"
done <<'EOF'
apps/api/src/atlas_api
apps/api/src/atlas_api/middleware
apps/api/src/atlas_api/routers
apps/api/src/atlas_api/schemas
apps/worker/src/atlas_worker
apps/worker/src/atlas_worker/handlers
packages/common/src/atlas_common
packages/security/src/atlas_security
packages/ingestion/src/atlas_ingestion
packages/ingestion/src/atlas_ingestion/loaders
packages/ingestion/src/atlas_ingestion/parsers
packages/ingestion/src/atlas_ingestion/chunking
packages/retrieval/src/atlas_retrieval
packages/retrieval/src/atlas_retrieval/dense
packages/retrieval/src/atlas_retrieval/sparse
packages/retrieval/src/atlas_retrieval/hybrid
packages/retrieval/src/atlas_retrieval/rerank
packages/retrieval/src/atlas_retrieval/query
packages/generation/src/atlas_generation
packages/generation/src/atlas_generation/prompts
packages/orchestration/src/atlas_orchestration
packages/orchestration/src/atlas_orchestration/graphs
packages/orchestration/src/atlas_orchestration/nodes
packages/persistence/src/atlas_persistence
packages/persistence/src/atlas_persistence/postgres
packages/persistence/src/atlas_persistence/postgres/repositories
packages/persistence/src/atlas_persistence/redis
packages/persistence/src/atlas_persistence/object_store
packages/evals/src/atlas_evals
packages/evals/src/atlas_evals/metrics
EOF

# ---------------------------------------------------------------------------
# Placeholder files (touch only — does not overwrite existing content)
# ---------------------------------------------------------------------------
touch_if_missing() {
  local f="$1"
  if [[ ! -e "$f" ]]; then
    mkdir -p "$(dirname "$f")"
    : >"$f"
  fi
}

while IFS= read -r f; do
  [[ -z "$f" || "$f" =~ ^# ]] && continue
  touch_if_missing "$f"
done <<'EOF'
# root
LICENSE
.dockerignore
Makefile
pyproject.toml
package.json
docker-compose.yml

# github
.github/workflows/ci.yml
.github/workflows/web-smoke.yml

# deploy
deploy/docker/api.Dockerfile
deploy/docker/worker.Dockerfile
deploy/docker/web.Dockerfile
deploy/k8s/README.md

# configs
configs/chunking.yaml
configs/retrieval.yaml
configs/models.yaml
configs/security.yaml
configs/observability.yaml
configs/feature_flags.yaml

# api
apps/api/pyproject.toml
apps/api/README.md
apps/api/src/atlas_api/main.py
apps/api/src/atlas_api/dependencies.py
apps/api/src/atlas_api/error_handlers.py
apps/api/src/atlas_api/middleware/request_context.py
apps/api/src/atlas_api/middleware/rate_limit.py
apps/api/src/atlas_api/middleware/security_headers.py
apps/api/src/atlas_api/routers/health.py
apps/api/src/atlas_api/routers/documents.py
apps/api/src/atlas_api/routers/jobs.py
apps/api/src/atlas_api/routers/ask.py
apps/api/src/atlas_api/routers/feedback.py
apps/api/src/atlas_api/routers/admin_evals.py
apps/api/src/atlas_api/schemas/documents.py
apps/api/src/atlas_api/schemas/ask.py
apps/api/src/atlas_api/schemas/common.py

# worker
apps/worker/pyproject.toml
apps/worker/README.md
apps/worker/src/atlas_worker/main.py
apps/worker/src/atlas_worker/settings.py
apps/worker/src/atlas_worker/dlq.py
apps/worker/src/atlas_worker/handlers/ingest_document.py
apps/worker/src/atlas_worker/handlers/delete_document.py
apps/worker/src/atlas_worker/handlers/reembed.py
apps/worker/src/atlas_worker/handlers/invalidate_cache.py

# web
apps/web/package.json
apps/web/tsconfig.json
apps/web/next.config.ts
apps/web/.env.example
apps/web/README.md
apps/web/src/app/layout.tsx
apps/web/src/app/page.tsx
apps/web/src/app/ask/page.tsx
apps/web/src/app/ingest/page.tsx
apps/web/src/app/jobs/[jobId]/page.tsx
apps/web/src/components/ask_panel.tsx
apps/web/src/components/citation_list.tsx
apps/web/src/components/upload_form.tsx
apps/web/src/components/diagnostics_drawer.tsx
apps/web/src/lib/atlas_client.ts
apps/web/src/lib/auth.ts
apps/web/src/lib/types.ts
apps/web/src/styles/globals.css
apps/web/tests/e2e/smoke_ask.spec.ts

# packages/common
packages/common/pyproject.toml
packages/common/README.md
packages/common/src/atlas_common/config.py
packages/common/src/atlas_common/logging.py
packages/common/src/atlas_common/telemetry.py
packages/common/src/atlas_common/types.py
packages/common/src/atlas_common/ids.py
packages/common/src/atlas_common/clock.py

# packages/security
packages/security/pyproject.toml
packages/security/README.md
packages/security/src/atlas_security/auth_context.py
packages/security/src/atlas_security/acl.py
packages/security/src/atlas_security/injection.py
packages/security/src/atlas_security/pii.py
packages/security/src/atlas_security/audit.py

# packages/ingestion
packages/ingestion/pyproject.toml
packages/ingestion/README.md
packages/ingestion/src/atlas_ingestion/pipeline.py
packages/ingestion/src/atlas_ingestion/cleaning.py
packages/ingestion/src/atlas_ingestion/metadata.py
packages/ingestion/src/atlas_ingestion/versioning.py
packages/ingestion/src/atlas_ingestion/chunking/fixed.py
packages/ingestion/src/atlas_ingestion/chunking/recursive.py
packages/ingestion/src/atlas_ingestion/chunking/semantic.py
packages/ingestion/src/atlas_ingestion/chunking/parent_child.py

# packages/retrieval
packages/retrieval/pyproject.toml
packages/retrieval/README.md
packages/retrieval/src/atlas_retrieval/models.py
packages/retrieval/src/atlas_retrieval/service.py
packages/retrieval/src/atlas_retrieval/dense/embedder.py
packages/retrieval/src/atlas_retrieval/dense/qdrant_store.py
packages/retrieval/src/atlas_retrieval/sparse/postgres_bm25.py
packages/retrieval/src/atlas_retrieval/hybrid/rrf.py
packages/retrieval/src/atlas_retrieval/hybrid/weighted.py
packages/retrieval/src/atlas_retrieval/hybrid/mmr.py
packages/retrieval/src/atlas_retrieval/rerank/cross_encoder.py
packages/retrieval/src/atlas_retrieval/rerank/xgboost_ranker.py
packages/retrieval/src/atlas_retrieval/query/rewrite.py
packages/retrieval/src/atlas_retrieval/query/multi_query.py

# packages/generation
packages/generation/pyproject.toml
packages/generation/README.md
packages/generation/src/atlas_generation/llm_client.py
packages/generation/src/atlas_generation/context_budget.py
packages/generation/src/atlas_generation/ordering.py
packages/generation/src/atlas_generation/citations.py
packages/generation/src/atlas_generation/abstain.py
packages/generation/src/atlas_generation/service.py

# packages/orchestration
packages/orchestration/pyproject.toml
packages/orchestration/README.md
packages/orchestration/src/atlas_orchestration/state.py
packages/orchestration/src/atlas_orchestration/graphs/ask_graph.py
packages/orchestration/src/atlas_orchestration/graphs/agentic_rag.py
packages/orchestration/src/atlas_orchestration/nodes/rewrite.py
packages/orchestration/src/atlas_orchestration/nodes/retrieve.py
packages/orchestration/src/atlas_orchestration/nodes/rerank.py
packages/orchestration/src/atlas_orchestration/nodes/generate.py
packages/orchestration/src/atlas_orchestration/nodes/guardrails.py

# packages/persistence
packages/persistence/pyproject.toml
packages/persistence/README.md
packages/persistence/src/atlas_persistence/postgres/engine.py
packages/persistence/src/atlas_persistence/postgres/models.py
packages/persistence/src/atlas_persistence/redis/client.py
packages/persistence/src/atlas_persistence/redis/cache.py
packages/persistence/src/atlas_persistence/redis/queue.py
packages/persistence/src/atlas_persistence/object_store/local.py

# packages/evals
packages/evals/pyproject.toml
packages/evals/README.md
packages/evals/src/atlas_evals/metrics/retrieval.py
packages/evals/src/atlas_evals/metrics/generation.py
packages/evals/src/atlas_evals/golden.py
packages/evals/src/atlas_evals/ablations.py
packages/evals/src/atlas_evals/attribution.py
packages/evals/src/atlas_evals/runner.py

# migrations / evals data / tests / scripts / docs / data
migrations/alembic.ini
migrations/env.py
evals/golden/README.md
evals/golden/corpus_manifest.json
evals/adversarial/injection_cases.json
evals/baselines/.gitkeep
evals/reports/.gitkeep
tests/conftest.py
tests/integration/conftest.py
tests/integration/test_ask_api.py
tests/integration/test_ingest_job.py
tests/security/test_cross_tenant.py
tests/security/test_filter_bypass.py
tests/contract/test_openapi_snapshots.py
scripts/bootstrap_dev.sh
scripts/seed_demo_corpus.py
scripts/run_evals.py
scripts/check_no_secrets.sh
docs/architecture.md
docs/interview_talk_track.md
docs/security_model.md
docs/runbooks/ingest_failures.md
docs/runbooks/bad_answer_debug.md
docs/adr/0001_hybrid_rrf.md
docs/adr/README.md
data/raw/.gitkeep
data/processed/.gitkeep
data/.gitkeep
EOF

chmod +x scripts/scaffold_structure.sh scripts/bootstrap_dev.sh scripts/check_no_secrets.sh 2>/dev/null || true

echo "Done."
echo "Dirs:  $(find . -type d | wc -l)"
echo "Files: $(find . -type f | wc -l)"
echo "Tip: existing non-empty files were left unchanged (touch_if_missing)."
