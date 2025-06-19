# AI Room Cleaner - Home Assistant Addon Audit (Cycle 1)

This report details the findings from the initial static code audit of the AI Room Cleaner Home Assistant addon. The following is a checklist of proposed changes to address the identified issues.

## Dockerfile (`ai_room_cleaner/Dockerfile`)

- [ ] **DL3006:** Pin the base image version explicitly. Instead of `FROM python:3.9-slim-buster`, specify a digest or a more specific tag like `FROM python:3.9.18-slim-buster`.
- [ ] **DL3018:** Pin versions of packages installed with `apk add`. For example, instead of `apk add --no-cache gcc`, use `apk add --no-cache gcc=<version>`.

## Shell Script (`ai_room_cleaner/run.sh`)

- [ ] **SC1008 & SC1017:** The shebang `#!/usr/bin/with-contenv bashio` is not standard and is causing issues with `shellcheck`. While necessary for Home Assistant addons, the script also contains Windows-style line endings (CRLF). The line endings should be converted to Unix-style (LF).
- [ ] **SC2164:** The `cd /app/app` command should include error handling to prevent the script from continuing if the directory change fails. It should be changed to `cd /app/app || exit 1`.

## Python Code (`ai_room_cleaner/app/`)

- [ ] **Architectural Improvement:** The `main.py` file directly instantiates service classes (`HomeAssistantService`, `CameraService`, `AIService`, `HistoryService`). It should instead use the provided dependency injection functions (`get_ha_service`, `get_camera_service`, etc.) from `dependencies.py` to improve modularity and testability.

## Configuration (`ai_room_cleaner/config.yaml`)

- [ ] No issues found. The configuration file is well-structured and adheres to the Home Assistant addon schema.