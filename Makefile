ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

install:
	uv sync
	pre-commit install

lint:
	uv run ruff format .
	uv run ruff check . --fix
	uvx ty check cbz_tagger

test-lint:
	uv run ruff format . --check
	uv run ruff check .
	uvx ty check cbz_tagger

test:
	uv run pytest tests/ -W ignore::DeprecationWarning

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
