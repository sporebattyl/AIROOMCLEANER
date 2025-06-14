# AI Room Cleaner: Prioritized Action Plan

This document outlines the prioritized action plan to address the findings from the `Code_Review_Report.md`. Issues are ordered by priority to ensure that the most critical items are addressed first.

---

## 1. [CRITICAL] Frontend: API Keys Exposed in Client-Side Code

*   **Issue Summary:** Sensitive API keys are hardcoded in the frontend JavaScript, creating a critical security vulnerability.
*   **Priority:** Critical
*   **Recommended Action:**
    1.  Create a new, secure backend endpoint (e.g., `/api/v1/analyze-room-secure`) in [`ai_room_cleaner/backend/api/router.py`](ai_room_cleaner/backend/api/router.py:1) that will proxy requests to the external AI service.
    2.  The frontend in [`ai_room_cleaner/frontend/modules/api.js`](ai_room_cleaner/frontend/modules/api.js:1) must be refactored to call this new backend endpoint instead of the external API directly.
    3.  The API key must be removed from the frontend code and used exclusively within the new backend endpoint, retrieved from a secure configuration source.
    ```javascript
    // Before: ai_room_cleaner/frontend/modules/api.js
    const API_KEY = 'some_hardcoded_secret_key'; // VULNERABILITY
    // ... fetch('https://external.ai/api', { headers: {'Authorization': `Bearer ${API_KEY}`} })

    // After: ai_room_cleaner/frontend/modules/api.js
    // ... fetch('/api/v1/analyze-room-secure', ...) // No key needed
    ```
*   **Rationale:** This change prevents the exposure of sensitive credentials on the client-side, completely mitigating the risk of key theft and unauthorized API usage. All sensitive operations are moved to a trusted backend environment.
*   **Estimated Effort:** Medium

---

## 2. [HIGH] Backend: Hardcoded Configuration and Secrets

*   **Issue Summary:** Application configuration and secrets are hardcoded in [`ai_room_cleaner/backend/core/config.py`](ai_room_cleaner/backend/core/config.py:1), which is inflexible and insecure.
*   **Priority:** High
*   **Recommended Action:**
    1.  Externalize all configuration—especially secrets like API keys—into environment variables.
    2.  Create a `.env` file for local development and add it to `.gitignore`.
    3.  Use a library like `pydantic-settings` in [`ai_room_cleaner/backend/core/config.py`](ai_room_cleaner/backend/core/config.py:1) to load these variables at runtime.
    ```python
    # After: ai_room_cleaner/backend/core/config.py
    from pydantic_settings import BaseSettings, SettingsConfigDict

    class Settings(BaseSettings):
        AI_API_KEY: str
        AI_API_ENDPOINT: str
        LOG_LEVEL: str = "INFO"

        model_config = SettingsConfigDict(env_file=".env")

    settings = Settings()
    ```
*   **Rationale:** Decouples configuration from the codebase, allowing for seamless environment-specific settings (dev, staging, prod) and secure management of secrets outside of version control.
*   **Estimated Effort:** Medium

---

## 3. [HIGH] Backend: Lack of Input Validation in API Router

*   **Issue Summary:** The `/analyze_room` endpoint in [`ai_room_cleaner/backend/api/router.py`](ai_room_cleaner/backend/api/router.py:1) does not validate incoming data, exposing the application to invalid data and potential injection attacks.
*   **Priority:** High
*   **Recommended Action:**
    1.  Leverage FastAPI's automatic validation by using `UploadFile` and `File`.
    2.  Add explicit checks for content type to ensure only image files are processed.
    ```python
    # After: ai_room_cleaner/backend/api/router.py
    from fastapi import APIRouter, File, UploadFile, HTTPException, status

    router = APIRouter()

    @router.post("/analyze_room")
    async def analyze_room(file: UploadFile = File(...)):
        if not file.content_type.startswith('image/'):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid file type. Only images are allowed."
            )
        # ... proceed with processing the validated file
        contents = await file.read()
        return {"filename": file.filename, "content_type": file.content_type}
    ```
*   **Rationale:** Enforces strict data contracts for the API, improving security by preventing common vulnerabilities and enhancing robustness by rejecting invalid requests early.
*   **Estimated Effort:** Small

---

