# Home Assistant Addon Audit Report 3

## 1. Failure Analysis (Cycle 2)

### Root Cause

The addon container failed to start due to a script execution error in `run.sh`. The error log shows `: No such file or directory bashio`, which is a classic symptom of a script saved with Windows-style CRLF (`\r\n`) line endings being executed in a Unix-like environment (which expects LF `\n` line endings). The shell interprets the carriage return (`\r`) as part of the command or interpreter path, leading to the "No such file or directory" error.

## 2. Corrective Action Plan

The following checklist outlines the steps to resolve the line ending issue.

### Checklist

- [ ] **Modify `Dockerfile` to fix line endings**
  - Add a `RUN` command to convert `run.sh` to Unix-style line endings after it's copied into the container.

### Proposed `Dockerfile` Modification

To ensure the `run.sh` script is executable within the Alpine-based container, we will add a step to the `Dockerfile` to normalize its line endings. The `sed` utility will be used to remove the carriage return characters (`\r`).

Add the following line to `ai_room_cleaner/Dockerfile` immediately after the `RUN chmod a+x /run.sh` command:

```dockerfile
RUN sed -i 's/\r$//g' /run.sh
```

This command modifies the file in-place, ensuring it has the correct LF line endings required for execution in the container's shell.