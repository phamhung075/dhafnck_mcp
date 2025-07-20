# Docker System Documentation

Welcome to the Docker System documentation. This system provides a comprehensive CLI interface for managing DhafnckMCP services with PostgreSQL-first architecture.

## =Ë Table of Contents

### =€ Getting Started
- [Docker CLI Guide](DOCKER_CLI_GUIDE.md) - Complete command reference and usage examples
- [Architecture Overview](ARCHITECTURE.md) - System design and component relationships

### >ê Development & Testing
- [Testing Guide](TESTING_GUIDE.md) - Test-driven development workflows and test execution
- [Changelog](changelog.md) - Recent updates, fixes, and improvements

## =' Quick Start

### Basic Commands
```bash
# Start all services
./docker-cli.sh start

# View service status and monitoring
./docker-cli.sh status
./docker-cli.sh monitor

# Access logs
./docker-cli.sh logs [service]

# Database operations
./docker-cli.sh db status
./docker-cli.sh db init
```

### Interactive Menu
```bash
# Launch interactive menu system
python3 docker-menu.py
```

## <× System Architecture

The Docker System consists of several key components:

- **Core Services**: Backend (MCP Server), Frontend, Redis, PostgreSQL
- **CLI Interface**: Unified command-line tool for all operations
- **Monitoring Dashboard**: Real-time system monitoring and metrics
- **Database Management**: PostgreSQL operations and migrations
- **Development Tools**: Testing, debugging, and development workflows

## =Ê Recent Updates

###  Latest Fixes (2025-07-20)
- **Monitoring Dashboard**: Fixed container name detection issues
  - Backend service now correctly shows as "Running"
  - Network status displays accurate container count
  - Logs access now works properly with correct container names
  - Added fallback network detection for different Docker configurations

### >ê Test-Driven Development
- Implemented comprehensive TDD workflow with 16 test cases
- Added mock Docker environment for isolated testing
- Established proper commit separation for tests vs implementation

## =Ö Documentation Structure

### Core Guides
- **[DOCKER_CLI_GUIDE.md](DOCKER_CLI_GUIDE.md)**: Complete CLI command reference
  - Service management (start, stop, restart)
  - Database operations (init, migrate, backup, restore)
  - Development commands (build, test, shell access)
  - Deployment and scaling operations
  - Troubleshooting and diagnostics

- **[ARCHITECTURE.md](ARCHITECTURE.md)**: System architecture and design
  - Component relationships and dependencies
  - Data flow and service interactions
  - Configuration and environment management
  - Security considerations

- **[TESTING_GUIDE.md](TESTING_GUIDE.md)**: Testing strategies and workflows
  - Test-driven development processes
  - Unit testing and integration testing
  - Mock environments and test isolation
  - Continuous integration guidelines

- **[changelog.md](changelog.md)**: Version history and updates
  - Recent bug fixes and improvements
  - New feature additions
  - Breaking changes and migration guides
  - Technical implementation details

## =à Common Workflows

### Development Setup
```bash
# Setup development environment
./docker-cli.sh workflow dev-setup

# Start with hot reload
./docker-cli.sh start

# Run tests
./docker-cli.sh test all
```

### Production Deployment
```bash
# Deploy to staging
./docker-cli.sh deploy staging

# Deploy to production
./docker-cli.sh deploy production

# Monitor system health
./docker-cli.sh health
./docker-cli.sh monitor
```

### Database Management
```bash
# Check database status
./docker-cli.sh db status

# Create backup
./docker-cli.sh backup create database

# Run migrations
./docker-cli.sh db migrate
```

### Troubleshooting
```bash
# Run system diagnostics
./docker-cli.sh diagnose

# Generate support bundle
./docker-cli.sh support-bundle

# Check service logs
./docker-cli.sh logs backend --tail 100
```

## = Monitoring & Observability

### Real-time Monitoring
The system includes a comprehensive monitoring dashboard accessible via:
```bash
./docker-cli.sh monitor
```

**Dashboard Features:**
-  Service status with health checks
- =Ê Resource usage (CPU, memory, network)
- =Ä Database metrics and connection monitoring
- =Ê Redis performance statistics
- =Ü Recent logs from all services
- =¾ Disk usage and storage monitoring
- < Network connectivity status

### Service Status Indicators
-  **Running**: Service is healthy and operational
- =á **Starting**: Service is initializing
- L **Unhealthy**: Service running but health checks failing
- « **Stopped**: Service not running

## =¨ Support & Troubleshooting

### Common Issues
1. **Service Status Shows "Stopped"**: Check container names and network configuration
2. **Database Connection Issues**: Verify PostgreSQL service status and credentials
3. **Port Conflicts**: Ensure required ports (8000, 3000, 5432, 6379) are available
4. **Permission Issues**: Run `./docker-cli.sh fix-permissions`

### Getting Help
- **Diagnostics**: `./docker-cli.sh diagnose`
- **Health Check**: `./docker-cli.sh health`
- **Support Bundle**: `./docker-cli.sh support-bundle`
- **Interactive Help**: `python3 docker-menu.py`

## =Ý Contributing

### Adding Documentation
1. Follow the established structure and format
2. Update this index when adding new documentation
3. Include practical examples and use cases
4. Test all code examples before committing

### Documentation Standards
- Use clear, actionable headings
- Include code examples with explanations
- Provide both quick reference and detailed guides
- Link related documentation sections
- Update changelog for significant changes

---

**Last Updated**: 2025-07-20  
**System Version**: Docker System v2.0 (PostgreSQL-First Architecture)  
**Documentation Status**:  Up to date with latest monitoring fixes