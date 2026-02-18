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
	uvx ty@0.0.14 check cbz_tagger

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

dev:
	@echo "Starting CBZ Tagger development servers..."
	@export LOG_LEVEL=INFO; \
	export DEBUG_MODE=true; \
	export TIMER_MODE=true; \
	export TIMER_DELAY=35; \
	export CONFIG_PATH=~/Downloads/cbz_tagger/config; \
	export SCAN_PATH=~/Downloads/cbz_tagger/scan; \
	export STORAGE_PATH=~/Downloads/cbz_tagger/storage; \
	mkdir -p $$CONFIG_PATH $$SCAN_PATH $$STORAGE_PATH; \
	echo "Starting FastAPI backend on port 8000..."; \
	uv run python -m cbz_tagger.web.server & \
	API_PID=$$!; \
	sleep 2; \
	echo "Starting NiceGUI frontend on port 8080..."; \
	uv run python -m cbz_tagger.gui.server || kill $$API_PID; \
	kill $$API_PID 2>/dev/null || true

run:
	export TIMER_MODE=true; \
	export TIMER_DELAY=600; \
	export GUI_MODE=true; \
	export LOG_LEVEL=INFO; \
	CONFIG_PATH=~/Downloads/cbz_tagger/config; \
	SCAN_PATH=~/Downloads/cbz_tagger/scan; \
	STORAGE_PATH=~/Downloads/cbz_tagger/storage; \
	mkdir -p $$CONFIG_PATH $$SCAN_PATH $$STORAGE_PATH; \
	uv run python run.py

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
