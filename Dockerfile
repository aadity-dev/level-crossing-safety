# Multi-Stage Production Build: Frontend Build + Python Edge Vision Backend

# -----------------------------------------------------------------------------
# Stage 1: Build React Vite TypeScript Modern Dashboard
# -----------------------------------------------------------------------------
FROM node:20-slim AS frontend-builder
WORKDIR /app/web

COPY web/package.json ./
RUN npm install

COPY web/ ./
RUN npm run build

# -----------------------------------------------------------------------------
# Stage 2: Python Runtime & FastAPI OCC Backend
# -----------------------------------------------------------------------------
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

# Install system runtime libraries for OpenCV and FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    ffmpeg \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt pyproject.toml ./
RUN pip install --upgrade pip && \
    pip install -r requirements.txt && \
    pip install .

# Copy application source and configs
COPY src/ ./src/
COPY configs/ ./configs/
COPY data/ ./data/

# Copy built frontend assets from Stage 1
COPY --from=frontend-builder /app/web/dist ./web/dist

# Expose HTTP API & Dashboard port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Launch FastAPI ASGI server
CMD ["uvicorn", "level_crossing.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
