#!/usr/bin/with-contenv bashio

echo "Starting AI Room Cleaner addon"

# Get configuration options
CAMERA_ENTITY=$(bashio::config 'camera_entity')
API_KEY=$(bashio::config 'api_key')
AI_MODEL=$(bashio::config 'ai_model')
UPDATE_FREQUENCY=$(bashio::config 'update_frequency')
PROMPT=$(bashio::config 'prompt')

# Export for the Python application
export CAMERA_ENTITY
export API_KEY
export AI_MODEL
export UPDATE_FREQUENCY
export PROMPT

# Start the FastAPI application
uvicorn app.backend.main:app --host 0.0.0.0 --port 8000