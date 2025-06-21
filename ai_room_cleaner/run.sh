#!/usr/bin/with-contenv bashio

bashio::log.info "Starting AI Room Cleaner..."

# Set the Python Path (optional with cd, but good practice)
export PYTHONPATH=/app

bashio::log.info "Activating virtual environment and starting server..."

# Change the current working directory to the app's root
cd /app || exit 1

# Execute the application from within its directory
# This allows Python's module discovery to work as intended.
exec /opt/venv/bin/uvicorn main:app --host 0.0.0.0 --port 8000