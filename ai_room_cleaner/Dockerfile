# Stage 1: Build stage
FROM python:3.12-slim-bookworm AS builder

# Install bashio and build dependencies
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

# Copy and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Fix line endings and permissions
RUN dos2unix /app/run.sh && chmod +x /app/run.sh


# Stage 2: Production stage
FROM python:3.12-slim-bookworm

# Install runtime dependencies
# bash is for bashio, curl/jq might be used by bashio scripts
RUN apt-get update && apt-get install -y \
    bash \
    curl \
    jq \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy installed Python dependencies from builder
COPY --from=builder /usr/local/lib/python3.12/site-packages/ /usr/local/lib/python3.12/site-packages/

# Copy bashio from builder
COPY --from=builder /usr/lib/bashio /usr/lib/bashio
COPY --from=builder /usr/bin/bashio /usr/bin/bashio

# Copy application from builder
COPY --from=builder /app /app

EXPOSE 8000

CMD ["/app/run.sh"]