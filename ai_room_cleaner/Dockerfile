# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Add non-root user for security
RUN addgroup -S appuser && adduser -S -G appuser appuser

# Create app directory with proper permissions
RUN mkdir -p /app && chown -R appuser:appuser /app

# Set the working directory
WORKDIR /app

# Copy the application code
COPY app/ .
COPY app/.env .

# Install Python dependencies
RUN apk add --no-cache python3 py3-pip && \
    python3 -m venv /app/venv && \
    /app/venv/bin/pip install --no-cache-dir -r requirements.txt

# Switch to non-root user
USER appuser

# Add security headers and optimize for production
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PATH="/app/venv/bin:$PATH"
ENV PYTHONPATH=/app

# This will be executed when the container starts
CMD [ "python3", "-u", "main.py" ]