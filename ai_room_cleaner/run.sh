#!/usr/bin/env bash

bashio::log.info "Starting AI Room Cleaner..."

# Configuration is now handled by the application

# Start the uvicorn server
echo "Activating virtual environment..."
# shellcheck disable=SC1091
source /opt/venv/bin/activate

echo "Current working directory: $(pwd)"
echo "Listing contents of /app:"
ls -l /app
exec uvicorn app.main:app --host 0.0.0.0 --port 8000