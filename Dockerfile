# ==============================================================================
# Multi-stage/Optimized Production Dockerfile for AI Data Engineering Copilot
# ==============================================================================

# Use an official, lightweight Python runtime as a parent image
FROM python:3.12-slim AS base

# Prevent Python from writing pyc files to disk
ENV PYTHONDONTWRITEBYTECODE=1

# Prevent Python from buffering stdout and stderr (helps with real-time docker logs)
ENV PYTHONUNBUFFERED=1

# Set the working directory inside the container
WORKDIR /workspace

# Install system dependencies if any are needed (e.g., build tools, curl)
# We keep this lightweight and clean up the apt cache to minimize image size.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy only the requirements file first to leverage Docker's cache layers
COPY requirements.txt .

# Install dependencies into the system environment inside the container
RUN pip install --no-cache-dir --upgrade -r requirements.txt

# Copy the rest of the application source code
COPY app/ ./app/
COPY .env .env

# Create a non-privileged user to run the app for security best practices.
# Running containers as root is a security risk in production environments.
RUN adduser --disabled-password --gecos "" appuser && chown -R appuser:appuser /workspace
USER appuser

# Expose the port FastAPI runs on
EXPOSE 8000

# Run Uvicorn.
# Important: We bind to 0.0.0.0 inside containers so it's accessible from the host.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
