# Dockerfile

# Use an efficient Python 3.11 base image
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file first to leverage Docker's build cache
COPY requirements.txt .

# Install the Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code
COPY . .

# Expose the port the web server will run on
EXPOSE 8080

# Command to run your application when the container starts
CMD ["python", "kannada_bot.py"]
