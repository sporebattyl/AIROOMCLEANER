# AI Room Cleaner: Implementation Plan

This document outlines the synthesized plan for implementing the recommended fixes and improvements for the AI Room Cleaner application. The changes are consolidated from `recommended_fixes.md` and `Claudefixes/otherfixes.md`.

## Phase 1: Backend Refactoring

### 1.1. Configuration Management

*   **File to Modify**: `ai_room_cleaner/backend/core/config.py`
*   **Changes**:
    *   Refactor the `Settings` class to inherit from `pydantic_settings.BaseSettings`.
    *   Load configuration from environment variables (e.g., `API_KEY`, `CAMERA_ENTITY`).
    *   Add validation for critical settings to ensure they are not empty.
    *   Define a default for `CORS_ALLOWED_ORIGINS` that is more restrictive than `"*"`.

*   **File to Modify**: `ai_room_cleaner/requirements.txt`
*   **Changes**:
    *   Add `pydantic-settings` and `python-dotenv` to the dependencies.
    *   Pin all dependency versions to ensure reproducible builds (e.g., `fastapi==0.104.1`).

### 1.2. Application State

*   **File to Modify**: `ai_room_cleaner/backend/core/state.py`
*   **Changes**:
    *   Implement a `State` class to manage the lifecycle of shared resources, such as the AI service client.
    *   This will prevent re-initialization on every API request.

### 1.3. AI Service

*   **File to Modify**: `ai_room_cleaner/backend/services/ai_service.py`
*   **Changes**:
    *   Remove hardcoded API keys. The service should receive the `Settings` object or the API key directly from the application's configuration.
    *   Implement basic input sanitization for the AI prompt to prevent potential injection attacks.
    *   Convert the image processing logic to be asynchronous using `async/await` to avoid blocking the main thread.

### 1.4. API Router and Error Handling

*   **File to Modify**: `ai_room_cleaner/backend/api/router.py`
*   **Changes**:
    *   Implement robust error handling using FastAPI's exception handlers to catch application-specific exceptions and return clear, structured error responses.
    *   Add a `/health` endpoint that returns a `200 OK` status, which can be used for health checks.

### 1.5. Main Application

*   **File to Modify**: `ai_room_cleaner/backend/main.py`
*   **Changes**:
    *   Integrate the `State` management.
    *   Configure structured logging using `loguru` to ensure consistent and useful logs.

## Phase 2: Frontend Improvements

### 2.1. API Module

*   **File to Modify**: `ai_room_cleaner/frontend/modules/api.js`
*   **Changes**:
    *   Remove the hardcoded API endpoint URL.
    *   Create a function, e.g., `getApiBaseUrl()`, that fetches the backend URL from a configuration source or defaults to the current host.

### 2.2. UI Module

*   **File to Modify**: `ai_room_cleaner/frontend/modules/ui.js`
*   **Changes**:
    *   Refactor the DOM manipulation logic. Instead of many `document.getElementById` calls, create helper functions to update UI elements in a more structured manner. For example, a function `updateStatus(message, isError)` could handle updating a status display area.

### 2.3. Main Frontend Logic

*   **File to Modify**: `ai_room_cleaner/frontend/main.js`
*   **Changes**:
    *   Break down the `init` function into smaller, more manageable functions (e.g., `initializeUI`, `setupEventListeners`).

## Phase 3: General and DevOps

### 3.1. Docker Configuration

*   **File to Create**: `.dockerignore`
*   **Changes**:
    *   Create a `.dockerignore` file in the root directory to exclude `.git`, `__pycache__`, `.pytest_cache`, `*.md`, and other non-essential files from the Docker build context.

*   **File to Modify**: `ai_room_cleaner/Dockerfile`
*   **Changes**:
    *   Implement a proper multi-stage build. The first stage will install dependencies, and the final stage will copy only the necessary application code and dependencies from the builder stage.
    *   Remove hardcoded Python version paths.
    *   Add a `HEALTHCHECK` instruction that uses the new `/health` endpoint.

### 3.2. Shell Script

*   **File to Modify**: `ai_room_cleaner/run.sh`
*   **Changes**:
    *   Correct the configuration key from `prompt` to `ai_prompt`.
    *   Ensure the environment variable exported for the prompt is `AI_PROMPT` for consistency.

### 3.3. Testing

*   **File to Create**: `ai_room_cleaner/backend/tests/test_config.py`
*   **Changes**:
    *   Add a basic unit test to verify that the Pydantic settings load configuration correctly. This will serve as a starting point for a more comprehensive test suite.