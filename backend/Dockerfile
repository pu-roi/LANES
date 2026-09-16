# ==============================================================================
# LANES Backend - Production Dockerfile for Google Cloud Run
# ==============================================================================
FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffer stdout/stderr
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080

# Working directory inside the container
WORKDIR /app

# Install minimal OS runtime packages required for networking & healthchecks
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only dependency files first to leverage Docker layer caching
COPY requirements.txt .

# Upgrade pip and install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy all application files
COPY . .

# Expose default Cloud Run port
EXPOSE 8080

# Run FastAPI using Uvicorn
# Dynamically binds to $PORT provided by Cloud Run (defaults to 8080)
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
