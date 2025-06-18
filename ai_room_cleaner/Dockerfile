# Use the official Home Assistant base image
ARG BUILD_FROM
FROM ${BUILD_FROM}

# Set the working directory
WORKDIR /app

# Copy the application code
COPY app/ .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# This will be executed when the container starts
CMD [ "python", "-u", "main.py" ]