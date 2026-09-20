# ==============================================================================
# SatQuery AI — Multi-Stage Production Dockerfile
# Stage 1: Compile React Frontend with Node 22
# Stage 2: Lightweight Python 3.12 Backend Server
# ==============================================================================

# --- Stage 1: Frontend Build ---
FROM node:22-alpine AS frontend-builder
WORKDIR /web
COPY frontend/ ./
# Preserve the reviewed local UI by default, including translation and speech.
# Opt in to rebuilding only when intentionally updating the frontend.
ARG REBUILD_FRONTEND=0
RUN if [ "$REBUILD_FRONTEND" = "1" ]; then npm ci && npm run build; \
    else test -f dist/index.html; fi

# --- Stage 2: Python Runtime ---
FROM python:3.12-slim AS runtime

RUN apt-get update \
    && apt-get install -y --no-install-recommends libexpat1 curl ca-certificates \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python backend dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

ARG WITH_ML=0
COPY requirements-ml.txt .
RUN if [ "$WITH_ML" = "1" ]; then pip install --no-cache-dir -r requirements-ml.txt; fi

# Copy application code
COPY . .

# Copy compiled React frontend assets from Stage 1
COPY --from=frontend-builder /web/dist ./frontend/dist

# Default environment configurations
ENV PORT=8000 \
    HOST=0.0.0.0 \
    SATQUERY_PIPELINE=legacy \
    PYTHONUNBUFFERED=1

EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
  CMD curl -f http://localhost:${PORT:-8000}/api/health || exit 1

# Start Uvicorn server respecting dynamic PORT
CMD ["sh", "-c", "uvicorn gateway.app:app --host 0.0.0.0 --port ${PORT:-8000}"]
