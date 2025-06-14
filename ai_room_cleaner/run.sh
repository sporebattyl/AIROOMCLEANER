#!/usr/bin/env bash
set -e

echo "Starting AI Room Cleaner addon"

# Source bashio if available
if [ -f /usr/bin/bashio ]; then
    source /usr/lib/bashio/bashio.sh
    
    # Get configuration options using bashio
    CAMERA_ENTITY_ID=$(bashio::config 'camera_entity')
    API_KEY=$(bashio::config 'api_key')
    AI_MODEL=$(bashio::config 'ai_model')
    UPDATE_FREQUENCY=$(bashio::config 'update_frequency')
    PROMPT=$(bashio::config 'prompt')
    
    echo "Configuration loaded via bashio"
else
    echo "Warning: bashio not available, using environment variables"
    # Fallback to environment variables if bashio is not available
    CAMERA_ENTITY_ID=${CAMERA_ENTITY_ID:-"camera.example"}
    API_KEY=${API_KEY:-""}
    AI_MODEL=${AI_MODEL:-"gemini-1.5-pro"}
    UPDATE_FREQUENCY=${UPDATE_FREQUENCY:-60}
    PROMPT=${PROMPT:-"Analyze this room for cleanliness and identify items that need attention."}
fi

# Export variables for the Python application
export CAMERA_ENTITY_ID
export GOOGLE_API_KEY="$API_KEY"
export OPENAI_API_KEY="$API_KEY"  # Support both API types
export AI_MODEL
export UPDATE_FREQUENCY
export PROMPT

# Get supervisor token if available (for Home Assistant)
if [ -n "$SUPERVISOR_TOKEN" ]; then
    export SUPERVISOR_TOKEN
else
    echo "Warning: SUPERVISOR_TOKEN not available"
fi

# Log configuration (without exposing API key)
echo "Camera Entity ID: $CAMERA_ENTITY_ID"
echo "AI Model: $AI_MODEL"
echo "Update Frequency: $UPDATE_FREQUENCY minutes"
echo "API Key configured: $([ -n "$API_KEY" ] && echo "Yes" || echo "No")"

# Change to the correct directory
cd /app

if [ "$1" == "test" ]; then
    echo "Running tests..."
    pip install -r requirements-dev.txt
    pytest
else
    # Start the FastAPI application
    echo "Starting FastAPI server..."
    exec python3 -m uvicorn backend.main:app --host 0.0.0.0 --port 8000 --log-level info
fi