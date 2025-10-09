# docker/celery/Dockerfile
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    C_FORCE_ROOT=true

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-dev \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Copy requirements
COPY requirements /app/requirements

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install --no-cache-dir -r requirements/production.txt && \
    pip install --no-cache-dir -r requirements/quantum.txt

# Copy project
COPY backend /app/

# Create necessary directories
RUN mkdir -p /app/logs

# Create non-root user
RUN groupadd -r quantum && useradd -r -g quantum quantum && \
    chown -R quantum:quantum /app
USER quantum

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD celery -A config.celery inspect ping -d celery@$HOSTNAME

# Start command
CMD ["celery", "-A", "config.celery", "worker", "--loglevel=info", "--concurrency=4"]