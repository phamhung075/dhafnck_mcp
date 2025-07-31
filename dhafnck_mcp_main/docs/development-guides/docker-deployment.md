# Docker Deployment Guide

## Overview

This guide covers deploying DhafnckMCP using Docker containers for both development and production environments. The system supports multiple deployment modes with proper database persistence and configuration management.

## Quick Start

### Development Deployment
```bash
# Clone the repository
git clone <repository-url>
cd dhafnck_mcp_main

# Build and start services
docker-compose up --build

# Check service health
curl http://localhost:8000/health
```

### Production Deployment
```bash
# Use production compose file
docker-compose -f docker-compose.prod.yml up -d

# Monitor logs
docker-compose logs -f dhafnck-mcp
```

## Container Architecture

### Service Components
```yaml
services:
  dhafnck-mcp:
    image: dhafnck/mcp-server:latest
    ports:
      - "8000:8000"
    volumes:
      - dhafnck_data:/data
    environment:
      - DATABASE_URL=/data/dhafnck_mcp.db
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dhafnck-db:
    image: postgres:13
    environment:
      - POSTGRES_DB=dhafnck_mcp
      - POSTGRES_USER=dhafnck
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

volumes:
  dhafnck_data:
  postgres_data:
```

## Database Configuration

### PostgreSQL (Primary Database)
```yaml
# docker-compose.yml
services:
  dhafnck-mcp:
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp
    depends_on:
      - postgres
  
  postgres:
    image: postgres:14-alpine
    environment:
      - POSTGRES_DB=dhafnck_mcp
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

### PostgreSQL (Production)
```yaml
# docker-compose.prod.yml
services:
  dhafnck-mcp:
    environment:
      - DATABASE_URL=postgresql+asyncpg://dhafnck:${DB_PASSWORD}@dhafnck-db:5432/dhafnck_mcp
    depends_on:
      - dhafnck-db
```

## Environment Configuration

### Environment Variables
```bash
# .env file
# Database
DATABASE_URL=postgresql://postgres:${DB_PASSWORD}@postgres:5432/dhafnck_mcp
DB_PASSWORD=secure_password_here

# Server
HOST=0.0.0.0
PORT=8000
LOG_LEVEL=INFO

# Authentication
JWT_SECRET_KEY=your_jwt_secret_key
TOKEN_EXPIRY_HOURS=24

# Cache
REDIS_URL=redis://dhafnck-redis:6379
CACHE_TTL_SECONDS=3600

# Performance
MAX_CONNECTIONS=100
POOL_SIZE=20
```

### Development Environment
```bash
# .env.development
DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp_dev
LOG_LEVEL=DEBUG
ENABLE_DEBUG_ROUTES=true
CORS_ORIGINS=http://localhost:3000,http://localhost:8080
```

### Production Environment
```bash
# .env.production
DATABASE_URL=postgresql+asyncpg://dhafnck:${DB_PASSWORD}@dhafnck-db:5432/dhafnck_mcp
LOG_LEVEL=WARNING
ENABLE_DEBUG_ROUTES=false
CORS_ORIGINS=https://your-frontend-domain.com
SENTRY_DSN=your_sentry_dsn
```

## Dockerfile

### Multi-stage Production Build
```dockerfile
# Build stage
FROM python:3.11-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Production stage
FROM python:3.11-slim

WORKDIR /app

# Install runtime dependencies
RUN apt-get update && apt-get install -y \
    libpq5 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy Python packages from builder
COPY --from=builder /root/.local /root/.local

# Copy application code
COPY src/ ./src/
COPY alembic.ini .
COPY alembic/ ./alembic/

# Create data directory
RUN mkdir -p /data && chmod 755 /data

# Create non-root user
RUN groupadd -r dhafnck && useradd -r -g dhafnck dhafnck
RUN chown -R dhafnck:dhafnck /app /data
USER dhafnck

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Expose port
EXPOSE 8000

# Start application
CMD ["python", "-m", "fastmcp.task_management.main"]
```

### Development Dockerfile
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies including development tools
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    git \
    vim \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt requirements-dev.txt ./
RUN pip install --no-cache-dir -r requirements-dev.txt

# Copy application code
COPY . .

# Create data directory
RUN mkdir -p /data

# Expose port
EXPOSE 8000

# Development command with hot reload
CMD ["python", "-m", "uvicorn", "fastmcp.task_management.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

## Docker Compose Configurations

### Development Setup
```yaml
# docker-compose.yml
version: '3.8'