## 4. [MEDIUM] Frontend: Monolithic `app.js`

*   **Issue Summary:** The primary frontend logic file, [`ai_room_cleaner/frontend/app.js`](ai_room_cleaner/frontend/app.js:1), is overly large and lacks separation of concerns.
*   **Priority:** Medium
*   **Recommended Action:**
    1.  Decompose [`app.js`](ai_room_cleaner/frontend/app.js:1) into smaller, single-responsibility modules (e.g., `state.js`, `eventHandlers.js`).
    2.  The existing [`ui.js`](ai_room_cleaner/frontend/modules/ui.js:1) should be used for all DOM manipulation logic.
    3.  [`app.js`](ai_room_cleaner/frontend/app.js:1) should be refactored to act as the application entry point, orchestrating the initialization of the other modules.
    ```javascript
    // Example: app.js (after refactor)
    import { initializeUI } from './modules/ui.js';
    import { setupEventListeners } from './modules/eventHandlers.js';
    import { initState } from './modules/state.js';

    document.addEventListener('DOMContentLoaded', () => {
        initState();
        initializeUI();
        setupEventListeners();
    });
    ```
*   **Rationale:** Improves code maintainability, readability, and testability. Smaller, focused modules are easier to understand, debug, and reuse.
*   **Estimated Effort:** Medium

---

## 5. [MEDIUM] Backend: Inadequate Test Coverage

*   **Issue Summary:** The test suite for [`ai_room_cleaner/backend/services/ai_service.py`](ai_room_cleaner/backend/services/ai_service.py:1) lacks coverage for edge cases and failure modes.
*   **Priority:** Medium
*   **Recommended Action:**
    1.  Expand [`ai_room_cleaner/backend/tests/test_ai_service.py`](ai_room_cleaner/backend/tests/test_ai_service.py:1) with new tests using `pytest` and `unittest.mock`.
    2.  Mock the external API client to simulate various responses:
        *   API errors (e.g., 500, 403 status codes).
        *   Network-level failures.
        *   Unexpected or malformed response payloads.
    ```python
    # Example: test_ai_service.py
    from unittest.mock import patch
    import pytest
    from my_project.core.exceptions import AIAPIServiceError

    async def test_analyze_image_handles_api_error(ai_service):
        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = httpx.HTTPStatusError("Error", request=..., response=...)
            with pytest.raises(AIAPIServiceError):
                await ai_service.analyze_image(b"fake_image_data")
    ```
*   **Rationale:** Creates a more resilient and reliable application by ensuring the service behaves predictably under adverse conditions, preventing regressions, and documenting behavior through tests.
*   **Estimated Effort:** Medium

---

## 6. [LOW] Backend: Insufficient Error Handling

*   **Issue Summary:** The AI service in [`ai_room_cleaner/backend/services/ai_service.py`](ai_room_cleaner/backend/services/ai_service.py:1) does not gracefully handle potential failures from its external dependencies.
*   **Priority:** Low
*   **Recommended Action:**
    1.  Wrap external API calls within `try...except` blocks.
    2.  Catch specific exceptions (e.g., `httpx.RequestError`, `httpx.HTTPStatusError`).
    3.  Translate low-level exceptions into custom, application-specific exceptions (e.g., `AIAPIServiceError`) to be handled by the API layer.
*   **Rationale:** Improves service resilience, prevents unhandled exceptions from crashing the application, and provides a clear error propagation mechanism.
*   **Estimated Effort:** Small

---

## 7. [LOW] Frontend: Direct DOM Manipulation

*   **Issue Summary:** The frontend code in [`ai_room_cleaner/frontend/modules/ui.js`](ai_room_cleaner/frontend/modules/ui.js:1) relies on direct DOM manipulation, which can be inefficient.
*   **Priority:** Low
*   **Recommended Action:**
    1.  No immediate, large-scale refactoring is required.
    2.  For future work, consider adopting a declarative UI library (e.g., React, Vue).
    3.  For now, apply micro-optimizations by batching DOM reads and writes to minimize layout thrashing and improve rendering performance where possible.
*   **Rationale:** While the current approach is functional, adopting modern UI patterns or libraries in the future would improve scalability and developer experience. Batching DOM operations is a low-effort way to gain minor performance improvements.
*   **Estimated Effort:** Small