#!/usr/bin/with-contenv bashio

bashio::log.info "Starting AI Room Cleaner..."

# Get configuration
export LOG_LEVEL
LOG_LEVEL=$(bashio::config 'log_level')
export AI_PROVIDER
AI_PROVIDER=$(bashio::config 'ai_provider')
export OPENAI_API_KEY
OPENAI_API_KEY=$(bashio::config 'openai_api_key')
export OPENAI_MODEL
OPENAI_MODEL=$(bashio::config 'openai_model')
export AI_PROMPT
AI_PROMPT=$(bashio::config 'ai_prompt')
export CAMERA_ENTITY_ID
CAMERA_ENTITY_ID=$(bashio::config 'camera_entity_id')
export TODO_LIST_ENTITY_ID
TODO_LIST_ENTITY_ID=$(bashio::config 'todo_list_entity_id')
export SUPERVISOR_TOKEN="${SUPERVISOR_TOKEN}"

# Start the uvicorn server
exec uvicorn app.main:app --host 0.0.0.0 --port 8000