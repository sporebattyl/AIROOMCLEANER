#!/usr/bin/with-contenv bashio

echo "Starting AI Room Cleaner..."

# Navigate to the backend directory and start the uvicorn server
cd /app/app
uvicorn main:app --host 0.0.0.0 --port 8000