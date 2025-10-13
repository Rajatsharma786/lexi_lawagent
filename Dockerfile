# syntax=docker/dockerfile:1.7

# ============================================
# Stage 1: Builder — create a self-contained venv
# ============================================
FROM python:3.11-slim-bookworm AS builder

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Build tools only in the builder
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      gcc \
      g++ \
      libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install Python dependencies into an isolated venv
COPY requirements.txt .
RUN python -m venv /opt/venv \
 && /opt/venv/bin/pip install --upgrade pip \
 && /opt/venv/bin/pip install --no-cache-dir -r requirements.txt

# ============================================
# Stage 2: Runtime — minimal production image
# ============================================
FROM python:3.11-slim-bookworm

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    DEBIAN_FRONTEND=noninteractive \
    PATH="/opt/venv/bin:${PATH}"

WORKDIR /app

# Runtime libs only (no compilers)
RUN apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      poppler-utils \
      libpq5 \
      libgl1-mesa-glx \
      libglib2.0-0 \
      libsm6 \
      libxext6 \
      libxrender1 \
      libgomp1 \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Bring in only the built virtualenv from the builder
COPY --from=builder /opt/venv /opt/venv

# Copy application code
COPY src/ ./src/
# If you have Streamlit config, uncomment:
# COPY .streamlit/ ./.streamlit/

# App local writable dirs (Chroma caches, tmp, etc.)
RUN mkdir -p .chroma_cache laws_db_chroma procedures_db_chroma /app/tmp

# Set temp dirs so anything writing to /tmp uses app-local storage
ENV TMPDIR=/app/tmp \
    TEMP=/app/tmp \
    TMP=/app/tmp

# Streamlit defaults suitable for App Service (optional, can also be env vars in App Settings)
ENV STREAMLIT_SERVER_HEADLESS=true \
    STREAMLIT_SERVER_ENABLE_CORS=false \
    STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION=false

# Health check
EXPOSE 8501
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run as non-root
USER appuser
# Start Streamlit
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
