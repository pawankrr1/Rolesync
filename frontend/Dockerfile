# ==============================================================================
# Career Intelligence Platform - Production Frontend Dockerfile
# Optimized Multi-Stage Next.js Build
# ==============================================================================

# Stage 1: Dependencies Installation
FROM node:20-alpine AS deps
RUN apk add --no-cache libc6-compat
WORKDIR /app

COPY package*.json ./
RUN npm ci

# Stage 2: Next.js Production Compilation
FROM node:20-alpine AS builder
WORKDIR /app

COPY --from=deps /app/node_modules ./node_modules
COPY . .

# Build-time API configuration for inlined client-side environment variables
ARG NEXT_PUBLIC_API_URL=http://localhost:8000
ENV NEXT_PUBLIC_API_URL=${NEXT_PUBLIC_API_URL} \
    NEXT_TELEMETRY_DISABLED=1 \
    NODE_ENV=production

RUN npm run build

# Stage 3: Minimal Production Runtime
FROM node:20-alpine AS runner
WORKDIR /app

ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    PORT=3000 \
    HOSTNAME="0.0.0.0"

# Install curl for health checking
RUN apk add --no-cache curl

# Create unprivileged application user
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy essential build outputs
COPY --from=builder /app/public ./public
COPY --from=builder --chown=nextjs:nodejs /app/.next ./.next
COPY --from=builder /app/node_modules ./node_modules
COPY --from=builder /app/package.json ./package.json
COPY --from=builder /app/scripts ./scripts

RUN chmod +x scripts/*.sh 2>/dev/null || true

USER nextjs

EXPOSE 3000

# Docker Healthcheck targeting dedicated Next.js health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:3000/api/health || exit 1

# Production server start
CMD ["npm", "run", "start", "--", "-p", "3000", "-H", "0.0.0.0"]
