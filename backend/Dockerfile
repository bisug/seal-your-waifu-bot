# Stage 1: Python Builder (for building wheels)
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim AS python-builder

WORKDIR /app

# Install build dependencies for C-extensions (needed by tgcrypto and other binary Python packages when wheels are unavailable)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy project files for dependency resolution
# Build context is backend/ (see compose.yaml and platform configs)
COPY pyproject.toml uv.lock ./

# Install dependencies into a dedicated environment
# We use --no-install-project because we only want the dependencies in this stage
RUN uv sync --frozen --no-install-project --no-dev

# Stage 2: Final Production Image
FROM ghcr.io/astral-sh/uv:python3.14-bookworm-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/app/.venv/bin:${PATH}"

WORKDIR /app

# Install runtime dependencies (curl for healthchecks)
RUN apt-get update && apt-get install -y --no-install-recommends curl && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

# Copy virtual environment from builder
COPY --from=python-builder /app/.venv /app/.venv

# Create a non-root user for security
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Copy application code explicitly to keep the image slim
# The context (backend/) contains the package (backend/), config.py, and scripts/
COPY --chown=botuser:botuser . /app/

USER botuser

# Expose port (Heroku sets $PORT automatically, but we define a default for local testing)
EXPOSE 8080

# Healthcheck to verify app stability
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8080}/healthz || exit 1

# Default runtime command
CMD ["sh", "-c", "uvicorn backend.webapp.main:app --host 0.0.0.0 --port ${PORT:-8080}"]
