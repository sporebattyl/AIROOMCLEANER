#!/usr/bin/env bashio

bashio::log.info "Starting AI Room Cleaner..."

# Configuration is now handled by the application

# Start the uvicorn server
echo "Current working directory: $(pwd)"
echo "Listing contents of /app:"
ls -l /app
exec /opt/venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000