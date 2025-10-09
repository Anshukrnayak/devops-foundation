# docker/celery/Dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements /app/requirements
RUN pip install --no-cache-dir -r requirements/production.txt

# Copy project
COPY backend /app/backend

# Celery worker
CMD ["celery", "-A", "config.celery", "worker", "--loglevel=info", "--concurrency=4", "-Q", "predictions,market_data,indicators,trading"]