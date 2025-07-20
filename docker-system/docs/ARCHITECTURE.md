# Docker CLI System Architecture

## Overview

The Docker CLI System is built with a modular, test-driven architecture that prioritizes maintainability, extensibility, and reliability. This document details the system's design principles, component interactions, and architectural decisions.

## Design Principles

### 1. Modular Architecture
- **Single Responsibility**: Each module handles one domain (database, monitoring, etc.)
- **Loose Coupling**: Modules communicate through well-defined interfaces
- **High Cohesion**: Related functionality is grouped together
- **Dependency Injection**: Components receive dependencies rather than creating them

### 2. Test-Driven Development (TDD)
- **Test First**: All features developed with tests written first
- **Mock Infrastructure**: Comprehensive mocking for external dependencies
- **Isolation**: Tests run independently without side effects
- **Coverage**: Aim for >90% test coverage

### 3. PostgreSQL-First Design
- **Optimized for PostgreSQL**: No compromises for other databases
- **Factory Pattern**: Extensible for future database support
- **Connection Pooling**: Efficient resource management
- **Migration System**: Version-controlled schema changes

### 4. Environment Isolation
- **Clear Boundaries**: Dev, staging, and production are isolated
- **Configuration as Code**: All settings in version control
- **No Hardcoding**: Everything configurable via environment
- **Secrets Management**: Secure handling of sensitive data

## System Components

### Core Components

```
┌─────────────────────────────────────────────────────────────┐
│                         CLI Interface                        │
│                      (docker-cli.sh)                        │
└─────────────────┬───────────────────────────┬──────────────┘
                  │                           │
                  ▼                           ▼
┌─────────────────────────────┐ ┌────────────────────────────┐
│        Command Router       │ │      Alternative UIs        │
│   (Pattern matching and     │ │  (docker-menu.sh/py)       │
│    module loading)          │ └────────────────────────────┘
└─────────────────┬───────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                        Module Layer                          │
├─────────────┬──────────────┬──────────────┬────────────────┤
│   Core      │   Database   │ Development  │   Monitoring   │
│   Module    │   Module     │   Module     │    Module      │
├─────────────┼──────────────┼──────────────┼────────────────┤
│ Maintenance │ Deployment   │Configuration │Troubleshooting │
│   Module    │   Module     │   Module     │    Module      │
├─────────────┴──────────────┴──────────────┴────────────────┤
│                     Workflows Module                         │
│              (Orchestrates multi-module operations)          │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                      Common Library                          │
│         (Shared utilities, helpers, and constants)           │
└─────────────────────────────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────────┐
│                    Docker Abstraction                        │
│              (Docker and Docker Compose APIs)                │
└─────────────────────────────────────────────────────────────┘
```

### Module Descriptions

#### Core Module (`lib/core.sh`)
Handles fundamental Docker operations:
- **start_command**: Orchestrates service startup
- **stop_command**: Graceful shutdown procedures
- **restart_command**: Service-specific or full restart
- **status_command**: Comprehensive status reporting
- **logs_command**: Log viewing with filtering
- **shell_command**: Container shell access

#### Database Module (`lib/database/`)
Manages all database operations:
- **Interface** (`interface.sh`): Routes commands to implementations
- **PostgreSQL** (`postgresql.sh`): PostgreSQL-specific operations
- Operations: init, migrate, backup, restore, status, shell

#### Development Module (`lib/development.sh`)
Development environment management:
- **dev_command**: Development environment operations
- **build_command**: Service building with caching
- **test_command**: Test execution framework
- Features: Hot reload, seeding, dependency management

#### Monitoring Module (`lib/monitoring.sh`)
System health and performance:
- **health_command**: Comprehensive health checks
- **monitor_command**: Real-time monitoring dashboard
- **monitor_snapshot_command**: Point-in-time metrics
- Metrics: CPU, memory, disk, network, service health

#### Workflows Module (`lib/workflows.sh`)
Orchestrates complex multi-step operations:
- **dev-setup**: Complete development environment setup
- **prod-deploy**: Production deployment workflow
- **backup-restore**: Backup and recovery procedures
- **health-check**: Full system health validation

### Common Library (`lib/common.sh`)

Provides shared functionality:

```bash
# Logging Functions
info()      # Information messages
success()   # Success confirmations
warning()   # Warning notifications
error()     # Error reporting

# Docker Helpers
check_docker()          # Verify Docker daemon
check_docker_compose()  # Verify Docker Compose
wait_for_services()     # Service readiness
get_container_id()      # Container lookup

# Environment Management
load_environment()      # Load env files
is_production()         # Environment checks
is_development()        # Development mode

# Utility Functions
compose_file_args()     # Build compose arguments
validate_service_name() # Service validation
ensure_network()        # Network management
measure_time()          # Performance tracking
```

## Service Architecture

