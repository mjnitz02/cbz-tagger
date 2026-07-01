#!/bin/sh
set -e

# Change to the app directory
cd /app

echo "Starting CBZ Tagger..."
echo "Config path: $CONFIG_PATH"
echo "Scan path: $SCAN_PATH"
echo "Storage path: $STORAGE_PATH"
echo "Starting server on port ${PORT:-8080}..."

exec uv run python -m cbz_tagger.web.server
