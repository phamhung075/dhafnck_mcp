# Docker Configuration Guide for DhafnckMCP Platform

This directory contains configuration files for the DhafnckMCP Multi-Project AI Orchestration Platform Docker deployment.

## 📋 Table of Contents

- [Overview](#overview)
- [Configuration Files](#configuration-files)
- [Environment Variables](#environment-variables)
- [Docker Compose Profiles](#docker-compose-profiles)
- [Service Configuration](#service-configuration)
- [Networking](#networking)
- [Security](#security)
- [Performance Tuning](#performance-tuning)

## Overview

The DhafnckMCP Docker configuration supports multiple deployment scenarios:
- **Development**: Full-featured local development with debugging
- **Production**: Optimized for performance and security
- **Testing**: Isolated environment for automated tests
- **Staging**: Production-like environment for validation

## Configuration Files

### Core Configuration Files

| File | Purpose | When to Use |
|------|---------|-------------|
| `docker-compose.yml` | Base configuration | Always (required) |
| `docker-compose.postgres.yml` | PostgreSQL service | Database deployment |
| `docker-compose.redis.yml` | Redis service | Caching layer (optional) |
| `docker-compose.local.yml` | Local overrides | Development |
| `docker-compose.dev.yml` | Development settings | Enhanced debugging |
| `docker-compose.prod.yml` | Production settings | Production deployment |
| `docker-compose.test.yml` | Test configuration | Automated testing |

### Environment Files

| File | Purpose | Example |
|------|---------|---------|
| `.env.example` | Template for environment variables | Copy to `.env` |
| `.env` | Local environment configuration | Git-ignored |
| `.env.production` | Production secrets | Secured storage |
| `.env.test` | Test environment | CI/CD pipelines |

## Environment Variables

### Database Configuration

```bash
# PostgreSQL Primary Database
POSTGRES_USER=dhafnck_user
POSTGRES_PASSWORD=secure_password_here
POSTGRES_DB=dhafnck_mcp
POSTGRES_HOST=postgres
POSTGRES_PORT=5432

# Database URL (constructed from above)
DATABASE_URL=postgresql://${POSTGRES_USER}:${POSTGRES_PASSWORD}@${POSTGRES_HOST}:${POSTGRES_PORT}/${POSTGRES_DB}

# Database Pool Settings
DB_POOL_SIZE=20              # Connection pool size
DB_MAX_OVERFLOW=40           # Max overflow connections
DB_POOL_TIMEOUT=30           # Pool timeout in seconds
DB_ECHO=false                # SQL query logging (true for debug)

# Database Mode
DATABASE_MODE=container      # Options: local, container, mcp_stdin, test
```

### Application Configuration

```bash
# Core Settings
MCP_ENVIRONMENT=development  # Options: development, staging, production
MCP_HOST=0.0.0.0           # Listen on all interfaces in container
MCP_PORT=8000              # Application port
MCP_DEBUG=true             # Debug mode
MCP_LOG_LEVEL=INFO         # Log level: DEBUG, INFO, WARNING, ERROR

# Performance Targets
PERFORMANCE_TARGET_RPS=15000    # Target requests per second
VISION_PERFORMANCE_TARGET=5     # Vision System overhead target (ms)
```

### 4-Tier Context System

```bash
# Context Hierarchy Configuration
CONTEXT_CACHE_TTL=3600              # Cache TTL in seconds
CONTEXT_INHERITANCE_ENABLED=true    # Enable inheritance
CONTEXT_DELEGATION_ENABLED=true     # Enable upward delegation
CONTEXT_AUTO_CREATE=true            # Auto-create contexts
CONTEXT_SYNC_ENABLED=true           # Real-time synchronization

# Context Cache Settings
CONTEXT_CACHE_MAX_SIZE=1000         # Max cached contexts
CONTEXT_CACHE_STRATEGY=lru          # Cache strategy: lru, lfu
```

### Vision System

```bash
# Vision System Core
VISION_SYSTEM_ENABLED=true          # Enable Vision System
VISION_CACHE_ENABLED=true           # Cache vision insights
VISION_WORKFLOW_HINTS=true          # Enable workflow guidance
VISION_PROGRESS_TRACKING=true       # Rich progress tracking

# Vision Performance
VISION_CACHE_TTL=1800              # Vision cache TTL
VISION_MAX_WORKERS=4               # Parallel vision workers
VISION_BATCH_SIZE=10               # Batch processing size
```

### Redis Cache (Optional)

```bash
# Redis Configuration
REDIS_ENABLED=true                 # Enable Redis
REDIS_HOST=redis                   # Redis hostname
REDIS_PORT=6379                    # Redis port
REDIS_PASSWORD=redis_password      # Redis password
REDIS_DB=0                         # Redis database number
REDIS_URL=redis://:${REDIS_PASSWORD}@${REDIS_HOST}:${REDIS_PORT}/${REDIS_DB}

# Redis Settings
REDIS_MAX_CONNECTIONS=50           # Max connections
REDIS_CONNECTION_TIMEOUT=5         # Connection timeout
```

### Authentication & Security

```bash
# Authentication
AUTH_ENABLED=true                  # Enable authentication
AUTH_TOKEN_TTL=3600               # Token TTL in seconds
AUTH_SECRET_KEY=your-secret-key   # JWT secret key
AUTH_ALGORITHM=HS256              # JWT algorithm

# Security Settings
CORS_ENABLED=true                 # Enable CORS
CORS_ORIGINS=["http://localhost:3000"]  # Allowed origins
RATE_LIMIT_ENABLED=true           # Enable rate limiting
RATE_LIMIT_REQUESTS=1000          # Requests per minute
SSL_ENABLED=false                 # SSL/TLS (handled by reverse proxy)
```

### Agent Configuration

```bash
# Agent Library
AGENT_LIBRARY_PATH=/app/agent-library    # Agent definitions
AGENT_CACHE_ENABLED=true                 # Cache agent configs
AGENT_HOT_RELOAD=true                    # Hot reload agents

# Agent Execution
AGENT_TIMEOUT=300                        # Agent timeout (seconds)
AGENT_MAX_RETRIES=3                      # Max retry attempts
AGENT_CONCURRENT_LIMIT=10                # Concurrent agents
```

## Docker Compose Profiles

### Development Profile

```yaml
# docker-compose.dev.yml
services:
  dhafnck-mcp:
    environment:
      - MCP_DEBUG=true
      - MCP_LOG_LEVEL=DEBUG
      - DB_ECHO=true
      - HOT_RELOAD=true
    volumes:
      - ../src:/app/src  # Mount source for hot reload
    ports:
      - "8001:8001"      # Debug port
```

### Production Profile

```yaml
# docker-compose.prod.yml
services:
  dhafnck-mcp:
    environment:
      - MCP_DEBUG=false
      - MCP_LOG_LEVEL=WARNING
      - DB_ECHO=false
    deploy:
      replicas: 3
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

## Service Configuration

### PostgreSQL Service

```yaml
postgres:
  image: postgres:14-alpine
  environment:
    POSTGRES_USER: ${POSTGRES_USER}
    POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    POSTGRES_DB: ${POSTGRES_DB}
    POSTGRES_INITDB_ARGS: "--encoding=UTF8 --locale=en_US.utf8"
  command:
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "effective_cache_size=1GB"
    - "-c"
    - "work_mem=4MB"
```

### MCP Server Service

```yaml
dhafnck-mcp:
  build:
    context: ..
    dockerfile: docker/Dockerfile
    args:
      PYTHON_VERSION: 3.12
  environment:
    DATABASE_URL: ${DATABASE_URL}
    REDIS_URL: ${REDIS_URL}
  healthcheck:
    test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
    interval: 30s
    timeout: 10s
    retries: 3
```

### Redis Service (Optional)

```yaml
redis:
  image: redis:7-alpine
  command: redis-server --requirepass ${REDIS_PASSWORD}
  volumes:
    - redis_data:/data
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 30s
    timeout: 10s
```

## Networking

### Network Configuration

```yaml
networks:
  dhafnck_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.28.0.0/16
```

### Service Discovery

Services can communicate using container names:
- `postgres`: PostgreSQL database
- `dhafnck-mcp`: MCP server
- `redis`: Redis cache

### Port Mapping

| Service | Internal Port | External Port | Purpose |
|---------|--------------|---------------|---------|
| MCP Server | 8000 | 8000 | HTTP API |
| PostgreSQL | 5432 | 54320 | Database |
| Redis | 6379 | 63790 | Cache |

## Security

### Security Best Practices

1. **Environment Variables**
   - Never commit `.env` files
   - Use Docker secrets for production
   - Rotate credentials regularly

2. **Network Security**
   - Use internal networks for service communication
   - Expose only necessary ports
   - Use reverse proxy for SSL termination

3. **Container Security**
   - Run containers as non-root user
   - Use read-only filesystems where possible
   - Implement resource limits

### Example Security Configuration

```yaml
services:
  dhafnck-mcp:
    user: "1000:1000"  # Non-root user
    read_only: true
    tmpfs:
      - /tmp
      - /app/temp
    security_opt:
      - no-new-privileges:true
    cap_drop:
      - ALL
    cap_add:
      - NET_BIND_SERVICE
```

## Performance Tuning

### PostgreSQL Optimization

```bash
# Shared memory
POSTGRES_SHARED_BUFFERS=512MB       # 25% of RAM
POSTGRES_EFFECTIVE_CACHE_SIZE=2GB   # 75% of RAM

# Connection pooling
POSTGRES_MAX_CONNECTIONS=200
POSTGRES_SUPERUSER_RESERVED=3

# Query performance
POSTGRES_WORK_MEM=8MB
POSTGRES_MAINTENANCE_WORK_MEM=128MB

# Write performance
POSTGRES_CHECKPOINT_SEGMENTS=32
POSTGRES_CHECKPOINT_COMPLETION_TARGET=0.9
```

### Application Optimization

```bash
# Worker processes
WORKERS=4                          # Number of worker processes
WORKER_CONNECTIONS=1000           # Connections per worker

# Request handling
REQUEST_TIMEOUT=30                # Request timeout
KEEPALIVE_TIMEOUT=5              # Keep-alive timeout

# Memory management
MEMORY_LIMIT=2048                # Memory limit in MB
MEMORY_RESERVATION=1024          # Memory reservation in MB
```

### Redis Optimization

```bash
# Memory management
REDIS_MAXMEMORY=512mb            # Max memory usage
REDIS_MAXMEMORY_POLICY=lru       # Eviction policy

# Persistence
REDIS_SAVE="900 1 300 10 60 10000"  # Save intervals
REDIS_AOF_ENABLED=yes            # Append-only file

# Performance
REDIS_TCP_BACKLOG=511
REDIS_TCP_KEEPALIVE=300
```

## Deployment Commands

### Development Deployment

```bash
# Start with development configuration
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml -f docker-compose.dev.yml up -d

# Watch logs
docker-compose logs -f dhafnck-mcp
```

### Production Deployment

```bash
# Deploy with production settings
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml -f docker-compose.redis.yml -f docker-compose.prod.yml up -d

# Scale MCP servers
docker-compose up -d --scale dhafnck-mcp=3
```

### Maintenance Commands

```bash
# Database backup
docker exec postgres pg_dump -U ${POSTGRES_USER} ${POSTGRES_DB} > backup.sql

# Redis backup
docker exec redis redis-cli BGSAVE

# Update containers
docker-compose pull
docker-compose up -d

# Clean up
docker system prune -f
```

---
*Last Updated: 2025-01-31 - Comprehensive Docker configuration guide for DhafnckMCP Platform*