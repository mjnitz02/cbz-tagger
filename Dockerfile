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

### Upgrade base packages and install uv ###
RUN apk update && apk upgrade && apk add --no-cache uv

WORKDIR /app

### Dependencies (cached unless pyproject.toml/uv.lock change) ###
COPY pyproject.toml uv.lock ./
RUN uv sync --no-cache --no-install-project

### CBZ Tagger ###
COPY . .
COPY --from=frontend-builder /app/frontend/dist /app/frontend/dist
RUN uv sync --no-cache

# Define volume mappings
VOLUME /config /scan /storage

EXPOSE 8080

CMD ["uv", "run", "python", "-m", "cbz_tagger.web.server"]
