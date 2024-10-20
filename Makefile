ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY : restart fresh stop clean build run

black:
	python -m isort --sl --line-length 120 cbz_tagger tests
	python -m black --line-length 120 cbz_tagger tests

lint:
	python -m isort --sl --line-length 120 cbz_tagger tests
	python -m black --line-length 120 cbz_tagger tests
	python -m pylint cbz_tagger tests

test:
	python -m pytest tests/

build:
	docker build -t manga-tag .

run:
	docker run \
		-d \
		-v $(ROOT_DIR)/debug_image/config:/config \
		-v $(ROOT_DIR)/debug_image/downloads:/downloads \
		-v $(ROOT_DIR)/debug_image/storage:/storage \
		--name "manga-tag" \
		manga-tag

test-dirs:
	mkdir -p debug_image/config
	mkdir -p debug_image/downloads
	mkdir -p debug_image/storage

test-seed:
	rm -rf debug_image/downloads
	cp -r test/downloads debug_image

remove-test-dirs:
	rm -rf debug_image

stop:
	docker stop "manga-tag"
	docker rm "manga-tag"

clean:
	docker container prune -f
	docker image prune -af

clean-git:
	git fetch -p
	# for branch in $(git for-each-ref --format '%(refname) %(upstream:track)' refs/heads | awk '$2 == "[gone]" {sub("refs/heads/", "", $1); print $1}'); do git branch -D $branch; done

shell:
	docker exec -it manga-tag bash

logs:
	docker logs manga-tag

fresh: clean build run

restart: stop fresh

python-fresh:
	export CONFIG_PATH=debug_image/config & \
	export DOWNLOADS_PATH=debug_image/downloads & \
	export STORAGE_PATH=debug_image/storage & \
	python3 start.py