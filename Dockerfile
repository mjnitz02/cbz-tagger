FROM python:3.13-alpine

LABEL maintainer="mjnitz02@gmail.com"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH="/config" \
    SCAN_PATH="/scan" \
    STORAGE_PATH="/storage" \
    TIMER_MODE_DELAY="600"

### Upgrade ###
RUN apk update && apk upgrade

### CBZ Tagger ###
COPY . /app
COPY pyproject.toml ./
COPY uv.lock ./

### Dependencies ###
RUN echo "Install dependencies" && \
# These dependencies don't seem necessary when using uv, but leaving them commented out for reference
#    apk add --no-cache gcc libffi-dev musl-dev postgresql-dev zlib-dev jpeg-dev && \
    apk add --no-cache uv nodejs npm && \
    uv sync --no-cache

### Container Aliases ###
RUN echo "Adding aliases to container" && \
    for cmd in auto manual refresh add remove delete; do \
        echo -e '#!/bin/sh\nuv run /app/run.py --'$cmd > /usr/bin/$cmd && \
        chmod +x /usr/bin/$cmd; \
    done

# Define volume mappings
VOLUME /config /scan /storage

ENTRYPOINT ["uv", "run", "/app/run.py", "--entrymode"]
