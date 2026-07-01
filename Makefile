SHELL := /usr/bin/env bash
.SHELLFLAGS := -eu -o pipefail -c

.DEFAULT_GOAL := help

.PHONY: help install pre-commit-install update-packages \
	lint-format lint-check lint-yaml lint-typing lint test-lint \
	frontend-install frontend-lint frontend-test-lint frontend-test frontend-build frontend-generate-api \
	test test-unit test-integration test-unit-docker test-integration-docker \
	build-docker run-docker dev run clean-git

help: ## Show this help message
	@awk 'BEGIN {FS = ":.*##"; printf "\nUsage:\n  make \033[36m<target>\033[0m\n"} \
		/^[a-zA-Z0-9_-]+:.*##/ { printf "  \033[36m%-24s\033[0m %s\n", $$1, $$2 } \
		/^##@/ { printf "\n\033[1m%s\033[0m\n", substr($$0, 5) }' $(MAKEFILE_LIST)

##@ Setup

install: ## Install project dependencies with uv
	uv sync

pre-commit-install: ## Install pre-commit git hooks
	pre-commit install

update-packages: ## Upgrade all dependencies to their latest compatible versions
	uv sync --upgrade

##@ Linting

lint-format: ## Format code with ruff
	uv run ruff format .

lint-check: ## Run ruff checks and auto-fix issues
	uv run ruff check . --fix

lint-yaml: ## Fix YAML formatting across the repo
	uvx yamlfix .github cbz_tagger tests docker-compose.yaml .pre-commit-config.yaml

lint-typing: ## Run static type checking with ty
	uvx ty@0.0.14 check cbz_tagger

lint: lint-format lint-check lint-typing lint-yaml frontend-lint ## Run all linters and auto-fix issues

test-lint: ## Check formatting/lint/types without modifying files (CI mode)
	uv run ruff format . --check
	uv run ruff check .
	uvx yamlfix .github cbz_tagger tests docker-compose.yaml .pre-commit-config.yaml --check
	uvx ty@0.0.14 check cbz_tagger
	$(MAKE) frontend-test-lint

##@ Frontend

frontend-install: ## Install frontend dependencies
	cd frontend && npm ci

frontend-lint: ## Format and lint the frontend, auto-fixing issues
	cd frontend && npm run format
	cd frontend && npm run lint

frontend-test-lint: ## Check frontend formatting/lint/types without modifying files (CI mode)
	cd frontend && npm run format:check
	cd frontend && npm run lint:check
	cd frontend && npx tsc -b --noEmit

frontend-test: ## Run frontend unit/component tests
	cd frontend && npm run test

frontend-build: ## Build the frontend static assets
	cd frontend && npm run build

frontend-generate-api: ## Regenerate the typed TS API client from FastAPI's OpenAPI schema
	uv run python -m scripts.export_openapi_schema
	cd frontend && npx openapi-typescript openapi.json -o src/lib/api-schema.ts

##@ Testing

test: build-docker ## Run the full test suite locally and in Docker
	@echo "Running tests locally"
	uv run pytest tests/ -W ignore::DeprecationWarning
	@echo "Running tests in Docker"
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/ -W ignore::DeprecationWarning"

test-unit: ## Run unit tests locally
	uv run pytest tests/test_unit/ -W ignore::DeprecationWarning

test-integration: ## Run integration tests locally
	uv run pytest tests/test_integration/ -W ignore::DeprecationWarning

test-unit-docker: build-docker ## Run unit tests inside a Docker container
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

test-integration-docker: build-docker ## Run integration tests inside a Docker container
	docker run -e CBZ_TAGGER_SKIP_INTEGRATION_TESTS --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_integration/ -W ignore::DeprecationWarning"

##@ Docker

build-docker: ## Build the cbz-tagger Docker image
	docker build -t cbz-tagger .

run-docker: ## Run cbz-tagger via docker-compose
	docker-compose up --build

##@ Local development

dev: ## Run the API, GUI, and frontend dev servers locally
	@echo "Starting CBZ Tagger development servers..."
	@export LOG_LEVEL=INFO; \
	export DEBUG_MODE=true; \
	export TIMER_DELAY=35; \
	export CONFIG_PATH=~/Downloads/cbz_tagger/config; \
	export SCAN_PATH=~/Downloads/cbz_tagger/scan; \
	export STORAGE_PATH=~/Downloads/cbz_tagger/storage; \
	mkdir -p $$CONFIG_PATH $$SCAN_PATH $$STORAGE_PATH; \
	echo "Starting FastAPI backend on port 8000..."; \
	uv run python -m cbz_tagger.web.server & \
	API_PID=$$!; \
	sleep 2; \
	echo "Starting Vite frontend dev server on port 5173..."; \
	(cd frontend && npm run dev) & \
	VITE_PID=$$!; \
	echo "Starting NiceGUI frontend on port 8080..."; \
	uv run python -m cbz_tagger.gui.server || (kill $$API_PID $$VITE_PID 2>/dev/null; true); \
	kill $$API_PID $$VITE_PID 2>/dev/null || true

run: ## Run the standalone tagger script locally
	@export TIMER_DELAY=600; \
	export LOG_LEVEL=INFO; \
	export CONFIG_PATH=~/Downloads/cbz_tagger/config; \
	export SCAN_PATH=~/Downloads/cbz_tagger/scan; \
	export STORAGE_PATH=~/Downloads/cbz_tagger/storage; \
	mkdir -p $$CONFIG_PATH $$SCAN_PATH $$STORAGE_PATH; \
	uv run python run.py

##@ Maintenance

clean-git: ## Delete local branches that no longer exist on the remote
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
