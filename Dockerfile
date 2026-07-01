FROM node:22-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

FROM python:3.13-alpine

LABEL maintainer="mjnitz02@gmail.com"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH="/config" \
    SCAN_PATH="/scan" \
    STORAGE_PATH="/storage" \
    PORT="8080"

### Upgrade ###
RUN apk update && apk upgrade

### CBZ Tagger ###
WORKDIR /app
COPY . /app
COPY pyproject.toml ./
COPY uv.lock ./
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist

### Dependencies ###
RUN echo "Install dependencies" && \
# These dependencies don't seem necessary when using uv, but leaving them commented out for reference
#    apk add --no-cache gcc libffi-dev musl-dev postgresql-dev zlib-dev jpeg-dev && \
    apk add --no-cache uv && \
    uv sync --no-cache

RUN chmod +x /app/docker-entrypoint.sh

# Define volume mappings
VOLUME /config /scan /storage

EXPOSE 8080

ENTRYPOINT ["/app/docker-entrypoint.sh"]
