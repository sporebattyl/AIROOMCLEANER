# Home Assistant Addon Audit Report 1

## Pre-flight Check

*   [x] Git installed (version 2.49.0.windows.1)
*   [x] Docker installed (version 28.1.1)
*   [x] hadolint installed (version 2.12.0)
*   [x] shellcheck installed (version 0.10.0)

## Branch

*   **Branch Name:** `guardian-addon-debug-20250619`

## Audit Findings & Remediation Plan

This audit identifies several areas for improvement in the Home Assistant addon. The following checklist outlines the planned changes to address these issues.

### 1. Dockerfile Improvements

*   [ ] **DL3006:** The `CMD` should use `exec` form to be the container's PID 1 process.
*   [ ] **DL3018:** Pin versions for `apt-get install` to ensure reproducible builds.
*   [ ] **DL3042:** Avoid use of `--no-cache-dir` with pip, as it can negatively impact layer caching.
*   [ ] **Best Practice:** Combine `RUN` commands to reduce layer count.
*   [ ] **Best Practice:** Use a non-root user for security.

### 2. run.sh Improvements

*   [ ] **SC2086:** Double quote variables to prevent globbing and word splitting.
*   [ ] **Best Practice:** The `run.sh` script in a Home Assistant addon should handle configuration from `/data/options.json`. The current script does not.
*   [ ] **Best Practice:** The `CMD` in the Dockerfile and the `run.sh` script are redundant. The `run.sh` should be the single entrypoint.

### 3. config.yaml Improvements

*   [ ] **Schema:** The `SUPERVISOR_TOKEN` should not be an option that the user can set. It is provided by the supervisor.
*   [ ] **Schema:** `LOG_LEVEL` has a default, so it should be marked as optional.
*   [ ] **Options:** The default `ai_prompt` is not very descriptive and could be improved.

### 4. main.py Improvements

*   [ ] **Error Handling:** The main `try...except` block is too broad. It should be more specific.
*   [ ] **Configuration:** The script should read configuration from `/data/options.json` via `bashio` in the `run.sh` script, not from environment variables that are set in the `config.yaml`.
*   [ ] **Hardcoded Values:** The sensor entity IDs are hardcoded. They should be dynamic based on the addon slug.
*   [ ] **To-Do List:** The to-do list logic is complex and could be simplified. The `get_items` service call is not standard for the `todo` integration.
*   [ ] **Redundancy:** The application is started with `uvicorn` in both the `Dockerfile` and `run.sh`. This is incorrect. The `Dockerfile` should not start the application.