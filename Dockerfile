FROM ghcr.io/linuxserver/baseimage-alpine:3.13

LABEL \
  maintainer="matt@mattnitzken.com"

ENV \
    DOWNLOADS_PATH="/downloads" \
    STORAGE_PATH="/downloads" \
    CONFIG_PATH="/config" \
    ENABLE_CONTINUOUS_MODE="false" \
    ENABLE_TIMER_MODE="false" \
    TIMER_MODE_DELAY="600"

### Upgrade ###
RUN \
  apk update && apk upgrade

### Manga Tagger ###
COPY manga_tag /app/manga_tag
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
    chmod +x /usr/bin/manual && \
    echo -e '#!/bin/bash\npython3 /app/start.py --retag' > /usr/bin/retag && \
    chmod +x /usr/bin/retag

VOLUME /config
VOLUME /downloads
VOLUME /storage

ENTRYPOINT ["python3", "-u", "/app/start.py", "--entrymode"]