#!/bin/sh
set -e

# Change to the app directory
cd /app

echo "Starting CBZ Tagger servers..."
echo "Config path: $CONFIG_PATH"
echo "Scan path: $SCAN_PATH"
echo "Storage path: $STORAGE_PATH"

# Start FastAPI backend in the background
echo "Starting FastAPI backend on port 8000..."
uv run python -m cbz_tagger.web.server &
API_PID=$!

# Give the API server a moment to start
sleep 2

# Start NiceGUI frontend in the foreground
echo "Starting NiceGUI frontend on port 8080..."
uv run python -m cbz_tagger.gui.server &
GUI_PID=$!

# Function to handle shutdown
shutdown() {
    echo "Shutting down servers..."
    kill $API_PID 2>/dev/null || true
    kill $GUI_PID 2>/dev/null || true
    exit 0
}

# Trap SIGTERM and SIGINT signals
trap shutdown TERM INT

# Wait for both processes
wait $GUI_PID $API_PID
