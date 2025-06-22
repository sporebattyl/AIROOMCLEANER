#!/usr/bin/with-contenv bashio

echo "Starting AI Room Cleaner addon"

# Get config values
CONFIG_PATH=/data/options.json

export LOG_LEVEL=$(bashio::config 'log_level')
export AI_PROVIDER=$(bashio::config 'ai_provider')
export OPENAI_API_KEY=$(bashio::config 'openai_api_key')
export GOOGLE_API_KEY=$(bashio::config 'google_api_key')
export AI_MODEL=$(bashio::config 'ai_model')
export PROMPT=$(bashio::config 'prompt')
export CAMERA_ENTITY=$(bashio::config 'camera_entity')
export CLEANLINESS_SENSOR_ENTITY=$(bashio::config 'cleanliness_sensor_entity')
export TODO_LIST_ENTITY=$(bashio::config 'todo_list_entity')
export RUN_INTERVAL_MINUTES=$(bashio::config 'run_interval_minutes')

# Start the application
exec python -m app.main