### Container Structure

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Host System                       │
├─────────────────────────────────────────────────────────────┤
│                    Docker Daemon & Engine                    │
├─────────────────────────────────────────────────────────────┤
│                       Network Layer                          │
│                    (dhafnck-network)                        │
├──────────────┬──────────────┬──────────────┬───────────────┤
│   Frontend   │   Backend    │  PostgreSQL  │     Redis     │
│  Container   │  Container   │  Container   │   Container   │
│              │              │              │               │
│ nginx:alpine │ FastAPI/MCP │ postgres:15  │ redis:alpine  │
│              │              │              │               │
│   Port 3000  │  Port 8000   │  Port 5432   │   Port 6379   │
│              │              │              │               │
│   Volumes:   │   Volumes:   │   Volumes:   │   Volumes:    │
│  - static    │  - app code  │  - data      │  - data       │
│  - config    │  - logs      │  - config    │  - config     │
└──────────────┴──────────────┴──────────────┴───────────────┘
```

### Network Architecture

```
External Network (Host)
        │
        ▼
┌───────────────┐
│   Port 3000   │ ─── Frontend (nginx)
├───────────────┤
│   Port 8000   │ ─── Backend API
├───────────────┤
│   Port 5432   │ ─── PostgreSQL (dev only)
├───────────────┤
│   Port 6379   │ ─── Redis (dev only)
└───────────────┘
        │
        ▼
Internal Network (dhafnck-network)
        │
┌───────┴────────┬────────────┬────────────┐
│                │            │            │
▼                ▼            ▼            ▼
Frontend ──────> Backend ──> PostgreSQL   Redis
(React)          (API)       (Database)   (Cache)
```

### Data Flow

```
User Request Flow:
====================
User ──> Frontend ──> Backend ──> Database
 ▲          │            │           │
 │          │            │           ▼
 └──────────┴────────────┴─────── Response

Cache Flow:
====================
Backend ──> Redis (Check) ──> Hit ──> Return
   │           │                        ▲
   │           └──> Miss ──> Database ──┘
   │                            │
   └────────────────────────────┘

Monitoring Flow:
====================
All Services ──> Metrics Collection ──> Monitoring Dashboard
                      │
                      └──> Alerts ──> Notifications
```

## Configuration Management

### Environment Hierarchy

```
Base Configuration (docker-compose.yml)
         │
         ├─── Development Override (docker-compose.dev.yml)
         │           │
         │           └─── dev.env
         │
         ├─── Staging Override (docker-compose.staging.yml)
         │           │
         │           └─── staging.env
         │
         └─── Production Override (docker-compose.prod.yml)
                     │
                     └─── production.env
```

### Configuration Loading

```bash
# 1. Command Line Environment
ENV=production ./docker-cli.sh start

# 2. Shell Environment
export ENV=staging
./docker-cli.sh start

# 3. Default Environment
# Falls back to 'dev' if not specified

# 4. Environment File Loading
load_environment() {
    source environments/${ENV}.env
}
```

## Error Handling Architecture

### Error Propagation

```
User Command
    │
    ▼
Command Router ──> Module Function ──> Docker Operation
    │                   │                    │
    │                   │                    ▼
    │                   │              Error Occurs
    │                   │                    │
    │                   ▼                    │
    │            Handle Error <──────────────┘
    │                   │
    │                   ▼
    └──────── Display Error to User
                        │
                        ▼
                 Suggest Resolution
```

### Error Categories

1. **System Errors**
   - Docker daemon not running
   - Insufficient permissions
   - Network failures
   - Resource exhaustion

2. **Configuration Errors**
   - Missing environment files
   - Invalid settings
   - Port conflicts
   - Volume mount issues

3. **Application Errors**
   - Service startup failures
   - Database connection issues
   - Migration failures
   - Test failures

4. **User Errors**
   - Invalid commands
   - Missing parameters
   - Incorrect service names
   - Permission denied

## Testing Architecture

### Test Infrastructure

```
Test Framework (test_framework.sh)
         │
         ├─── Mock Infrastructure
         │     ├─── Mock Docker
         │     ├─── Mock Docker Compose
         │     └─── Mock File System
         │
         ├─── Assertion Library
         │     ├─── Value Assertions
         │     ├─── String Assertions
         │     └─── File Assertions
         │
         └─── Test Runner
               ├─── Test Discovery
               ├─── Test Execution
               └─── Result Reporting
```

### Test Execution Flow

```
1. Initialize Test Environment
   - Create mock directory
   - Set test mode flag
   - Load test framework

2. Run Test Suites
   - Discover test functions
   - Execute each test
   - Track results

3. Mock Command Execution
   - Intercept Docker calls
   - Return mock responses
   - Log command history

4. Assert Results
   - Verify exit codes
   - Check output content
   - Validate side effects

5. Cleanup
   - Remove mock files
   - Reset environment
   - Report summary
