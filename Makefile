ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY: install lint-format lint-check lint-typing

install:
	uv sync

precommit:
	pre-commit install

lint-format:
	uv run ruff format .

lint-check:
	uv run ruff check . --fix

lint-typing:
	uvx ty check cbz_tagger

lint:
	$(MAKE) lint-format
	$(MAKE) lint-check
	$(MAKE) lint-typing

test-lint:
	uv run ruff format . --check
	uv run ruff check .
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
	uv run pytest tests/test_integration/ -W ignore::DeprecationWarning

test-unit-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

test-integration-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_integration/ -W ignore::DeprecationWarning"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
