# Use official Python runtime as a parent image
FROM python:3.11-slim

# Set work directory
WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the backend code
COPY backend/ ./backend/
COPY simulation.py .
COPY genesis.json .
COPY system_config.json .

# Expose the port
EXPOSE 6429

# Run the application
CMD ["uvicorn", "backend.api.app:app", "--host", "0.0.0.0", "--port", "6429"]
