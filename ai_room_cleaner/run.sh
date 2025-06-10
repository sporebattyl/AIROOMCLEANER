#!/usr/bin/env bash

echo "Starting AI Room Cleaner addon"

# Get configuration options
CAMERA_ENTITY_ID=$(bashio::config 'camera_entity')
OPENAI_API_KEY=$(bashio::config 'api_key')
AI_MODEL=$(bashio::config 'ai_model')
UPDATE_FREQUENCY=$(bashio::config 'update_frequency')
PROMPT=$(bashio::config 'prompt')

# Export for the Python application
export CAMERA_ENTITY_ID
export OPENAI_API_KEY
export AI_MODEL
export UPDATE_FREQUENCY
export PROMPT
export SUPERVISOR_TOKEN

# Start the FastAPI application
python3 -u /app/backend/main.py