FROM python:3.12-slim-bookworm

WORKDIR /app
COPY . .
RUN apt-get update && apt-get install -y bash dos2unix
RUN dos2unix /app/run.sh
RUN chmod +x /app/run.sh


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable

# Run app.py when the container launches
CMD [ "/app/run.sh" ]