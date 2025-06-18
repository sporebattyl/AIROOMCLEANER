#!/usr/bin/with-contenv bashio

echo "Starting AI Room Cleaner..."

# The main application is started by the Dockerfile's CMD instruction.
# This script is here for compatibility and future extensions.
# For example, you could add logic to check for configuration
# or run pre-flight checks here.

# Keep the script running if needed, though with CMD this is not strictly necessary
# while true; do
#   sleep 60
# done