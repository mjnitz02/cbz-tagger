FROM ghcr.io/linuxserver/baseimage-alpine:3.13

LABEL \
  maintainer="mjnitz02@gmail.com"

ENV \
    DOWNLOADS_PATH="/downloads" \
    STORAGE_PATH="/storage" \
    CONFIG_PATH="/config" \
    TIMER_MODE_DELAY="600"

### Upgrade ###
RUN \
  apk update && apk upgrade

### Manga Tagger ###
COPY cbz_tagger /app/cbz_tagger
COPY start.py /app/start.py
COPY requirements.txt /app/requirements.txt

### Dependencies ###
RUN   echo "Install dependencies" && \
    apk add --no-cache --update python3 py3-pip && \
    pip3 install --no-cache-dir -r /app/requirements.txt

RUN \
    echo "Adding aliases to container" && \
    echo -e '#!/bin/bash\npython3 /app/start.py --auto' > /usr/bin/auto && \
    chmod +x /usr/bin/auto && \
    echo -e '#!/bin/bash\npython3 /app/start.py --manual' > /usr/bin/manual && \
    chmod +x /usr/bin/manual

VOLUME /config
VOLUME /downloads
VOLUME /storage

ENTRYPOINT ["python3", "-u", "/app/start.py", "--entrymode"]