```

## Security Architecture

### Security Layers

```
┌─────────────────────────────────────────────┐
│          User Authentication                │
│     (Application level - not in CLI)        │
├─────────────────────────────────────────────┤
│         Environment Isolation               │
│    (Separate configs per environment)       │
├─────────────────────────────────────────────┤
│          Secret Management                  │
│    (Environment variables, not in code)     │
├─────────────────────────────────────────────┤
│         Network Isolation                   │
│    (Internal network for services)          │
├─────────────────────────────────────────────┤
│          Volume Permissions                 │
│    (Restricted access to volumes)           │
├─────────────────────────────────────────────┤
│         Process Isolation                   │
│    (Container boundaries)                   │
└─────────────────────────────────────────────┘
```

### Security Best Practices

1. **Secrets Management**
   - Never hardcode passwords
   - Use environment variables
   - Rotate credentials regularly
   - Different passwords per environment

2. **Network Security**
   - Internal service communication only
   - Expose minimal ports
   - Use HTTPS in production
   - Implement firewall rules

3. **Access Control**
   - Principle of least privilege
   - Service-specific database users
   - Read-only access where possible
   - Audit logging

## Performance Considerations

### Optimization Strategies

1. **Image Optimization**
   - Multi-stage builds
   - Minimal base images
   - Layer caching
   - Dependency optimization

2. **Resource Management**
   - CPU limits per service
   - Memory constraints
   - Disk quota management
   - Connection pooling

3. **Caching Strategy**
   - Redis for session data
   - Build cache optimization
   - Query result caching
   - Static asset caching

### Performance Monitoring

```
Metrics Collection Points:
========================
Application ──> Response Time ──> Monitoring
    │               │
    ├──> CPU Usage  │
    │               │
    ├──> Memory     │
    │               │
    ├──> Disk I/O   │
    │               │
    └──> Network ───┘
```

## Extensibility

### Adding New Modules

1. Create module file in `lib/`
2. Define command functions
3. Add routing in `docker-cli.sh`
4. Write comprehensive tests
5. Update documentation

### Adding New Services

1. Define in `docker-compose.yml`
2. Create Dockerfile if needed
3. Add to service validation
4. Update health checks
5. Add to monitoring

### Database Factory Pattern

```bash
# Current Implementation
database/
├── interface.sh      # Command router
└── postgresql.sh     # PostgreSQL implementation

# Future Extension
database/
├── interface.sh      # Command router
├── postgresql.sh     # PostgreSQL implementation
├── mysql.sh         # MySQL implementation
└── mongodb.sh       # MongoDB implementation
```

## Deployment Architecture

### Development Deployment

```
Local Machine
    │
    ├─── Source Code
    ├─── Docker Desktop
    └─── Services
         ├─── Frontend (hot reload)
         ├─── Backend (hot reload)
         ├─── PostgreSQL (persistent)
         └─── Redis (ephemeral)
```

### Production Deployment

```
Production Server
    │
    ├─── Git Repository
    ├─── Docker Engine
    ├─── Reverse Proxy (nginx/traefik)
    └─── Services
         ├─── Frontend (scaled)
         ├─── Backend (scaled)
         ├─── PostgreSQL (managed/RDS)
         └─── Redis (managed/ElastiCache)
```

## Maintenance Procedures

### Backup Architecture

```
Backup Types:
============
1. Database Backup
   - Full SQL dump
   - Compressed with gzip
   - Timestamped naming
   - Automated rotation

2. Volume Backup
   - Docker volume export
   - File system snapshot
   - Configuration backup

3. Full System Backup
   - All databases
   - All volumes
   - All configurations
   - Deployment scripts
```

### Update Procedures

```
Update Flow:
===========
1. Check for Updates
   - Git pull latest
   - Review changes
   - Check compatibility

2. Prepare Update
   - Create backup
   - Notify users
   - Schedule window

3. Execute Update
   - Stop services
   - Update code
   - Build images
   - Run migrations

4. Verify Update
   - Start services
   - Run health checks
   - Test functionality
   - Monitor logs
```

## Future Enhancements

### Planned Features

1. **Kubernetes Support**
   - Helm charts
   - K8s manifests
   - Operator pattern

2. **Multi-Database Support**
   - MySQL adapter
   - MongoDB adapter
   - Database routing

3. **Advanced Monitoring**
   - Prometheus metrics
   - Grafana dashboards
   - Alert manager

4. **CI/CD Integration**
   - GitHub Actions
   - GitLab CI
   - Jenkins pipelines

### Architecture Evolution

```
Current: Monolithic CLI
        │
        ▼
Phase 1: Microservices
        │
        ▼
Phase 2: Kubernetes Native
        │
        ▼
Phase 3: Cloud Native (Serverless)
```

---

*This architecture document is a living document and will be updated as the system evolves.*