services:
  dhafnck-mcp:
    build:
      context: .
      dockerfile: Dockerfile.dev
    ports:
      - "8000:8000"
    volumes:
      - .:/app
      - dhafnck_data:/data
    environment:
      - DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp_dev
      - LOG_LEVEL=DEBUG
      - PYTHONPATH=/app/src
    env_file:
      - .env.development
    depends_on:
      - dhafnck-redis
    restart: unless-stopped

  dhafnck-redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    restart: unless-stopped

volumes:
  dhafnck_data:
  redis_data:
```

### Production Setup
```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  dhafnck-mcp:
    image: dhafnck/mcp-server:${VERSION:-latest}
    ports:
      - "8000:8000"
    volumes:
      - dhafnck_data:/data
    environment:
      - DATABASE_URL=postgresql+asyncpg://dhafnck:${DB_PASSWORD}@dhafnck-db:5432/dhafnck_mcp
    env_file:
      - .env.production
    depends_on:
      - dhafnck-db
      - dhafnck-redis
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3

  dhafnck-db:
    image: postgres:13
    environment:
      - POSTGRES_DB=dhafnck_mcp
      - POSTGRES_USER=dhafnck
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./docker/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    restart: unless-stopped
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U dhafnck"]
      interval: 30s
      timeout: 10s
      retries: 5

  dhafnck-redis:
    image: redis:6-alpine
    volumes:
      - redis_data:/data
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./docker/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./docker/nginx/ssl:/etc/nginx/ssl
    depends_on:
      - dhafnck-mcp
    restart: unless-stopped

volumes:
  dhafnck_data:
  postgres_data:
  redis_data:
```

## Database Management

### Database Initialization
```bash
# Initialize database schema
docker-compose exec dhafnck-mcp python -m alembic upgrade head

# Create initial admin user
docker-compose exec dhafnck-mcp python -m fastmcp.task_management.scripts.create_admin
```

### Database Migrations
```bash
# Create new migration
docker-compose exec dhafnck-mcp python -m alembic revision --autogenerate -m "Description"

# Apply migrations
docker-compose exec dhafnck-mcp python -m alembic upgrade head

# Rollback migration
docker-compose exec dhafnck-mcp python -m alembic downgrade -1
```

### Database Backup and Restore
```bash
# Backup PostgreSQL database (recommended)
docker-compose exec postgres pg_dump -U postgres dhafnck_mcp > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup PostgreSQL database
docker-compose exec dhafnck-db pg_dump -U dhafnck dhafnck_mcp > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore PostgreSQL database
docker-compose exec -T dhafnck-db psql -U dhafnck dhafnck_mcp < backup_file.sql
```

## Container Management

### Common Operations
```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart specific service
docker-compose restart dhafnck-mcp

# View logs
docker-compose logs -f dhafnck-mcp

# Execute commands in container
docker-compose exec dhafnck-mcp bash

# Scale services (if using multiple replicas)
docker-compose up -d --scale dhafnck-mcp=3
```

### Container Health Monitoring
```bash
# Check container health
docker-compose ps

# Detailed health status
docker inspect --format='{{.State.Health.Status}}' dhafnck-mcp

# Health check logs
docker inspect --format='{{range .State.Health.Log}}{{.Output}}{{end}}' dhafnck-mcp
```

## Monitoring and Logging

### Log Configuration
```yaml
# docker-compose.yml
services:
  dhafnck-mcp:
    logging:
      driver: "json-file"
      options:
        max-size: "10m"
        max-file: "3"
```

### Monitoring Stack
```yaml
# docker-compose.monitoring.yml
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./docker/prometheus/prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus

  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    volumes:
      - grafana_data:/var/lib/grafana
      - ./docker/grafana/dashboards:/etc/grafana/provisioning/dashboards
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=${GRAFANA_PASSWORD}

  loki:
    image: grafana/loki
    ports:
      - "3100:3100"
    volumes:
      - ./docker/loki/local-config.yaml:/etc/loki/local-config.yaml
      - loki_data:/loki

volumes:
  prometheus_data:
  grafana_data:
  loki_data:
