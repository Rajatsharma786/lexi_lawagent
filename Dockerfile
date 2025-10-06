# syntax=docker/dockerfile:1.7

FROM python:3.11-slim-bookworm

# Keep image small & predictable
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# System deps (runtime only)
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
 && apt-get update \
 && apt-get install -y --no-install-recommends \
      tesseract-ocr \
      poppler-utils \
      libpq-dev \
      curl \
 && rm -rf /var/lib/apt/lists/*

# Python deps first to maximize caching
COPY requirements.txt .
RUN python -m pip install --upgrade pip \
 && pip install -r requirements.txt

# App code
COPY src/ ./src/
# (Optional) settings dir if you have it
COPY .streamlit/ ./.streamlit/

# ChromaDB local dirs (if your app expects them)
RUN mkdir -p .chroma_cache laws_db_chroma procedures_db_chroma

# Streamlit port
EXPOSE 8501

# Healthcheck for App Service/K8s/etc.
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
  CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Run
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]
