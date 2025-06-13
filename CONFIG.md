# AI Room Cleaner Configuration

This document outlines the configuration options for the AI Room Cleaner project. These settings can be configured in the `config.yaml` file or by using environment variables.

## Configuration Options

| Option | Environment Variable | Description | Example |
| :--- | :--- | :--- | :--- |
| **`camera_entity`** | `CAMERA_ENTITY` | The entity ID of the camera in Home Assistant that provides the room's image. | `camera.living_room_camera` |
| **`api_key`** | `API_KEY` | Your API key for the multimodal AI service (e.g., Google AI). | `your_secret_api_key` |
| **`ai_model`** | `AI_MODEL` | The specific AI model to use for analysis. | `gemini-1.5-pro` |
| **`update_frequency`** | `UPDATE_FREQUENCY` | The interval in minutes at which the room is checked for cleanliness. | `60` |
| **`supervisor_url`** | `SUPERVISOR_URL` | The URL of the Home Assistant Supervisor API. | `http://supervisor/core/api` |
| **`ai_prompt`** | `AI_PROMPT` | The prompt sent to the AI to guide its analysis of the room image. | `"Analyze this image and identify messes."` |
| **`cors_allowed_origins`** | `CORS_ALLOWED_ORIGINS` | A list of allowed origins for Cross-Origin Resource Sharing (CORS). Use `"*"` to allow all. | `["http://localhost:8123"]` |

## Example `config.yaml`

```yaml
# AI Room Cleaner Addon Configuration
name: "AI Room Cleaner"
version: "0.1.0"
slug: "ai_room_cleaner"
description: "An intelligent cleanliness assistant using a multimodal AI to keep your room tidy."
arch:
  - "aarch64"
  - "amd64"
  - "armv7"
init: false
panel_icon: "mdi:robot-vacuum"
ingress: true
ingress_port: 8000
startup: "application"
boot: "auto"
url: "https://github.com/hassio-addons/addon-ai-room-cleaner"
options:
  camera_entity: "camera.living_room_camera"
  api_key: "your_secret_api_key"
  ai_model: "gemini-1.5-pro"
  update_frequency: 60
  supervisor_url: "http://supervisor/core/api"
  ai_prompt: >-
    Analyze this room image for cleanliness. Identify items that are out of place or messy.
    Return the output as a JSON object with a single key "tasks".
    The "tasks" key should contain a list of objects, where each object has two keys: "mess" (a string describing the task) and "reason" (a brief explanation).
    Example: {"tasks": [{"mess": "Clothes on the floor", "reason": "Reduces tidiness and can wrinkle clothes."}]}
  cors_allowed_origins:
    - "*"
schema:
  camera_entity: "str"
  api_key: "password"
  ai_model: "str"
  update_frequency: "int(1,1440)"
  supervisor_url: "str"
  ai_prompt: "str"
  cors_allowed_origins: "list(str)"