# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Install build dependencies
RUN apk add --no-cache nodejs npm python3 py3-pip

# Create app directory
WORKDIR /app

# Copy application files
COPY . .

# Build frontend assets
RUN npm install && npm run build

# Install Python dependencies
RUN pip3 install --no-cache-dir -r requirements.txt

# Expose the application port
EXPOSE 8000

# Start the application
CMD [ "sh", "-c", "cd /app/app && uvicorn main:app --host 0.0.0.0 --port 8000" ]