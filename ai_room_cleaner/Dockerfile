# Stage 1: Build stage for Python dependencies
FROM python:3.13-slim-bookworm AS python-builder

# Set the working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy poetry lock and pyproject to leverage Docker cache
COPY poetry.lock pyproject.toml ./

# Install poetry and dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir poetry && \
    poetry config virtualenvs.create false && \
    poetry install --no-root --without dev --no-interaction --no-ansi


# Stage 2: Final production stage
FROM python:3.13-slim-bookworm

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python dependencies from the builder stage
COPY --from=python-builder /usr/local/lib/python3.13/site-packages /usr/local/lib/python3.13/site-packages
COPY --from=python-builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY . .

# Ensure the run script is executable
RUN chmod +x /app/run.sh

# Expose the port the app runs on
EXPOSE 8000

# Add a health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8000/api/health || exit 1

# Define the command to run the application
CMD ["/app/run.sh"]