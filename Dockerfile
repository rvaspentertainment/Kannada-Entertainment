# [cite_start]Use an official Python runtime as a parent image [cite: 820]
FROM python:3.11-slim

# [cite_start]Set the working directory within the container [cite: 820]
WORKDIR /app

# [cite_start]Install system dependencies that might be needed by some Python packages [cite: 820]
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# [cite_start]Copy the dependencies file first to leverage Docker's layer caching [cite: 820]
COPY requirements.txt .

# [cite_start]Install Python dependencies specified in requirements.txt [cite: 821]
RUN pip install --no-cache-dir -r requirements.txt

# [cite_start]Copy the rest of the application's code into the container [cite: 821]
COPY . .

# [cite_start]Create directories that might be needed by the application [cite: 822]
RUN mkdir -p logs temp_data

# [cite_start]Set environment variables for the container [cite: 822]
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# [cite_start]Expose the port the app runs on (for the health check server) [cite: 822]
EXPOSE 8080

# [cite_start]Command to run the application when the container starts [cite: 823]
CMD ["python", "main.py"]
