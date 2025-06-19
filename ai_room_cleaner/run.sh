#!/usr/bin/with-contenv bashio

echo "Starting AI Room Cleaner..."

# Start the uvicorn server
uvicorn app.main:app --host 0.0.0.0 --port 8000