# Use the official Home Assistant base image
ARG BUILD_FROM="ghcr.io/home-assistant/amd64-base-python:latest"
FROM ${BUILD_FROM}

# Set shell
SHELL ["/bin/bash", "-o", "pipefail", "-c"]

# Install build dependencies, create a non-root user, and install python dependencies
RUN apk add --no-cache python3 py3-pip && \
    addgroup --system app && \
    adduser --system --ingroup app app

# Create app directory
WORKDIR /

# Copy the run script to the root and make it executable
COPY run.sh /run.sh
RUN chmod a+x /run.sh && sed -i 's/\r$//g' /run.sh

# Copy application files and install dependencies
WORKDIR /app
COPY --chown=app:app . .
RUN pip3 install --no-cache-dir -r requirements.txt

# Switch to the non-root user
USER app

# Set the entrypoint to run.sh
CMD [ "/run.sh" ]