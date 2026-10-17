#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Career Intelligence Platform - Production Backend Entrypoint
# ==============================================================================

echo "=================================================================="
echo "🚀 STARTING CAREER INTELLIGENCE PRODUCTION BACKEND"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=================================================================="

# Ensure working directory is backend root
cd "$(dirname "$0")/.."

# 1. Environment Variable Pre-flight Verification
echo "🔍 Running environment pre-flight audit..."

if [ "${ENVIRONMENT:-development}" = "production" ]; then
    if [ -z "${SECRET_KEY:-}" ] || [ "${SECRET_KEY}" = "insecure-dev-secret-key-change-in-production-min-32-chars" ]; then
        echo "❌ FATAL: SECRET_KEY must be provided via environment variable in production (minimum 32 characters)."
        exit 1
    fi
    if [ "${#SECRET_KEY}" -lt 32 ]; then
        echo "❌ FATAL: SECRET_KEY must be at least 32 characters long."
        exit 1
    fi
    if [[ "${CORS_ORIGINS:-}" == *"*"* ]]; then
        echo "❌ FATAL: Wildcard CORS ('*') is forbidden in production. Provide explicit domain(s)."
        exit 1
    fi
    echo "✅ Production security requirements validated."
else
    echo "ℹ️  Running in non-production mode: ${ENVIRONMENT:-development}"
fi

# 2. Database Migrations
echo "📦 Applying database migrations..."
python3 scripts/migrate.py

# 3. Canonical Reference Seeding
echo "🌱 Verifying canonical skill and role taxonomy..."
python3 scripts/seed_production.py

# 4. Process Launch via Uvicorn
PORT="${PORT:-${BACKEND_PORT:-8000}}"
HOST="${BACKEND_HOST:-0.0.0.0}"
WORKERS="${WORKERS:-4}"

echo "=================================================================="
echo "⚡ Launching Uvicorn production server on ${HOST}:${PORT} (${WORKERS} workers)"
echo "=================================================================="

exec uvicorn app.main:app \
    --host "${HOST}" \
    --port "${PORT}" \
    --workers "${WORKERS}" \
    --proxy-headers \
    --forwarded-allow-ips='*'
