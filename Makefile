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
	uvx ty@0.0.14 check cbz_tagger --exclude 'cbz_tagger/reflex_gui/**'

lint:
	$(MAKE) lint-format
	$(MAKE) lint-check
	$(MAKE) lint-typing
	$(MAKE) lint-yaml

test-lint:
	uv run ruff format . --check
	uv run ruff check .
	uvx yamlfix .github cbz_tagger tests docker-compose.yaml .pre-commit-config.yaml --check
	uvx ty check cbz_tagger --exclude 'cbz_tagger/reflex_gui/**'

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
	uv run pytest tests/test_integration/ -W ignore::DeprecationWarning

test-unit-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

test-integration-docker:
	docker build -t cbz-tagger .
	docker run -e CBZ_TAGGER_SKIP_INTEGRATION_TESTS --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_integration/ -W ignore::DeprecationWarning"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh

dev:
	@echo "Starting Reflex GUI in development mode"
	@echo "Access the app at http://localhost:8080"
	GUI_MODE=true TIMER_DELAY=600 USE_REFLEX=true \
	CONFIG_PATH=./config SCAN_PATH=./scan STORAGE_PATH=./storage \
	uv run reflex run --reload
