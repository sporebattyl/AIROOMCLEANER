# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends python3 python3-pip && rm -rf /var/lib/apt/lists/*

# Create app directory
WORKDIR /app

# Copy application files
ENV PYTHONPATH=/app
COPY . .

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8000

# Start the application
CMD [ "sh", "-c", "cd /app/app && uvicorn main:app --host 0.0.0.0 --port 8000" ]