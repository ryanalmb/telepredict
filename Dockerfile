# Multi-stage Docker build for sports prediction bot

# Stage 1: Base Python environment
FROM python:3.11-slim as base

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    curl \
    git \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Create app user
RUN useradd --create-home --shell /bin/bash app

# Set work directory
WORKDIR /app

# Stage 2: Dependencies
FROM base as dependencies

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --upgrade pip && \
    pip install -r requirements.txt

# Stage 3: Development
FROM dependencies as development

# Install development dependencies
RUN pip install pytest pytest-asyncio pytest-cov black flake8 mypy

# Copy source code
COPY . .

# Change ownership to app user
RUN chown -R app:app /app

# Switch to app user
USER app

# Expose port
EXPOSE 8000

# Development command
CMD ["python", "-m", "src.sports_prediction.cli", "run-bot"]

# Stage 4: Production
FROM dependencies as production

# Copy only necessary files
COPY src/ ./src/
COPY pyproject.toml .
COPY README.md .

# Install the package
RUN pip install -e .

# Create necessary directories
RUN mkdir -p data logs models && \
    chown -R app:app /app

# Switch to app user
USER app

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Production command
CMD ["python", "-m", "src.sports_prediction.cli", "run-bot", "--production"]
