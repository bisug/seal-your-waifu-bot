# Use Python 3.13 slim image as base
FROM python:3.13-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libffi-dev \
    libssl-dev \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Create a non-root user
RUN useradd -m -u 1000 botuser && \
    chown -R botuser:botuser /app

# Switch to non-root user
USER botuser

# Copy and install Python dependencies
COPY --chown=botuser:botuser requirements.txt .
RUN pip install --user --no-warn-script-location -r requirements.txt

# Add user's bin to PATH
ENV PATH="/home/botuser/.local/bin:${PATH}"

# Copy the rest of the application
COPY --chown=botuser:botuser . .

# Run the application
CMD ["python", "-m", "Grabber"]
