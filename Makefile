ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: install lint-format lint-check lint-typing

install:
	uv sync

pre-commit-install:
	pre-commit install

update-packages:
	uv sync --upgrade

lint-format:
	uv run ruff format .

lint-check:
	uv run ruff check . --fix

lint-yaml:
	uvx yamlfix .github cbz_tagger tests docker-compose.yaml .pre-commit-config.yaml

lint-typing:
	uvx ty@0.0.14 check cbz_tagger

lint:
	$(MAKE) lint-format
	$(MAKE) lint-check
	$(MAKE) lint-typing
	$(MAKE) lint-yaml

test-lint:
	uv run ruff format . --check
	uv run ruff check .
	uvx yamlfix .github cbz_tagger tests docker-compose.yaml .pre-commit-config.yaml --check
	uvx ty check cbz_tagger

test:
	echo "Running tests locally"
	uv run pytest tests/ -W ignore::DeprecationWarning
	echo "Building Docker image for testing"
	docker build -t cbz-tagger .
	echo "Running tests in Docker"
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/ -W ignore::DeprecationWarning"

test-unit:
	uv run pytest tests/test_unit/ -W ignore::DeprecationWarning

test-integration:
	@echo "Starting API server..."
	@uv run python -m cbz_tagger.api.server & echo $$! > /tmp/cbz-tagger-api.pid
	@sleep 3
	@echo "Running integration tests..."
	@uv run pytest tests/test_integration/ -W ignore::DeprecationWarning; \
	TEST_EXIT=$$?; \
	echo "Stopping API server..."; \
	kill `cat /tmp/cbz-tagger-api.pid` 2>/dev/null || true; \
	rm -f /tmp/cbz-tagger-api.pid; \
	exit $$TEST_EXIT

# API Server targets
run-api:
	uv run python -m cbz_tagger.api.server

run-api-dev:
	uv run uvicorn cbz_tagger.api.app:app --host 0.0.0.0 --port 8000 --reload

run-frontend:
	export GUI_MODE=true && uv run run.py

test-unit-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

test-integration-docker:
	docker build -t cbz-tagger .
	docker run -e CBZ_TAGGER_SKIP_INTEGRATION_TESTS --entrypoint "/bin/sh" cbz-tagger -c "\
		cd /app && \
		uv run python -m cbz_tagger.api.server & \
		sleep 3 && \
		uv run pytest /app/tests/test_integration/ -W ignore::DeprecationWarning; \
		TEST_EXIT=\$$?; \
		kill %1 2>/dev/null || true; \
		exit \$$TEST_EXIT"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
