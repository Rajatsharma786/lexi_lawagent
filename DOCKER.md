# Lexi Law Agent - Docker Deployment

## 🐳 Docker Setup

This directory contains Docker configuration for containerized deployment of Lexi Law Agent.

### Prerequisites

- Docker installed (20.10+)
- Docker Compose installed (1.29+)
- `.env` file configured with your credentials

### Quick Start

1. **Configure environment variables**:
```bash
cp .env.example .env
# Edit .env with your actual credentials
```

2. **Build and run with Docker Compose**:
```bash
docker-compose up -d
```

3. **Access the application**:
```
http://localhost:8501
```

4. **View logs**:
```bash
docker-compose logs -f
```

5. **Stop the application**:
```bash
docker-compose down
```

### Manual Docker Build

If you prefer to build without Docker Compose:

```bash
# Build image
docker build -t lexi-law-agent .

# Run container
docker run -p 8501:8501 \
  --env-file .env \
  -v $(pwd)/.chroma_cache:/app/.chroma_cache \
  lexi-law-agent
```

### Environment Variables

All environment variables should be set in `.env` file:

- `OPENAI_API_KEY`: Your OpenAI API key
- `AZURE_POSTGRES_*`: Azure PostgreSQL connection details
- `LAWS_CHROMA_SAS_URL`: SAS URL for laws ChromaDB (optional)
- `PROCS_CHROMA_SAS_URL`: SAS URL for procedures ChromaDB (optional)
- `REDIS_HOST`, `REDIS_PORT`, `REDIS_PASSWORD`: Redis Cloud credentials
- `ARIZE_PHNX`: Phoenix tracing API key (optional)

### Volumes

The Docker setup creates persistent volumes for:
- `.chroma_cache`: Downloaded ChromaDB from Azure Blob
- `laws_db_chroma`: Local laws database
- `procedures_db_chroma`: Local procedures database

### Health Check

The container includes a health check that monitors Streamlit's status:
- Interval: 30 seconds
- Timeout: 10 seconds
- Start period: 40 seconds

Check container health:
```bash
docker ps
# Look for "healthy" status
```

### Production Deployment

For production deployments, consider:

1. **Use secrets management** instead of `.env` file
2. **Set resource limits**:
```yaml
services:
  lexi-law-agent:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
```

3. **Use a reverse proxy** (nginx/traefik) for HTTPS
4. **Enable container monitoring** (Prometheus, Grafana)

### Troubleshooting

**Container won't start**:
```bash
docker-compose logs lexi-law-agent
```

**Out of memory**:
Increase Docker memory limit in Docker Desktop settings or add memory limits to docker-compose.yml

**ChromaDB sync issues**:
Check SAS URLs are valid and have read+list permissions

**Connection refused**:
Ensure port 8501 is not already in use:
```bash
# Windows
netstat -ano | findstr :8501

# Linux/Mac
lsof -i :8501
```

### Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart
docker-compose down
docker-compose build --no-cache
docker-compose up -d
```
