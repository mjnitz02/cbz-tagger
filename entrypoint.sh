#!/bin/sh
set -e

# Change to the app directory
cd /app

echo "Starting CBZ Tagger services..."

# Start the FastAPI backend server in the background
echo "Starting FastAPI backend on port 8000..."
uv run python -m cbz_tagger.api.server &
FASTAPI_PID=$!

# Wait a moment for the API server to start
sleep 2

# Check if FastAPI server is running
if ! kill -0 $FASTAPI_PID 2>/dev/null; then
    echo "ERROR: FastAPI server failed to start"
    exit 1
fi

echo "FastAPI backend started successfully (PID: $FASTAPI_PID)"

# Start the GUI frontend
echo "Starting GUI frontend..."
exec uv run /app/run.py --entrymode
