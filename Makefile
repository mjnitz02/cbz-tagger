ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY : restart fresh stop clean build run

req:
	python -m pip install --upgrade pip
	python -m pip install poetry
	python -m poetry update

lint:
	poetry run ruff check . --fix
	poetry run ruff format .

test-lint:
	poetry run ruff check .
	poetry run ruff format . --check

test-unit:
	poetry run pytest tests/ -W ignore::DeprecationWarning

test-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "python3 -m pytest /app/tests/test_unit/ -W ignore::DeprecationWarning"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
