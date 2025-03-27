FROM python:3.12-alpine

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

### CBZ Tagger ###
COPY . /app

### Dependencies ###
RUN echo "Install dependencies"
RUN apk add --no-cache gcc libffi-dev musl-dev postgresql-dev zlib-dev jpeg-dev
RUN python3 -m pip install --upgrade pip

### Python Environment ###
COPY pyproject.toml poetry.lock ./
RUN pip install "poetry==2.1.1"
RUN pip install poetry-plugin-export
# Poetry is a pain in docker, so export and use basic requirements.txt
# when building the image. This could be revised in the future, but it
# messes with the entrypoint commands really badly if using pure poetry.
RUN poetry export -f requirements.txt --output requirements.txt
RUN pip install -r requirements.txt

### Container Aliases ###
RUN echo "Adding aliases to container"
RUN echo -e '#!/bin/sh\npython3 /app/run.py --auto' > /usr/bin/auto
RUN chmod +x /usr/bin/auto
RUN echo -e '#!/bin/sh\npython3 /app/run.py --manual' > /usr/bin/manual
RUN chmod +x /usr/bin/manual
RUN echo -e '#!/bin/sh\npython3 /app/run.py --refresh' > /usr/bin/refresh
RUN chmod +x /usr/bin/refresh
RUN echo -e '#!/bin/sh\npython3 /app/run.py --add' > /usr/bin/add
RUN chmod +x /usr/bin/add
RUN echo -e '#!/bin/sh\npython3 /app/run.py --remove' > /usr/bin/remove
RUN chmod +x /usr/bin/remove
RUN echo -e '#!/bin/sh\npython3 /app/run.py --delete' > /usr/bin/delete
RUN chmod +x /usr/bin/delete

### Volume Mappings ###
VOLUME /config
VOLUME /scan
VOLUME /storage

ENTRYPOINT ["python", "-u", "/app/run.py", "--entrymode"]

