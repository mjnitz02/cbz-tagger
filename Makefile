ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY : restart fresh stop clean build run

req:
	uv sync

lint:
	uv run ruff check . --fix
	uv run ruff format .

test-lint:
	uv run ruff check .
	uv run ruff format . --check

test:
	uv run pytest tests/ -W ignore::DeprecationWarning

test-unit:
	uv run pytest tests/test_unit/ -W ignore::DeprecationWarning

test-integration:
	uv run pytest tests/test_integration/ -W ignore::DeprecationWarning

test-docker:
	docker run --entrypoint "/bin/sh" cbz-tagger -c "uv run pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
