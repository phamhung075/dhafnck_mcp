# 🐳 DhafnckMCP Multi-Project AI Orchestration Platform - Docker Guide

Complete guide for deploying the DhafnckMCP platform with Docker, featuring PostgreSQL database, 4-tier hierarchical context system, Vision System integration, and 60+ specialized AI agents.

## 📋 Table of Contents

- [Quick Start](#-quick-start)
- [System Overview](#-system-overview)
- [Prerequisites](#-prerequisites)
- [Installation & Setup](#-installation--setup)
- [Usage Commands](#-usage-commands)
- [Configuration](#-configuration)
- [Data Storage](#-data-storage)
- [Development Mode](#-development-mode)
- [Troubleshooting](#-troubleshooting)
- [Architecture](#-architecture)
- [Advanced Usage](#-advanced-usage)

## 🚀 Quick Start

### 1. Start the Server
```bash
# Navigate to project root
cd dhafnck_mcp_main

# Start the server with PostgreSQL (creates containers if needed)
./scripts/manage-docker.sh start
```

### 2. Verify It's Working
```bash
# Check server health
./scripts/manage-docker.sh health

# View server status
./scripts/manage-docker.sh status

# Test database connection
docker exec dhafnck-mcp-server psql -U postgres -d dhafnck_mcp -c "SELECT 1;"
```

### 3. Connect Your MCP Client
- **MCP Server URL**: `http://localhost:8000/mcp/`
- **Authentication**: Token-based (configurable)
- **Available Tools**: 15+ MCP tool categories with 60+ specialized agents
- **Context System**: 4-tier hierarchy (Global→Project→Branch→Task)
- **Vision System**: Strategic AI orchestration with <5ms overhead

## 🏗️ System Overview

The DhafnckMCP Docker system provides:

- **🐘 PostgreSQL Database**: Production-ready database with JSONB support
- **🏗️ 4-Tier Context System**: Hierarchical context management with inheritance
- **👁️ Vision System Integration**: Strategic AI orchestration for all operations
- **🤖 60+ AI Agents**: Specialized agents for every development task
- **📦 Multi-Container Architecture**: PostgreSQL + MCP Server + Redis (optional)
- **🔄 Development Mode**: Full-featured local development environment
- **📊 Performance Monitoring**: Built-in metrics and health checks
- **💾 Data Persistence**: PostgreSQL volumes for all project data

## 📋 Prerequisites

### Required Software
- **Docker Desktop** or **Docker Engine** (20.10+)
- **Docker Compose** (v2.0+)
- **PostgreSQL Client** (for database management)
- **bash** shell (for management scripts)
- **curl** and **netcat** (for health checks)

### System Requirements
- **OS**: Linux (WSL2), macOS, or Windows with Docker Desktop
- **RAM**: Minimum 2GB available for Docker (PostgreSQL + MCP Server)
- **Storage**: 5GB free space for images, volumes, and database
- **CPU**: 2+ cores recommended for optimal performance

### Verify Prerequisites
```bash
# Check Docker version
docker --version
docker-compose --version

# Test Docker is running
docker ps

# Check PostgreSQL client (optional but recommended)
psql --version
```

## 🛠️ Installation & Setup

### 1. Clone and Navigate
```bash
git clone <repository-url>
cd dhafnck_mcp_main
```

### 2. Make Scripts Executable
```bash
chmod +x scripts/manage-docker.sh
```

### 3. Create Required Directories
```bash
# These are created automatically, but you can create them manually:
mkdir -p docker/data/{tasks,projects,rules}
mkdir -p docker/logs
```

### 4. Configure Environment
```bash
# Copy environment template
cp docker/.env.example docker/.env

# Edit configuration for PostgreSQL and other settings
nano docker/.env
```

### 5. Start the System
```bash
# Start all containers (PostgreSQL + MCP Server)
./scripts/manage-docker.sh start

# Or use docker-compose directly
docker-compose -f docker/docker-compose.yml up -d
```

## 🎮 Usage Commands

### Management Script Commands

```bash
# Start the container (creates if doesn't exist)
./scripts/manage-docker.sh start

# Stop the running container
./scripts/manage-docker.sh stop

# Restart the container
./scripts/manage-docker.sh restart

# Show live logs (Ctrl+C to exit)
./scripts/manage-docker.sh logs

# Check container status and resource usage
./scripts/manage-docker.sh status

# Verify server health
./scripts/manage-docker.sh health

# Open shell inside container for debugging
./scripts/manage-docker.sh shell

# Remove container (preserves data volumes)
./scripts/manage-docker.sh remove

# Complete cleanup and rebuild
./scripts/manage-docker.sh cleanup

# Show help and available commands
./scripts/manage-docker.sh help
```

### Direct Docker Commands

```bash
# View all containers
docker ps -a

# View container logs
docker logs dhafnck-mcp-server -f

# Execute commands in container
docker exec -it dhafnck-mcp-server /bin/bash

# View resource usage
docker stats dhafnck-mcp-server

# View volumes
docker volume ls | grep dhafnck
```

## ⚙️ Configuration

### Environment Variables

The system uses these key environment variables:

```bash
# PostgreSQL Database Configuration
DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp
DATABASE_MODE=container
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Core MCP Configuration
PYTHONPATH=/app/src
FASTMCP_LOG_LEVEL=INFO
FASTMCP_TRANSPORT=streamable-http
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8000

# 4-Tier Context System
CONTEXT_CACHE_TTL=3600
CONTEXT_INHERITANCE_ENABLED=true
CONTEXT_DELEGATION_ENABLED=true
CONTEXT_AUTO_CREATE=true

# Vision System Configuration
VISION_SYSTEM_ENABLED=true
VISION_PERFORMANCE_TARGET=5
VISION_CACHE_ENABLED=true
VISION_WORKFLOW_HINTS=true

# Redis Cache (Optional)
REDIS_URL=redis://redis:6379/0
CACHE_ENABLED=true

# Authentication
DHAFNCK_AUTH_ENABLED=true
AUTH_TOKEN_TTL=3600

# Development Settings
DEV_MODE=1
MCP_DEBUG=true
```

### Configuration Files

| File | Purpose | Location |
|------|---------|----------|
| `docker-compose.yml` | Main container configuration | `docker/docker-compose.yml` |
| `docker-compose.postgres.yml` | PostgreSQL container config | `docker/docker-compose.postgres.yml` |
| `docker-compose.redis.yml` | Redis container config | `docker/docker-compose.redis.yml` |
| `docker-compose.local.yml` | Local development overrides | `docker/docker-compose.local.yml` |
| `docker-compose.dev.yml` | Development-specific settings | `docker/docker-compose.dev.yml` |
| `docker-compose.prod.yml` | Production optimizations | `docker/docker-compose.prod.yml` |
| `Dockerfile` | MCP server build instructions | `docker/Dockerfile` |

### Customizing Configuration

1. **For local development**: Modify `docker-compose.local.yml`
2. **For production**: Use `docker-compose.prod.yml`
3. **Environment variables**: Create `.env` file in `docker/` directory

Example `.env` file:
```bash
# docker/.env
# PostgreSQL Configuration
POSTGRES_USER=dhafnck_user
POSTGRES_PASSWORD=secure_password
POSTGRES_DB=dhafnck_mcp
DATABASE_URL=postgresql://dhafnck_user:secure_password@postgres:5432/dhafnck_mcp

# Application Configuration
FASTMCP_LOG_LEVEL=INFO
VISION_SYSTEM_ENABLED=true
CONTEXT_AUTO_CREATE=true

# Redis Configuration (Optional)
REDIS_PASSWORD=redis_password

# Authentication
DHAFNCK_AUTH_ENABLED=true
AUTH_SECRET_KEY=your-secret-key
```

## 💾 Data Storage

The DhafnckMCP Docker system supports two data storage modes controlled by the `DATA_STORAGE_MODE` environment variable:

### Storage Modes

#### 1. Internal Storage (Default)
- **Mode**: `DATA_STORAGE_MODE=internal`
- **Description**: Data is stored inside the Docker container using named volumes
- **Use Case**: Simple deployment, container-managed data persistence
- **Persistence**: Data survives container restarts but not container removal
- **Backup**: Use `docker volume` commands to backup data

```bash
# Start with internal storage (default)
docker-compose -f docker-compose.yml up -d

# Or explicitly set internal mode
DATA_STORAGE_MODE=internal docker-compose -f docker-compose.yml up -d
```

#### 2. External Storage
- **Mode**: `DATA_STORAGE_MODE=external`
- **Description**: Data is stored in host directories mounted as volumes
- **Use Case**: Easy data access, backup, and sharing between containers
- **Persistence**: Data survives container removal and can be easily backed up
- **Location**: `./data` and `./logs` directories in the project

```bash
# Start with external storage
docker-compose -f docker-compose.external.yml up -d

# Or set environment variable
DATA_STORAGE_MODE=external docker-compose -f docker-compose.yml up -d
```

### Storage Comparison

| Feature | Internal Storage | External Storage |
|---------|------------------|------------------|
| **Setup Complexity** | Simple | Requires directory setup |
| **Data Access** | Docker commands only | Direct file system access |
| **Backup** | `docker volume` commands | Standard file backup |
| **Sharing** | Between containers only | Host and containers |
| **Performance** | Optimized | Depends on host filesystem |
| **Portability** | High | Medium (path dependent) |

### Setting Up External Storage

1. **Create host directories**:
   ```bash
   mkdir -p data/{tasks,projects,contexts,rules}
   mkdir -p logs
   chmod 777 data logs  # Ensure container can write
   ```

2. **Start with external storage**:
   ```bash
   docker-compose -f docker-compose.external.yml up -d
   ```

3. **Verify data location**:
   ```bash
   ls -la data/  # Should show task data
   ls -la logs/  # Should show application logs
   ```

### Switching Between Storage Modes

#### From Internal to External
```bash
# 1. Stop the container
docker-compose down

# 2. Export data from internal volumes
docker run --rm -v docker_dhafnck_data:/source -v $(pwd)/data:/dest alpine cp -r /source/. /dest/
docker run --rm -v docker_dhafnck_logs:/source -v $(pwd)/logs:/dest alpine cp -r /source/. /dest/

# 3. Start with external storage
docker-compose -f docker-compose.external.yml up -d
```

#### From External to Internal
```bash
# 1. Stop the container
docker-compose -f docker-compose.external.yml down

# 2. Start with internal storage (data will be imported automatically if volumes exist)
docker-compose -f docker-compose.yml up -d
```

### Data Directory Structure

With PostgreSQL, most data is stored in the database, but some files remain:

```
postgres-data/               # PostgreSQL database files
├── pg_data/                # Database cluster data
├── pg_wal/                 # Write-ahead logs
└── pg_stat/                # Statistics

app-data/
├── agent-library/          # 60+ agent YAML definitions
├── vision-cache/           # Vision System cache
├── temp/                   # Temporary files
└── uploads/                # User uploads

logs/
├── fastmcp.log            # Main application log
├── postgres.log           # PostgreSQL logs
├── vision.log             # Vision System logs
├── agent.log              # Agent execution logs
└── access.log             # HTTP access logs
```

### Environment Variables for Data Storage

```bash
# Database Storage
DATABASE_URL=postgresql://postgres:password@postgres:5432/dhafnck_mcp
POSTGRES_DATA=/var/lib/postgresql/data

# Application Data Paths
AGENT_LIBRARY_PATH=/app/agent-library
VISION_CACHE_PATH=/data/vision-cache
TEMP_PATH=/data/temp
UPLOAD_PATH=/data/uploads

# Log Paths
LOG_PATH=/app/logs
POSTGRES_LOG_PATH=/var/log/postgresql
```

## 🔧 Development Mode

### Features
- **Full Feature Set**: All 60+ agents and tools available
- **PostgreSQL with Sample Data**: Pre-populated database for testing
- **Live Logs**: Verbose logging for all components
- **Debug Ports**: Additional ports for database and debugging
- **Vision System Tracing**: Detailed Vision System performance metrics
- **Hot Reload**: Code changes reflected without restart (Python files)

### Switching Modes

```bash
# Use local development mode (default)
docker-compose -f docker-compose.yml -f docker-compose.local.yml up -d

# Use development mode with more debugging
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Use production mode
docker-compose -f docker-compose.yml up -d
```

### Development Workflow

1. **Start in development mode**:
   ```bash
   ./scripts/manage-docker.sh start
   ```

2. **Monitor logs during development**:
   ```bash
   ./scripts/manage-docker.sh logs
   ```

3. **Test changes**:
   ```bash
   # Restart after code changes
   ./scripts/manage-docker.sh restart
   ```

4. **Debug issues**:
   ```bash
   # Open shell in container
   ./scripts/manage-docker.sh shell
   
   # Check server status
   ./scripts/manage-docker.sh status
   ```

## 🐛 Troubleshooting

### Common Issues and Solutions

#### 1. Container Won't Start
```bash
# Check Docker is running
docker ps

# Check for port conflicts
netstat -tulpn | grep 8000

# View detailed error logs
./scripts/manage-docker.sh logs

# Clean up and restart
./scripts/manage-docker.sh cleanup
./scripts/manage-docker.sh start
```

#### 2. Volume Mount Errors
```bash
# Ensure data directories exist
mkdir -p docker/data/{tasks,projects,rules}

# Remove problematic volumes
docker volume rm docker_dhafnck_data docker_dhafnck_logs 2>/dev/null || true

# Restart with fresh volumes
./scripts/manage-docker.sh cleanup
./scripts/manage-docker.sh start
```

#### 3. Health Check Failures
```bash
# Check if port is accessible
nc -z localhost 8000

# Verify container is running
docker ps | grep dhafnck

# Check server logs for errors
./scripts/manage-docker.sh logs
```

#### 4. Permission Issues (Linux/WSL2)
```bash
# Fix directory permissions
sudo chown -R $USER:$USER docker/data docker/logs

# Or run with user override
docker-compose up -d --user $(id -u):$(id -g)
```

#### 5. WSL2 Specific Issues
```bash
# Restart Docker Desktop
# Or restart WSL2
wsl --shutdown
# Then restart Docker Desktop

# Check WSL2 integration
docker context ls
```

### Diagnostic Commands

```bash
# Full system status
./scripts/manage-docker.sh status

# Container inspection
docker inspect dhafnck-mcp-server

# Network inspection
docker network ls
docker network inspect docker_default

# Volume inspection
docker volume ls
docker volume inspect docker_dhafnck_data
```

### Log Analysis

```bash
# View recent logs
docker logs dhafnck-mcp-server --tail 50

# Search for specific errors
docker logs dhafnck-mcp-server 2>&1 | grep -i error

# Follow logs in real-time
./scripts/manage-docker.sh logs
```

## 🏛️ Architecture

### Multi-Container Architecture
```
DhafnckMCP Platform/
├── postgres/                # PostgreSQL Database Container
│   ├── Data Volume         # Persistent database storage
│   ├── Config              # PostgreSQL configuration
│   └── Port: 5432          # Database port
├── dhafnck-mcp-server/     # Main Application Container
│   ├── /app/src/           # DDD-structured source code
│   ├── /app/agent-library/ # 60+ agent definitions
│   ├── /data/              # Application data
│   └── Port: 8000          # MCP server port
└── redis/ (optional)        # Redis Cache Container
    ├── Data Volume         # Cache persistence
    └── Port: 6379          # Redis port
```

### Network Configuration
- **Network Name**: `dhafnck_network`
- **Network Type**: Bridge network with DNS
- **Service Discovery**: Container names as hostnames
- **Ports Exposed**:
  - `8000`: MCP Server (HTTP)
  - `5432`: PostgreSQL (mapped to 54320 on host)
  - `6379`: Redis (optional, mapped to 63790 on host)

### Volume Mapping
| Volume | Purpose | Container | Mount Point |
|--------|---------|-----------|-------------|
| `postgres_data` | Database files | postgres | `/var/lib/postgresql/data` |
| `dhafnck_data` | Application data | mcp-server | `/data` |
| `dhafnck_logs` | Application logs | mcp-server | `/app/logs` |
| `agent_library` | Agent definitions | mcp-server | `/app/agent-library` |
| `redis_data` | Cache data | redis | `/data` |

### Resource Allocation
#### PostgreSQL Container
- **Memory Limit**: 1GB
- **Memory Reservation**: 512MB
- **CPU Limit**: 1.0 cores
- **Shared Memory**: 256MB

#### MCP Server Container
- **Memory Limit**: 2GB
- **Memory Reservation**: 1GB
- **CPU Limit**: 2.0 cores
- **CPU Reservation**: 0.5 cores

#### Redis Container (Optional)
- **Memory Limit**: 512MB
- **Memory Reservation**: 256MB
- **CPU Limit**: 0.5 cores

## 🚀 Advanced Usage

### Custom Builds
```bash
# Build custom image
docker build -t dhafnck/mcp-server:custom -f docker/Dockerfile .

# Use custom image
docker-compose -f docker-compose.yml up -d
```

### Multiple Environments
```bash
# Production environment with all services
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml -f docker-compose.redis.yml -f docker-compose.prod.yml up -d

# Staging environment
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml -f docker-compose.staging.yml up -d

# Testing environment with test database
docker-compose -f docker-compose.yml -f docker-compose.postgres.yml -f docker-compose.test.yml up -d
```

### Scaling Strategies
```bash
# Horizontal scaling with multiple MCP servers
docker-compose up -d --scale dhafnck-mcp=3

# Database read replicas (PostgreSQL streaming replication)
docker-compose -f docker-compose.yml -f docker-compose.postgres-replica.yml up -d

# Redis cluster for distributed caching
docker-compose -f docker-compose.yml -f docker-compose.redis-cluster.yml up -d
```

### Backup and Restore

#### PostgreSQL Database Backup
```bash
# Backup PostgreSQL database
docker exec postgres pg_dump -U postgres dhafnck_mcp > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup with compression
docker exec postgres pg_dump -U postgres -Fc dhafnck_mcp > backup_$(date +%Y%m%d_%H%M%S).dump

# Restore PostgreSQL database
docker exec -i postgres psql -U postgres dhafnck_mcp < backup.sql

# Restore compressed backup
docker exec -i postgres pg_restore -U postgres -d dhafnck_mcp < backup.dump
```

#### Application Data Backup
```bash
# Backup all volumes
docker run --rm -v dhafnck_data:/data -v $(pwd):/backup alpine tar czf /backup/app-data-backup.tar.gz -C /data .

# Restore application data
docker run --rm -v dhafnck_data:/data -v $(pwd):/backup alpine tar xzf /backup/app-data-backup.tar.gz -C /data
```

### Monitoring
```bash
# Resource monitoring for all containers
docker stats dhafnck-mcp-server postgres redis

# Database monitoring
docker exec postgres psql -U postgres -d dhafnck_mcp -c "SELECT * FROM pg_stat_activity;"

# Health monitoring
watch -n 5 './scripts/manage-docker.sh health'

# Log monitoring
tail -f docker/logs/*.log

# Vision System performance monitoring
docker exec dhafnck-mcp-server tail -f /app/logs/vision.log | grep "performance"
```

## 📚 Additional Resources

### Related Documentation
- [Architecture Overview](../docs/architecture.md)
- [Domain-Driven Design](../docs/domain-driven-design.md)
- [Vision System Guide](../docs/vision/README.md)
- [API Reference](../docs/api-reference.md)
- [Database Setup](../DATABASE_SETUP.md)

### External Links
- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Reference](https://docs.docker.com/compose/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [MCP Protocol Specification](https://modelcontextprotocol.io/)

### Support
- **Issues**: Check container logs with `./scripts/manage-docker.sh logs`
- **Database**: Access PostgreSQL with `docker exec -it postgres psql -U postgres`
- **Debugging**: Use `./scripts/manage-docker.sh shell` for container access
- **Health**: Monitor with `./scripts/manage-docker.sh health`
- **Performance**: Check Vision System metrics in logs

---

**Last Updated**: 2025-01-31  
**Version**: 2.1.0  
**Platform**: DhafnckMCP Multi-Project AI Orchestration Platform
**Compatibility**: Docker 20.10+, Docker Compose v2.0+, PostgreSQL 14+ 


### quickstart

cd dhafnck_mcp_main

docker system prune -f && docker-compose -f docker/docker-compose.redis.yml down && docker-compose -f docker/docker-compose.redis.yml build --no-cache dhafnck-mcp && ./scripts/manage-docker.sh start

./scripts/manage-docker.sh start

docker exec -it dhafnck-mcp-server /bin/bash


docker logs dhafnck-mcp-server | tail -200


# Start the container (creates if doesn't exist)
./scripts/manage-docker.sh start

# Stop the running container
./scripts/manage-docker.sh stop

# Restart the container
./scripts/manage-docker.sh restart

# Show live logs (Ctrl+C to exit)
./scripts/manage-docker.sh logs

# Check container status and resource usage
./scripts/manage-docker.sh status

# Verify server health
./scripts/manage-docker.sh health

# Open shell inside container for debugging
./scripts/manage-docker.sh shell

# Remove container (preserves data volumes)
./scripts/manage-docker.sh remove

# Complete cleanup and rebuild
./scripts/manage-docker.sh cleanup

# Show help and available commands
./scripts/manage-docker.sh help