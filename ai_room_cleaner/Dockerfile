FROM python:3.12-slim-bookworm

# Install bashio for Home Assistant addon support
RUN apt-get update && apt-get install -y \
    bash \
    dos2unix \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

# Install bashio
RUN curl -J -L -o /tmp/bashio.tar.gz \
    "https://github.com/hassio-addons/bashio/archive/v0.16.2.tar.gz" \
    && mkdir /tmp/bashio \
    && tar zxvf /tmp/bashio.tar.gz --strip 1 -C /tmp/bashio \
    && mv /tmp/bashio/lib /usr/lib/bashio \
    && ln -s /usr/lib/bashio/bashio /usr/bin/bashio \
    && rm -rf /tmp/bashio*

WORKDIR /app

# Copy requirements first for better Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Explicitly copy frontend files to ensure they're included
COPY frontend/ ./frontend/

# Fix line endings and permissions
RUN dos2unix /app/run.sh
RUN chmod +x /app/run.sh

# List files to verify they were copied (for debugging)
RUN echo "=== Files in /app ===" && find /app -type f -name "*.html" -o -name "*.css" -o -name "*.js" | head -20

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the startup script when the container launches
CMD ["/app/run.sh"]