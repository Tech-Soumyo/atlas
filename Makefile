.PHONY: help install install-web lint format typecheck test test-unit ci pre-commit-install up down

help: ## Show targets
	@grep -E '^[a-zA-Z_-]+:.*?##' $(MAKEFILE_LIST) | awk 'BEGIN {FS = ":.*?## "}; {printf "  %-18s %s\n", $$1, $$2}'

install: ## Install Python workspace + dev tools (uv)
	uv sync --group dev
	uv sync --all-packages --group dev

install-web: ## Install Next.js deps
	cd apps/web && npm install

lint: ## Ruff lint + ESLint
	uv run ruff check apps packages tests scripts
	cd apps/web && npm run lint

format: ## Ruff format + Prettier
	uv run ruff format apps packages tests scripts
	uv run ruff check --fix apps packages tests scripts
	cd apps/web && npm run format

typecheck: ## mypy strict + TypeScript check
	uv run mypy
	cd apps/web && npx tsc --noEmit

test: ## pytest (all)
	uv run pytest

test-unit: ## pytest unit only
	uv run pytest tests/unit

ci: ## Local CI gate (lint, types, tests)
	uv run ruff check apps packages tests scripts
	uv run ruff format --check apps packages tests scripts
	uv run mypy
	uv run pytest
	cd apps/web && npm run lint
	cd apps/web && npx tsc --noEmit

pre-commit-install: ## Install git hooks
	uv run pre-commit install

up: ## Start Compose stack (filled in during M0)
	docker compose up --build

down: ## Stop Compose stack
	docker compose down
