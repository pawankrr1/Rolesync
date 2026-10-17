# ==============================================================================
# Career Intelligence Platform - Production Backend Dockerfile
# Multi-stage security hardened Python container
# ==============================================================================

FROM python:3.9-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# Install minimal required OS dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Create unprivileged application user
RUN addgroup --system --gid 1001 appgroup && \
    adduser --system --uid 1001 --ingroup appgroup --home /app --no-create-home appuser

# Install Python dependencies in separate layer for cache optimization
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code and seed data
COPY . .

# Set execution permissions on scripts and change file ownership
RUN chmod +x scripts/*.sh scripts/*.py && \
    chown -R appuser:appgroup /app

# Switch to unprivileged runtime user
USER appuser

EXPOSE 8000

# Container liveness and readiness probe
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python3 scripts/healthcheck.py || exit 1

# Production startup entrypoint with automated migration & canonical seed hooks
CMD ["./scripts/start_production.sh"]
