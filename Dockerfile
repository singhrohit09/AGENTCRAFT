# ==============================================================================
# AgentCraft / RakshaGrid — Production Multi-Stage Containerfile
# AGENTCRAFT 2026 National AI Agent Challenge
# ==============================================================================

# ------------------------------------------------------------------------------
# Stage 1: Build Frontend Assets (React + Vite)
# ------------------------------------------------------------------------------
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend

COPY frontend/package*.json ./
RUN npm ci

COPY frontend/ ./
RUN npm run build

# ------------------------------------------------------------------------------
# Stage 2: Production Python Backend Runtime
# ------------------------------------------------------------------------------
FROM python:3.12-slim AS runner
WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8000 \
    AGENTCRAFT_ENV=production \
    AGENTCRAFT_DEBUG=false \
    RAKSHAGRID_DEMO_MODE=false

# Install curl for healthcheck and system essentials
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY backend/requirements.txt ./backend/requirements.txt
RUN pip install --no-cache-dir -r ./backend/requirements.txt

# Copy application code
COPY ai/ ./ai/
COPY backend/ ./backend/
COPY alembic.ini ./alembic.ini

# Copy prebuilt frontend static files from Stage 1 into frontend/dist
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Expose HTTP port
EXPOSE 8000

# Container Healthcheck targeting the RakshaGrid health endpoint
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:8000/api/rakshagrid/health || exit 1

# Production entrypoint
CMD ["python", "-m", "uvicorn", "backend.app:app", "--host", "0.0.0.0", "--port", "8000"]
