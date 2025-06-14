# Implementation Plan for Backend Fixes

This document outlines the step-by-step plan for implementing the backend fixes, categorized by priority.

---

## Critical Errors

### 1. Fix Import Error in Camera Service
*   **File:** [`ai_room_cleaner/backend/services/camera_service.py`](ai_room_cleaner/backend/services/camera_service.py:4)
*   **Change:** Replace the direct import of `settings` from `ai_room_cleaner.backend.core.config` with the `get_settings()` dependency injection function.
    *   **From:** `from ai_room_cleaner.backend.core.config import settings`
    *   **To:** `from ai_room_cleaner.backend.core.config import get_settings`

### 2. Remove Unused Global Variable in AI Service
*   **File:** [`ai_room_cleaner/backend/services/ai_service.py`](ai_room_cleaner/backend/services/ai_service.py:57)
*   **Change:** Remove the `_gemini_configured` global variable and any related logic, as it is unused.

### 3. Update Deprecated Startup Event in Main Application
*   **File:** [`ai_room_cleaner/backend/main.py`](ai_room_cleaner/backend/main.py:81)
*   **Change:** Replace the deprecated `@app.on_event("startup")` decorator with a modern `lifespan` context manager to handle application startup and shutdown events.

---

## High-Priority Issues

### 1. Implement Error Handling in Camera Service
*   **File:** [`ai_room_cleaner/backend/services/camera_service.py`](ai_room_cleaner/backend/services/camera_service.py)
*   **Change:** Add robust error handling during the initialization of camera settings to gracefully manage potential configuration issues.

### 2. Refine Exception Handling in API Router
*   **File:** [`ai_room_cleaner/backend/api/router.py`](ai_room_cleaner/backend/api/router.py)
*   **Change:** Make exception handling more specific. Instead of catching broad exceptions, catch specific ones and provide more meaningful error responses.

### 3. Enhance Security
*   **File:** [`ai_room_cleaner/backend/main.py`](ai_room_cleaner/backend/main.py) (for CORS) & [`ai_room_cleaner/backend/services/camera_service.py`](ai_room_cleaner/backend/services/camera_service.py) (for image processing)
*   **Changes:**
    *   Restrict the CORS policy to allow only specific origins.
    *   Improve resource management for image processing to prevent potential memory leaks or performance issues.

---

## Medium-Priority Issues

### 1. Refactor Hardcoded Path in State Management
*   **File:** [`ai_room_cleaner/backend/core/state.py`](ai_room_cleaner/backend/core/state.py:10)
*   **Change:** Refactor the hardcoded path for `analysis_history.json`. This path should be configurable, possibly through environment variables or a configuration file.

### 2. Add/Correct Type Hinting
*   **Files:** Entire codebase.
*   **Change:** Perform a full pass over the codebase to add or correct type hints for function arguments, return values, and variables to improve code clarity and maintainability.

### 3. Consolidate Configuration
*   **Files:** [`ai_room_cleaner/backend/main.py`](ai_room_cleaner/backend/main.py) and other relevant files.
*   **Change:** Consolidate rate-limiter instances to avoid redundancy and improve logging configuration for better monitoring and debugging.

---

## Low-Priority and Quality Improvements

### 1. Address Code Quality Issues
*   **Files:** Entire codebase.
*   **Changes:**
    *   **Duplicated Code:** Refactor duplicated code blocks into reusable functions or classes.
    *   **Hardcoded Constants:** Replace hardcoded constants with configurable values or named constants.
    *   **Test Coverage:** Improve test coverage, especially for critical components.
    *   **Input Validation:** Add comprehensive input validation to API endpoints.
    *   **Naming Consistency:** Ensure consistent naming conventions for variables, functions, and classes.
    *   **Docstrings:** Add or improve docstrings for all modules, classes, and functions.