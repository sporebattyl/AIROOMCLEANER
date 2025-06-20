#!/usr/bin/with-contenv bashio
set -ex

bashio::log.info "Starting AI Room Cleaner..."

# Configuration is now handled by the application

# Start the uvicorn server
echo "Activating virtual environment..."
# shellcheck disable=SC1091
source /opt/venv/bin/activate

echo "Current working directory: $(pwd)"
echo "Listing contents of /app:"
ls -l /app
export PYTHONPATH=/
exec /opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000

sleep infinity