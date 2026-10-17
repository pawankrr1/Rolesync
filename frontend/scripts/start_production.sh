#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# Career Intelligence Platform - Production Frontend Entrypoint
# ==============================================================================

echo "=================================================================="
echo "🌐 STARTING CAREER INTELLIGENCE PRODUCTION FRONTEND"
echo "Timestamp: $(date -u +"%Y-%m-%dT%H:%M:%SZ")"
echo "=================================================================="

cd "$(dirname "$0")/.."

PORT="${PORT:-3000}"
HOSTNAME="${HOSTNAME:-0.0.0.0}"

echo "Configured API Gateway: ${NEXT_PUBLIC_API_URL:-http://localhost:8000}"
echo "Binding Address:       ${HOSTNAME}:${PORT}"

# Execute Next.js production server
exec npm run start -- -p "${PORT}" -H "${HOSTNAME}"
