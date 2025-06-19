# Home Assistant Addon Guardian Audit Report (Cycle 1)

This report details the findings of the static code audit for the "AI Room Cleaner" addon. The following issues were identified and require attention.

## 1. Dockerfile Analysis (`hadolint`)

The `hadolint` tool identified several opportunities for improvement in the addon's Dockerfile.

**Actionable Checklist:**

- [ ] **DL3006: Explicit Image Tagging:** Pin the base image to a specific version in the `FROM` instruction to ensure build reproducibility. For example, change `FROM homeassistant/base` to `FROM homeassistant/base:2023.10.0`.
- [ ] **DL3008: Pin Package Versions:** Specify versions for all packages installed with `apt-get` to prevent unexpected changes from upstream. For example, `apt-get install -y git=1:2.34.1-1`.
- [ ] **DL3059: Consolidate `RUN` Instructions:** Combine consecutive `RUN` commands using `&&` to reduce the number of layers in the Docker image, which can improve image size and build performance.
- [ ] **DL3042: Use `--no-cache-dir` with `pip`:** Add the `--no-cache-dir` flag to `pip install` commands to prevent caching, which can reduce the image size.

## 2. Shell Script Analysis (`shellcheck`)

The `shellcheck` tool found multiple issues in the `run.sh` script.

**Actionable Checklist:**

- [ ] **SC1008: Unrecognized Shebang:** The shebang `#!/usr/bin/with-contenv bashio` is not standard. While it may work in the Home Assistant environment, it prevents standard tools like `shellcheck` from analyzing the script correctly. This does not require a fix but is noted for awareness.
- [ ] **SC1017: Literal Carriage Returns:** The script contains Windows-style line endings (CRLF). These should be converted to Unix-style line endings (LF) to ensure compatibility. This can be fixed by running `tr -d '\r' < ai_room_cleaner/run.sh > ai_room_cleaner/run.sh.new && mv ai_room_cleaner/run.sh.new ai_room_cleaner/run.sh`.
- [ ] **SC2155: Declare and Assign Separately:** For better error handling, declare and assign variables in separate steps. For example, `export LOG_LEVEL; LOG_LEVEL=$(bashio::config 'log_level')`.

## 3. Configuration Review (`config.yaml`)

A manual review of the `config.yaml` file revealed a potential configuration issue.

**Actionable Checklist:**

- [ ] **Missing `openai_api_key` in `options`:** The `openai_api_key` is defined in the `schema` but is not present in the `options` block. If this key is required for the addon to start, it should be added to the `options` with a placeholder value, like `openai_api_key: ""`.

## 4. Python Source Code Review (`main.py`)

A high-level review of the Python source code identified a potential runtime error.

**Actionable Checklist:**

- [ ] **Incorrect `todo.remove_item` Service Call:** The `todo.remove_item` service call in `main.py` uses `"item": "all"` to clear the list, which is not supported. This should be replaced with a loop that retrieves all items from the list and removes them one by one.