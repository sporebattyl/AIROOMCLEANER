# Use an official Python runtime as a parent image
FROM %%BASE_IMAGE%%

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Make the run script executable
RUN chmod +x /app/run.sh


# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# Make port 8000 available to the world outside this container
EXPOSE 8000

# Define environment variable

# Run app.py when the container launches
CMD [ "/app/run.sh" ]