# DhafnckMCP Multi-Project AI Orchestration Platform - Scripts Documentation

## 📋 Index

This directory contains various scripts for managing, deploying, and debugging the DhafnckMCP Multi-Project AI Orchestration Platform. Scripts support PostgreSQL database, 4-tier hierarchical context system, Vision System integration, and 60+ specialized AI agents. Below is an index of all available scripts organized by category:

### 🐳 Docker Management Scripts
- [dev-docker.sh](#dev-dockersh) - Development Docker orchestration with PostgreSQL and Redis
- [manage-docker.sh](#manage-dockersh) - Production multi-container management (PostgreSQL + MCP + Redis)
- [manage_container.sh](#manage_containersh) - Advanced container lifecycle with database management
- [docker-entrypoint.sh](#docker-entrypointsh) - Docker container initialization with Vision System
- [run-docker-local.sh](#run-docker-localsh) - Local development environment with full stack

### 🚀 Deployment Scripts
- [deploy-mvp.sh](#deploy-mvpsh) - Complete platform deployment with PostgreSQL and agents
- [deploy-frontend.sh](#deploy-frontendsh) - Frontend deployment with API integration
- [publish-docker.sh](#publish-dockersh) - Multi-architecture image publishing

### 🔧 MCP Server Management
- [run_mcp_server.sh](#run_mcp_serversh) - MCP server with PostgreSQL and context system
- [run_mcp_server_with_logging.sh](#run_mcp_server_with_loggingsh) - Enhanced logging with Vision System metrics
- [restart_mcp.sh](#restart_mcpsh) - Quick server restart with database health checks
- [wsl_mcp_bridge.sh](#wsl_mcp_bridgesh) - WSL bridge with PostgreSQL compatibility

### 🔍 Debugging & Diagnostics
- [diagnostic_connect.sh](#diagnostic_connectsh) - Comprehensive diagnostics including database and agents
- [diagnose_mcp_connection.sh](#diagnose_mcp_connectionsh) - Connection troubleshooting with context validation
- [check_cursor_logs.sh](#check_cursor_logssh) - Cursor IDE log analysis with Vision System errors
- [start_inspector.sh](#start_inspectorsh) - MCP Inspector with agent library integration

---

## 📖 Detailed Script Documentation

### dev-docker.sh
**Purpose**: Development Docker orchestration with PostgreSQL, Redis, and live code reloading

**Features**:
- Multi-container startup (PostgreSQL + MCP Server + Redis)
- Live code reloading for development
- Database migration and seeding
- Vision System debugging and metrics
- 4-tier context system testing
- Agent library hot-reloading
- Container health monitoring
- Interactive shell access with database tools

**Usage**:
```bash
./dev-docker.sh [COMMAND]

Commands:
  start     - Start all containers (PostgreSQL, MCP Server, Redis) with live reload
  stop      - Stop all development containers
  restart   - Restart all containers with database health check
  logs      - Show aggregated logs from all containers
  shell     - Open shell in MCP server container with database access
  db        - Open PostgreSQL shell for database management
  test      - Run comprehensive tests including database and agent tests
  status    - Show status of all containers and services
  migrate   - Run database migrations
  seed      - Seed database with sample data
  clean     - Clean up all containers, volumes, and database data
```

**Key Features**:
- Uses `docker-compose.yml`, `docker-compose.postgres.yml`, `docker-compose.dev.yml`
- Multi-container orchestration with service dependencies
- Live reload for Python code and agent configurations
- Database migration and seeding capabilities
- Vision System performance monitoring
- Agent library hot-reloading for development
- Comprehensive health checks for all services

---

### manage-docker.sh
**Purpose**: Production multi-container management for the complete DhafnckMCP platform

**Features**:
- Multi-service lifecycle management (PostgreSQL + MCP Server + Redis)
- Database health monitoring and backup automation
- Vision System performance tracking
- Agent registry health checks
- Log aggregation from all services
- Resource usage monitoring across containers
- Container cleanup with data preservation
- Production deployment orchestration

**Usage**:
```bash
./manage-docker.sh <command>

Commands:
  start     - Start all services (PostgreSQL, MCP Server, Redis)
  stop      - Stop all running containers gracefully
  restart   - Restart all services with health validation
  logs      - Show aggregated logs from all services (follow mode)
  status    - Show comprehensive status of all containers and services
  health    - Check health of database, MCP server, and Vision System
  backup    - Create database backup with timestamp
  restore   - Restore database from backup file
  shell     - Open shell inside MCP server container
  db-shell  - Open PostgreSQL shell for database operations
  remove    - Stop and remove all containers (preserves data volumes)
  cleanup   - Complete cleanup and rebuild with fresh database
```

**Key Features**:
- Multi-service orchestration with dependency management
- PostgreSQL backup and restore capabilities
- Vision System performance monitoring
- Agent health and registry validation
- Resource usage tracking across all containers
- Database volume preservation during maintenance

---

### diagnostic_connect.sh
**Purpose**: Comprehensive MCP server connection diagnostics and troubleshooting

**Features**:
- Complete environment validation
- Path and configuration verification
- Server startup testing
- Tool loading diagnostics
- WSL/Cursor/Claude Desktop compatibility checks
- Detailed error reporting and suggestions

**Usage**:
```bash
./diagnostic_connect.sh
```

**Diagnostic Areas**:
- Project structure validation
- Python environment checks
- Virtual environment verification
- Server import and startup testing
- Tool manager functionality
- MCP protocol compliance
- Configuration file validation

**Key Features**:
- Color-coded output for easy reading
- Comprehensive error reporting
- Automatic fix suggestions
- Environment-specific diagnostics

---

### deploy-mvp.sh
**Purpose**: Complete MVP deployment pipeline orchestration

**Features**:
- Pre-deployment validation
- Docker image building and testing
- Frontend deployment to Vercel
- Docker image publishing
- Documentation updates
- Deployment announcements

**Usage**:
```bash
./deploy-mvp.sh [production|preview] [skip_tests]

# Examples:
./deploy-mvp.sh preview          # Preview deployment
./deploy-mvp.sh production       # Production deployment
./deploy-mvp.sh preview true     # Skip tests in preview
```

**Deployment Steps**:
1. Pre-deployment validation
2. Docker image build and test
3. Frontend deployment
4. Docker image publishing
5. Documentation updates
6. Launch announcement

**Key Features**:
- Environment-specific deployments
- Comprehensive validation
- Rollback capabilities
- Deployment logging and tracking

---

### run_mcp_server.sh
**Purpose**: Basic MCP server startup with proper environment configuration

**Features**:
- Environment variable setup
- Python path configuration
- Server startup with proper context

**Usage**:
```bash
./run_mcp_server.sh
```

**Environment Variables Set**:
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_MODE`: Database mode (local, container, mcp_stdin, test)
- `PYTHONPATH`: Python module search path
- `CONTEXT_CACHE_TTL`: 4-tier context system cache settings
- `VISION_SYSTEM_ENABLED`: Vision System activation
- `AGENT_LIBRARY_PATH`: 60+ agent definitions directory
- `REDIS_URL`: Redis cache connection (optional)
- Various PostgreSQL and performance-related settings

**Key Features**:
- Proper working directory setup
- Complete environment configuration
- Compatible with MCP Inspector

---

### check_cursor_logs.sh
**Purpose**: Cursor IDE log analysis for MCP connection troubleshooting

**Features**:
- Cursor log directory detection
- MCP-specific error searching
- Recent log file analysis
- Error pattern recognition
- Troubleshooting suggestions

**Usage**:
```bash
./check_cursor_logs.sh
```

**Search Patterns**:
- dhafnck_mcp specific errors
- General MCP connection issues
- Server startup failures
- Renderer process errors

**Key Features**:
- Cross-platform log directory detection
- Pattern-based error identification
- Contextual error reporting
- Troubleshooting recommendations

---

### diagnose_mcp_connection.sh
**Purpose**: Quick MCP connection troubleshooting and validation

**Features**:
- Connection status checking
- Configuration validation
- Server responsiveness testing
- Common issue identification

**Usage**:
```bash
./diagnose_mcp_connection.sh
```

**Key Features**:
- Quick diagnostic checks
- Configuration file validation
- Server health verification
- Common fix suggestions

---

### manage_container.sh
**Purpose**: Advanced container lifecycle management with monitoring

**Features**:
- Container creation and management
- Health monitoring
- Log aggregation
- Performance monitoring
- Cleanup and maintenance

**Usage**:
```bash
./manage_container.sh [command]
```

**Key Features**:
- Advanced container operations
- Health and performance monitoring
- Automated maintenance tasks
- Comprehensive logging

---

### docker-entrypoint.sh
**Purpose**: Docker container initialization and startup orchestration

**Features**:
- Container environment setup
- Service initialization
- Health check implementation
- Graceful shutdown handling

**Usage**: 
Automatically executed when Docker container starts

**Key Features**:
- Environment validation
- Service startup orchestration
- Health monitoring
- Signal handling for graceful shutdown

---

### run-docker-local.sh
**Purpose**: Local Docker development environment setup

**Features**:
- Local development container setup
- Volume mounting for development
- Port mapping configuration
- Development-specific optimizations

**Usage**:
```bash
./run-docker-local.sh
```

**Key Features**:
- Development-optimized configuration
- Live code reloading
- Debug port exposure
- Local volume mounting

---

### deploy-frontend.sh
**Purpose**: Frontend deployment to Vercel platform

**Features**:
- Vercel deployment automation
- Environment configuration
- Build optimization
- Deployment verification

**Usage**:
```bash
./deploy-frontend.sh [--production]
```

**Key Features**:
- Automated Vercel deployment
- Environment-specific configurations
- Build optimization
- Deployment status verification

---

### publish-docker.sh
**Purpose**: Docker image publishing to container registry

**Features**:
- Image building and tagging
- Registry authentication
- Multi-platform support
- Version management

**Usage**:
```bash
./publish-docker.sh
```

**Key Features**:
- Automated image publishing
- Version tagging
- Registry management
- Multi-platform builds

---

### run_mcp_server_with_logging.sh
**Purpose**: MCP server startup with enhanced logging and debugging

**Features**:
- Enhanced logging configuration
- Debug output capture
- Log file management
- Error tracking

**Usage**:
```bash
./run_mcp_server_with_logging.sh
```

**Key Features**:
- Comprehensive logging
- Debug information capture
- Log rotation and management
- Error tracking and reporting

---

### restart_mcp.sh
**Purpose**: Quick MCP server restart utility

**Features**:
- Fast server restart
- Process cleanup
- Environment reset
- Status verification

**Usage**:
```bash
./restart_mcp.sh
```

**Key Features**:
- Quick restart capability
- Process management
- Environment cleanup
- Status verification

---

### wsl_mcp_bridge.sh
**Purpose**: WSL-specific MCP server bridge and compatibility layer

**Features**:
- WSL environment detection
- Path translation
- Network bridge setup
- Compatibility fixes

**Usage**:
```bash
./wsl_mcp_bridge.sh
```

**Key Features**:
- WSL-specific optimizations
- Path and network handling
- Compatibility layer
- Environment adaptation

---

### start_inspector.sh
**Purpose**: MCP Inspector startup for debugging and development

**Features**:
- MCP Inspector initialization
- Debug interface setup
- Tool inspection capabilities
- Development debugging

**Usage**:
```bash
./start_inspector.sh
```

**Key Features**:
- Interactive debugging interface
- Tool inspection and testing
- Development utilities
- Real-time monitoring

---

## 🛠️ Common Usage Patterns

### Development Workflow
1. Start development environment: `./dev-docker.sh start`
2. Monitor logs: `./dev-docker.sh logs -f`
3. Run tests: `./dev-docker.sh test`
4. Debug issues: `./diagnostic_connect.sh`

### Production Deployment
1. Deploy MVP: `./deploy-mvp.sh production`
2. Monitor container: `./manage-docker.sh status`
3. Check health: `./manage-docker.sh health`
4. View logs: `./manage-docker.sh logs`

### Troubleshooting
1. Check connections: `./diagnose_mcp_connection.sh`
2. Analyze Cursor logs: `./check_cursor_logs.sh`
3. Full diagnostics: `./diagnostic_connect.sh`
4. Restart services: `./restart_mcp.sh`

---

## 📋 Prerequisites

### System Requirements
- Docker and Docker Compose (v2.0+)
- PostgreSQL 14+ (for local development)
- Python 3.12+ (for direct server execution)
- Node.js 18+ (for frontend deployment)
- Redis 7+ (optional, for caching)
- WSL2 (for Windows users)

### Environment Setup
- Virtual environment: `dhafnck_mcp_main/.venv`
- Project root: `/home/daihungpham/agentic-project`
- Database: PostgreSQL with JSONB support
- Agent library: 60+ specialized agents in YAML format
- Configuration files in `.cursor/` and `docker/` directories

### Required Permissions
- All scripts should be executable: `chmod +x *.sh`
- Docker access for container management
- Network access for deployments

---

## 🔧 Configuration

### Environment Variables
Key environment variables used across scripts:
- `DATABASE_URL`: PostgreSQL connection string
- `DATABASE_MODE`: Database operation mode
- `PYTHONPATH`: Python module search path
- `CONTEXT_CACHE_TTL`: 4-tier context system settings
- `VISION_SYSTEM_ENABLED`: Vision System control
- `AGENT_LIBRARY_PATH`: 60+ agent definitions path
- `REDIS_URL`: Redis cache connection
- `PERFORMANCE_TARGET_RPS`: Performance targets

### Configuration Files
- `.cursor/mcp.json`: MCP server configuration with PostgreSQL
- `docker-compose.yml`: Main service definitions
- `docker-compose.postgres.yml`: PostgreSQL service configuration
- `docker-compose.redis.yml`: Redis service configuration
- `pyproject.toml`: Python project configuration
- `docker/.env`: Environment variables for containers
- `frontend/.env.local`: Frontend environment variables

---

## 🚨 Troubleshooting

### Common Issues
1. **Container won't start**: Check Docker service, PostgreSQL availability, and permissions
2. **Database connection failed**: Verify PostgreSQL is running and credentials are correct
3. **MCP connection failed**: Run diagnostic scripts to check database and agent health
4. **Port conflicts**: Check for services on ports 8000 (MCP), 5432 (PostgreSQL), 6379 (Redis)
5. **Vision System errors**: Check agent library path and permissions
6. **Context system failures**: Verify database schema and migrations
7. **Permission denied**: Ensure scripts are executable and database access is configured

### Debug Commands
```bash
# Check all service status
./manage-docker.sh status

# Test database connection
./manage-docker.sh db-shell

# View detailed diagnostics including database and agents
./diagnostic_connect.sh

# Check Cursor logs for Vision System errors
./check_cursor_logs.sh

# Test server startup with enhanced logging
./run_mcp_server_with_logging.sh

# Check database health
./manage-docker.sh health
```

---

## 📚 Additional Resources

### Related Documentation
- [Architecture Overview](../docs/architecture.md)
- [Vision System Guide](../docs/vision/README.md)
- [API Reference](../docs/api-reference.md)
- [Docker Deployment](../docs/docker-deployment.md)
- [Database Setup](../DATABASE_SETUP.md)
- [MCP Protocol Documentation](https://modelcontextprotocol.io/)
- [Docker Documentation](https://docs.docker.com/)
- [PostgreSQL Documentation](https://www.postgresql.org/docs/)
- [Cursor IDE Documentation](https://cursor.sh/)

### Support
For issues and questions:
1. Check the diagnostic scripts output for comprehensive analysis
2. Review the troubleshooting section for common solutions
3. Examine database and application logs for specific errors
4. Test individual components (database, agents, Vision System)
5. Consult the complete project documentation
6. Check agent library and context system health

---

*Last updated: 2025-01-31*
*Version: 2.1.0*
*Platform: DhafnckMCP Multi-Project AI Orchestration Platform*
*Maintainer: DhafnckMCP Team* 