# Stage 1: Frontend Builder
FROM node:18-alpine AS frontend-builder
WORKDIR /app
COPY frontend/ ./frontend/
RUN cd frontend && npm install && npm run build

# Stage 2: Python Builder
FROM python:3.13-slim AS builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install dependencies
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 3: Final
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/botuser/.local/bin:${PATH}"

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/*

# Create a non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app
USER botuser

# Copy application code
COPY --chown=botuser:botuser . .

# Copy compiled frontend assets from Stage 1
COPY --from=frontend-builder --chown=botuser:botuser /app/Grabber/static /app/Grabber/static

# Default command (will be overridden by Procfile/heroku.yml)
HEALTHCHECK --interval=30s --timeout=10s --start-period=20s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/healthz || exit 1
CMD ["python", "-m", "Grabber"]
