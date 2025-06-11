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
COPY . .

# Fix line endings and permissions
RUN dos2unix /app/run.sh
RUN chmod +x /app/run.sh

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Run the startup script when the container launches
CMD ["/app/run.sh"]