#!/usr/bin/with-contenv bashio
set -ex

bashio::log.info "Starting AI Room Cleaner..."

if [ -z "$SUPERVISOR_TOKEN" ]; then
    bashio::log.warning "SUPERVISOR_TOKEN is not set. API calls to Home Assistant will likely fail."
else
    bashio::log.info "SUPERVISOR_TOKEN is set."
fi

# Start the uvicorn server
bashio::log.info "Activating virtual environment and starting server..."
# shellcheck disable=SC1091
source /opt/venv/bin/activate

export PYTHONPATH=/app
exec /opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000