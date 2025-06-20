# Home Assistant Addon Guardian: Cycle 2 Audit Report

This report details the findings of a static code audit of the AI Room Cleaner addon. The following issues were identified and require attention.

## Audit Checklist

### 1. Dockerfile Analysis

-   **[HIGH] DL3006: Pin Image Versions**
    -   **File:** `ai_room_cleaner/Dockerfile`
    -   **Line:** 3
    -   **Issue:** The base image `python:3.9-slim-buster` is not pinned to a specific digest.
    -   **Recommendation:** Pin the image to a specific digest to ensure reproducible builds. For example: `FROM python:3.9-slim-buster@sha256:abc...`

### 2. Shell Script Analysis

-   **[MEDIUM] SC1017: Carriage Returns**
    -   **File:** `ai_room_cleaner/run.sh`
    -   **Issue:** The script contains literal carriage returns, which can cause execution failures in Unix-like environments.
    -   **Recommendation:** Convert the line endings from CRLF to LF. This can be done using the `dos2unix` utility or by configuring your editor to save with LF line endings.

-   **[LOW] SC1008: Unrecognized Shebang**
    -   **File:** `ai_room_cleaner/run.sh`
    -   **Issue:** The shebang `#!/usr/bin/with-contenv bashio` is not recognized by `shellcheck`.
    -   **Recommendation:** This is expected in the Home Assistant environment and can be safely ignored.

### 3. Configuration Review

-   **[HIGH] Indentation Error**
    -   **File:** `ai_room_cleaner/config.yaml`
    -   **Line:** 17
    -   **Issue:** The `openai_api_key` option is not correctly indented under the `options` key.
    -   **Recommendation:** Indent `openai_api_key` to align with the other options.

### 4. Source Code Review

-   **[MEDIUM] Deprecated FastAPI Event Handler**
    -   **File:** `ai_room_cleaner/app/main.py`
    -   **Issue:** The `@app.on_event("startup")` decorator is deprecated and will be removed in future versions of FastAPI.
    -   **Recommendation:** Move the startup logic into the `lifespan` context manager, which is already partially implemented in the file.