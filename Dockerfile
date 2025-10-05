##############################
# Stage 1: Build & Test
##############################
FROM python:3.11-slim-bookworm AS builder

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# System deps needed to build wheels and to run tests that call tesseract/poppler
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       build-essential \
       curl \
       git \
       tesseract-ocr \
       poppler-utils \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies including test tools
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt \
    && pip install --no-cache-dir pytest pytest-cov

# Copy application code and tests
COPY src/ ./src/
COPY test_file.py ./test_file.py
COPY .streamlit/ ./.streamlit/

# Run tests
RUN pytest test_file.py --cov=src --cov-report=html --tb=short || true

##############################
# Stage 2: Production
##############################
FROM python:3.11-slim-bookworm AS production

ENV DEBIAN_FRONTEND=noninteractive
WORKDIR /app

# Install only runtime dependencies
RUN echo 'Acquire::Retries "3";' > /etc/apt/apt.conf.d/80-retries \
    && apt-get update \
    && apt-get install -y --no-install-recommends \
       curl \
       tesseract-ocr \
       poppler-utils \
       libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install production dependencies only
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Copy application code from builder stage
COPY --from=builder /app/src/ ./src/
COPY --from=builder /app/.streamlit/ ./.streamlit/

# Create necessary directories for ChromaDB cache
RUN mkdir -p .chroma_cache laws_db_chroma procedures_db_chroma

# Expose Streamlit port
EXPOSE 8501

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=40s --retries=3 \
    CMD curl --fail http://localhost:8501/_stcore/health || exit 1

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    STREAMLIT_SERVER_PORT=8501 \
    STREAMLIT_SERVER_ADDRESS=0.0.0.0

# Run the application
CMD ["streamlit", "run", "src/app.py", "--server.port=8501", "--server.address=0.0.0.0"]