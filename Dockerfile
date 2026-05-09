# Stage 1: Frontend Builder
FROM node:22-alpine AS frontend-builder
WORKDIR /app/frontend
# Install dependencies first for better caching
COPY frontend/package*.json ./
RUN npm ci
# Copy source and build
COPY frontend/ ./
RUN npm run build

# Stage 2: Python Builder (for building wheels)
FROM python:3.13-slim AS python-builder

WORKDIR /app

# Install build dependencies for C-extensions (needed by tgcrypto, orjson, psutil)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and build wheels
RUN pip install --upgrade pip
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 3: Final Production Image
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/home/botuser/.local/bin:${PATH}"

WORKDIR /app

# Install runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=python-builder /app/wheels /wheels
RUN pip install --upgrade pip && \
    pip install --no-cache /wheels/* && \
    rm -rf /wheels

# Create a non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Copy application code explicitly to keep the image slim
# We avoid COPY . . to prevent including frontend source, local venvs, etc.
COPY --chown=botuser:botuser Grabber/ /app/Grabber/
COPY --chown=botuser:botuser config.py /app/
COPY --chown=botuser:botuser .python-version /app/
COPY --chown=botuser:botuser runtime.txt /app/
COPY --chown=botuser:botuser heroku.yml /app/

# Copy compiled frontend assets from Stage 1 into the Grabber static folder
# We explicitly target the 'dist' folder and ensure the destination is fresh
RUN rm -rf /app/Grabber/static && mkdir -p /app/Grabber/static
COPY --from=frontend-builder --chown=botuser:botuser /app/frontend/dist/ /app/Grabber/static/

USER botuser

# Expose port (Heroku sets $PORT automatically, but we define a default for local testing)
EXPOSE 8080

# Healthcheck to verify app stability
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/healthz || exit 1

# Default runtime command
CMD ["uvicorn", "Grabber.webapp.main:app", "--host", "0.0.0.0", "--port", "8080"]