```

## Security Configuration

### SSL/TLS Setup
```nginx
# docker/nginx/nginx.conf
server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;

    location / {
        proxy_pass http://dhafnck-mcp:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Container Security
```dockerfile
# Security hardening in Dockerfile
# Run as non-root user
RUN groupadd -r dhafnck && useradd -r -g dhafnck dhafnck
USER dhafnck

# Remove unnecessary packages
RUN apt-get autoremove -y && apt-get autoclean

# Set secure file permissions
RUN chmod 755 /app && chmod 600 /app/config/*
```

## Performance Optimization

### Resource Limits
```yaml
# docker-compose.yml
services:
  dhafnck-mcp:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: '0.5'
        reservations:
          memory: 256M
          cpus: '0.25'
```

### Connection Pooling
```python
# Database connection configuration
DATABASE_CONFIG = {
    "pool_size": 20,
    "max_overflow": 30,
    "pool_timeout": 30,
    "pool_recycle": 3600
}
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker-compose logs dhafnck-mcp

# Check configuration
docker-compose config

# Validate Dockerfile
docker build -t test-image .
```

#### Database Connection Issues
```bash
# Test database connectivity
docker-compose exec dhafnck-mcp python -c "from src.fastmcp.task_management.infrastructure.database import test_connection; test_connection()"

# Check database container
docker-compose exec dhafnck-db psql -U dhafnck -d dhafnck_mcp -c "SELECT 1;"
```

#### Performance Issues
```bash
# Monitor resource usage
docker stats

# Check container metrics
docker-compose exec dhafnck-mcp top

# Review slow queries
docker-compose logs dhafnck-mcp | grep "slow query"
```

### Debug Mode
```yaml
# docker-compose.debug.yml
services:
  dhafnck-mcp:
    environment:
      - LOG_LEVEL=DEBUG
      - ENABLE_DEBUG_ROUTES=true
    ports:
      - "8000:8000"
      - "5678:5678"  # Debug port
    volumes:
      - .:/app
    command: ["python", "-m", "debugpy", "--listen", "0.0.0.0:5678", "--wait-for-client", "-m", "fastmcp.task_management.main"]
```

## CI/CD Integration

### GitHub Actions
```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]
  
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    
    - name: Build Docker image
      run: docker build -t dhafnck/mcp-server:${{ github.sha }} .
    
    - name: Test Docker image
      run: |
        docker run -d --name test-container dhafnck/mcp-server:${{ github.sha }}
        sleep 30
        docker exec test-container curl -f http://localhost:8000/health
    
    - name: Push to registry
      run: |
        echo ${{ secrets.DOCKER_PASSWORD }} | docker login -u ${{ secrets.DOCKER_USERNAME }} --password-stdin
        docker push dhafnck/mcp-server:${{ github.sha }}
        docker tag dhafnck/mcp-server:${{ github.sha }} dhafnck/mcp-server:latest
        docker push dhafnck/mcp-server:latest
```

## Deployment Checklist

### Pre-deployment
- [ ] Environment variables configured
- [ ] SSL certificates in place
- [ ] Database backup created
- [ ] Resource limits set
- [ ] Health checks configured

### Deployment
- [ ] Pull latest images
- [ ] Run database migrations
- [ ] Start services with zero downtime
- [ ] Verify health checks pass
- [ ] Test critical functionality

### Post-deployment
- [ ] Monitor application logs
- [ ] Check system metrics
- [ ] Verify database connectivity
- [ ] Test user workflows
- [ ] Update monitoring dashboards

## Maintenance

### Regular Tasks
```bash
# Weekly cleanup
docker system prune -f

# Update images
docker-compose pull
docker-compose up -d

# Database optimization
docker-compose exec dhafnck-db psql -U dhafnck -d dhafnck_mcp -c "VACUUM ANALYZE;"

# Log rotation
docker-compose exec dhafnck-mcp logrotate /etc/logrotate.conf
```

### Backup Strategy
```bash
#!/bin/bash
# backup.sh - Daily backup script

DATE=$(date +%Y%m%d_%H%M%S)

# Backup database
docker-compose exec -T dhafnck-db pg_dump -U dhafnck dhafnck_mcp | gzip > backup_db_$DATE.sql.gz

# Backup data volume
docker run --rm -v dhafnck_data:/data -v $(pwd):/backup alpine tar czf /backup/backup_data_$DATE.tar.gz -C /data .

# Clean old backups (keep 30 days)
find . -name "backup_*" -mtime +30 -delete
```

This Docker deployment guide provides comprehensive coverage of deploying DhafnckMCP in containerized environments, from development to production, with proper security, monitoring, and maintenance procedures.