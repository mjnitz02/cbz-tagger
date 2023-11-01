FROM python:3.11-alpine

LABEL maintainer="mjnitz02@gmail.com"

# set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV CONFIG_PATH "/config"
ENV SCAN_PATH "/scan"
ENV STORAGE_PATH "/storage"
ENV TIMER_MODE_DELAY "600"

### Upgrade ###
RUN apk update && apk upgrade

### Manga Tagger ###
COPY cbz_tagger /app/cbz_tagger
COPY run.py /app/run.py
COPY requirements.txt /app/requirements.txt

### Dependencies ###
RUN   echo "Install dependencies"
RUN   apk add -u zlib-dev jpeg-dev gcc musl-dev
RUN   python3 -m pip install --upgrade pip
# RUN   apk add --no-cache --update python3 py3-pip
RUN   pip3 install --no-cache-dir -r /app/requirements.txt

### Container Aliases ###
RUN echo "Adding aliases to container"
RUN echo -e '#!/bin/sh\npython3 /app/run.py --auto' > /usr/bin/auto
RUN chmod +x /usr/bin/auto
RUN echo -e '#!/bin/sh\npython3 /app/run.py --manual' > /usr/bin/manual
RUN chmod +x /usr/bin/manual
RUN echo -e '#!/bin/sh\npython3 /app/run.py --refresh' > /usr/bin/refresh
RUN chmod +x /usr/bin/refresh

### Volume Mappings ###
VOLUME /config
VOLUME /scan
VOLUME /storage

ENTRYPOINT ["python3", "-u", "/app/run.py", "--entrymode"]
