# Home Assistant Addon Guardian - Cycle 4 Audit Report

This report details the findings of the static code audit for the AI Room Cleaner addon.

## 1. Dockerfile (`ai_room_cleaner/Dockerfile`)

*   **[High] DL3006: Always tag the version of an image explicitly.**
    *   **Finding:** The base image `ghcr.io/home-assistant/amd64-base-python` is not tagged with a specific version. This can lead to unexpected changes in the build environment.
    *   **Recommendation:** Pin the base image to a specific version, for example: `ghcr.io/home-assistant/amd64-base-python:3.11-slim`.

## 2. Shell Scripts (`ai_room_cleaner/run.sh`)

*   **[Critical] SC1008: Unrecognized shebang.**
    *   **Finding:** The shebang `#!/usr/bin/with-contenv bashio` is not standard and not recognized by `shellcheck`.
    *   **Recommendation:** Change the shebang to `#!/usr/bin/env bashio` for better compatibility.
*   **[Critical] SC1017: Literal carriage return.**
    *   **Finding:** The script contains Windows-style line endings (`\r\n`), which can cause execution errors in a Linux environment.
    *   **Recommendation:** Convert the line endings to Unix-style (`\n`). This can be done with the `tr -d '\r' < run.sh > run_fixed.sh` command.

## 3. Configuration (`ai_room_cleaner/config.yaml`)

*   **[Medium] Incorrect schema for `log_level`.**
    *   **Finding:** The schema for `log_level` is defined as `list(CRITICAL|ERROR|WARNING|INFO|DEBUG)?`. The `list` type is for a list of strings, but this option should only accept one value.
    *   **Recommendation:** Change the schema to `match(^(CRITICAL|ERROR|WARNING|INFO|DEBUG)$)`.

## 4. Source Code (`ai_room_cleaner/app/main.py`)

*   **[Medium] Potential error in clearing to-do list.**
    *   **Finding:** In the `analyze_room_task` function, the code attempts to remove items from the to-do list using the full item object. The `todo.remove_item` service likely expects only the item's name.
    *   **Recommendation:** Modify the loop to extract the item name from the `existing_items` list before calling the `remove_item` service. The `state.get('attributes', {}).get('items', [])` returns a list of dictionaries, so the code should iterate over `item['name']` or a similar key.