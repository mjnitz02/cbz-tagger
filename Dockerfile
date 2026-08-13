FROM node:26-alpine AS frontend-builder

WORKDIR /app/frontend
COPY frontend/package.json frontend/package-lock.json frontend/.npmrc ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

### Runtime image — this is what gets published to Docker Hub. It carries the
### [project.dependencies] only; test and lint tooling is excluded via --no-dev.
FROM python:3.13-alpine AS runtime

LABEL maintainer="mjnitz02@gmail.com"

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CONFIG_PATH="/config" \
    SCAN_PATH="/scan" \
    STORAGE_PATH="/storage" \
    PORT="8080"

### Upgrade base packages and install uv ###
RUN apk update && apk upgrade && apk add --no-cache uv

WORKDIR /app

### Dependencies (cached unless pyproject.toml/uv.lock change) ###
# --locked: install exactly what uv.lock pins and fail the build if uv.lock has
# drifted from pyproject.toml. Without it, `uv sync` will quietly re-resolve and
# rewrite the lock, so the image could ship versions that were never locked,
# never reviewed and never tested by CI.
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache --no-install-project --no-dev --locked

### CBZ Tagger ###
COPY . .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
RUN uv sync --no-cache --no-dev --locked

# Define volume mappings
VOLUME /config /scan /storage

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "cbz_tagger.web.server"]

### Test image — the runtime image plus the dev group, so the dockerised test
### targets exercise the exact layers that ship and then add pytest on top.
### Built with `--target test`; never published.
FROM runtime AS test

RUN uv sync --no-cache --locked
