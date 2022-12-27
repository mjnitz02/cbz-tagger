ROOT_DIR:=$(shell dirname $(realpath $(firstword $(MAKEFILE_LIST))))

.PHONY : restart fresh stop clean build run

build:
	docker build -t manga-tag .

run:
	mkdir -p debug_image/config
	mkdir -p debug_image/downloads
	mkdir -p debug_image/storage
	docker run \
		-d \
		-v $(ROOT_DIR)/debug_image/config:/config \
		-v $(ROOT_DIR)/debug_image/downloads:/downloads \
		-v $(ROOT_DIR)/debug_image/storage:/storage \
		--name "manga-tag" \
		manga-tag

stop:
	docker stop "manga-tag"
	docker rm "manga-tag"

clean:
	rm -rf debug_image
	docker container prune -f
	docker image prune -af

shell:
	docker exec -it manga-tag bash

logs:
	docker logs manga-tag

fresh: clean build run

restart: stop fresh