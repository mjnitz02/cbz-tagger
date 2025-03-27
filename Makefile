ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY : restart fresh stop clean build run

req:
	python -m pip install --upgrade pip
	python -m pip install poetry
	python -m poetry update

lint:
	python -m ruff check . --fix
	python -m ruff format .

test-lint:
	python -m ruff check .
	python -m ruff format . --check

test-unit:
	python -m pytest tests/

test-docker:
	docker build -t cbz-tagger .
	docker run --entrypoint "/bin/sh" cbz-tagger -c "python3 -m pytest /app/tests"

build-docker:
	docker build -t cbz-tagger .

run-docker:
	docker-compose up --build

clean-git:
	chmod +x ./scripts/clean_git.sh
	./scripts/clean_git.sh
