# backend/Dockerfile
FROM python:3.11-slim-bullseye

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=on \
    PIP_DISABLE_PIP_VERSION_CHECK=on

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    postgresql-dev \
    libpq-dev \
    curl \
    netcat-traditional \
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
RUN mkdir -p /app/staticfiles /app/media /app/logs

# Create non-root user
RUN groupadd -r quantum && useradd -r -g quantum quantum && \
    chown -R quantum:quantum /app
USER quantum

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/ || exit 1

# Start command
CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000", "--workers", "4", "--threads", "2"]