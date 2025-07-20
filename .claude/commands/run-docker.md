# DhafnckMCP Docker System Documentation

## 🚀 Quick Start

The new Docker system provides a unified CLI interface for managing the DhafnckMCP development environment with PostgreSQL as the primary database.

### First Time Setup
```bash
cd docker-system
./docker-cli.sh workflow dev-setup
```

This will:
- ✅ Check prerequisites (Docker, Docker Compose)
- ✅ Create necessary directories and configuration
- ✅ Start PostgreSQL, Redis, Backend, and Frontend services
- ✅ Initialize the database
- ✅ Seed development data (if enabled)

### Access Points
- **Backend API**: http://localhost:8000/health
- **Frontend**: http://localhost:3000
- **PostgreSQL**: `postgresql://dhafnck_user:dev_password@localhost:5432/dhafnck_mcp`
- **Redis**: `redis://localhost:6379`

## 📁 Project Structure

```
docker-system/
├── docker-cli.sh              # Main CLI entry point
├── docker-menu.sh             # Interactive bash menu
├── docker-menu.py             # Interactive Python menu (with rich UI)
├── docker/
│   ├── docker-compose.yml     # Base compose configuration
│   ├── docker-compose.dev.yml # Development overrides
│   ├── docker-compose.prod.yml # Production configuration
│   ├── frontend.Dockerfile    # Frontend production build
│   ├── frontend.dev.Dockerfile # Frontend development build
│   └── init-scripts/          # Database initialization scripts
├── environments/
│   ├── dev.env               # Development environment
│   ├── staging.env           # Staging environment
│   └── production.env        # Production environment
├── lib/                      # Modular command libraries
│   ├── common.sh             # Shared utilities
│   ├── core.sh               # Core Docker operations
│   ├── database/             # Database operations
│   │   ├── interface.sh      # Database factory pattern
│   │   └── postgresql.sh     # PostgreSQL implementation
│   ├── development.sh        # Development commands
│   ├── deployment.sh         # Deployment operations
│   ├── monitoring.sh         # Real-time monitoring
│   ├── maintenance.sh        # Backup and maintenance
│   ├── configuration.sh      # Config management
│   ├── troubleshooting.sh    # Diagnostics and fixes
│   └── workflows.sh          # Automated workflows
├── backups/                  # Database backups
├── logs/                     # Application logs
└── docs/                     # Additional documentation
```

## 🎯 Core Commands

### Service Management
```bash
# Start all services
./docker-cli.sh start

# Stop all services
./docker-cli.sh stop

# Restart services
./docker-cli.sh restart           # All services
./docker-cli.sh restart backend   # Specific service

# Check status
./docker-cli.sh status

# View logs
./docker-cli.sh logs backend      # Specific service
./docker-cli.sh logs backend -f   # Follow logs
./docker-cli.sh logs backend --tail 50  # Last 50 lines
```

### Database Operations
```bash
# Initialize database
./docker-cli.sh db init

# Test connection
./docker-cli.sh db test-connection

# Access PostgreSQL shell
./docker-cli.sh db shell

# Backup database
./docker-cli.sh db backup

# Restore from backup
./docker-cli.sh db restore backup_file.sql

# Reset database (WARNING: data loss)
./docker-cli.sh db reset
```

### Development Commands
```bash
# Setup development environment
./docker-cli.sh dev setup

# Reset development data
./docker-cli.sh dev reset

# Seed sample data
./docker-cli.sh dev seed

# Build services
./docker-cli.sh build          # All services
./docker-cli.sh build backend  # Specific service

# Run tests
./docker-cli.sh test all
./docker-cli.sh test unit
./docker-cli.sh test integration
```

### Monitoring
```bash
# Real-time monitoring dashboard
./docker-cli.sh monitor

# Single snapshot
./docker-cli.sh monitor-snapshot

# Health check
./docker-cli.sh health

# Diagnostics
./docker-cli.sh diagnose
```

### Interactive Menus
```bash
# Bash-based menu
./docker-menu.sh

# Python-based menu (with rich UI)
./docker-menu.py
```

## 🔧 Configuration

### Environment Variables
The system uses environment files in the `environments/` directory:
- `dev.env` - Development settings
- `staging.env` - Staging settings  
- `production.env` - Production settings

Key variables:
```bash
# Database
DATABASE_TYPE=postgresql
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=dhafnck_mcp
DATABASE_USER=dhafnck_user
DATABASE_PASSWORD=dev_password

# Application
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
SECRET_KEY=dev-secret-key-change-in-production
JWT_SECRET=dev-jwt-secret-change-in-production

# Features
HOT_RELOAD=true
AUTO_MIGRATE=true
SEED_DATA=true
```

### Loading Custom Environment
```bash
# Use specific environment
./docker-cli.sh --env staging start

# Or set default
export DEFAULT_ENV=staging
./docker-cli.sh start
```

## 🚀 Workflows

### Development Workflow
```bash
# 1. Start development environment
./docker-cli.sh workflow dev-setup

# 2. Make code changes
# - Backend changes: Hot reload is enabled
# - Frontend changes: Auto-refresh in browser

# 3. View logs while developing
./docker-cli.sh logs backend -f

# 4. Run tests
./docker-cli.sh test all

# 5. Stop when done
./docker-cli.sh stop
```

### Production Deployment
```bash
# Deploy to production
./docker-cli.sh workflow prod-deploy production latest

# This will:
# - Create pre-deployment backup
# - Run health checks
# - Pull new images
# - Run migrations
# - Deploy with rolling update
# - Verify deployment
# - Clean up old images
```

### Backup and Restore
```bash
# Create backup
./docker-cli.sh backup create full

# List backups
./docker-cli.sh backup list

# Restore from backup
./docker-cli.sh backup restore backup_20250720_1234.tar.gz

# Automated backup workflow
./docker-cli.sh workflow backup-restore
```

## 🛠️ Troubleshooting

### Common Issues

#### Services showing as unhealthy
```bash
# Run diagnostics
./docker-cli.sh diagnose

# Check specific service logs
./docker-cli.sh logs backend --tail 100

# Restart problematic service
./docker-cli.sh restart backend
```

#### Database connection issues
```bash
# Test connection
./docker-cli.sh db test-connection

# Check PostgreSQL logs
docker logs dhafnck-postgres --tail 50

# Reinitialize if needed
./docker-cli.sh db init
```

#### Port conflicts
```bash
# Check what's using a port
lsof -i :8000

# Use different ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=3001
```

#### Reset everything
```bash
# Soft reset (keeps data)
./docker-cli.sh restart

# Hard reset (loses data)
./docker-cli.sh dev reset

# Nuclear option
./docker-cli.sh stop
docker system prune -a --volumes
./docker-cli.sh workflow dev-setup
```

### Emergency Commands
```bash
# Fix permissions
./docker-cli.sh fix-permissions

# Create emergency backup
./docker-cli.sh emergency-backup

# Generate support bundle
./docker-cli.sh support-bundle
```

## 📊 Monitoring & Health

### Service Status
The monitoring dashboard shows:
- Service health status (✅ healthy, 🟡 starting, ❌ unhealthy)
- Resource usage (CPU, memory)
- Database metrics (connections, size, cache hit ratio)
- Redis metrics (operations/sec, memory)
- Recent logs
- Disk usage
- Network status

### Health Endpoints
- Backend: http://localhost:8000/health
- Frontend: http://localhost:3000

### Performance Monitoring
```bash
# Real-time stats
docker stats

# Database performance
./docker-cli.sh db shell
\> SELECT * FROM pg_stat_activity;
\> SELECT * FROM pg_stat_database;
```

## 🔒 Security Considerations

### Development Mode
- Default passwords are for development only
- CORS is permissive for local development
- Debug mode is enabled
- No SSL/TLS encryption

### Production Recommendations
1. Change all default passwords
2. Use environment-specific secrets
3. Enable SSL/TLS
4. Restrict CORS origins
5. Disable debug mode
6. Use proper firewall rules
7. Regular security updates

## 🎯 Best Practices

### Daily Development
1. Start services in the morning: `./docker-cli.sh start`
2. Monitor health: `./docker-cli.sh monitor-snapshot`
3. Check logs regularly: `./docker-cli.sh logs backend -f`
4. Stop services when done: `./docker-cli.sh stop`

### Before Commits
1. Run tests: `./docker-cli.sh test all`
2. Check linting: `./docker-cli.sh test lint`
3. Verify build: `./docker-cli.sh build`

### Weekly Maintenance
1. Create backup: `./docker-cli.sh backup create full`
2. Clean up Docker: `docker system prune`
3. Update dependencies
4. Review logs for errors

## 🚦 System Requirements

### Minimum
- Docker 20.10+
- Docker Compose 2.0+
- 4GB RAM
- 10GB disk space

### Recommended
- Docker 24.0+
- Docker Compose 2.20+
- 8GB RAM
- 20GB disk space
- SSD storage

## 📚 Additional Resources

### Architecture
- PostgreSQL as primary database
- Factory pattern for future database support
- Redis for caching and sessions
- MCP server for backend
- React for frontend
- Docker Compose for orchestration

### Future Enhancements
- Supabase integration for production
- Kubernetes deployment manifests
- CI/CD pipeline integration
- Automated testing in Docker
- Multi-environment support
- Database migration system

## 🎉 Success Metrics

Your development environment is ready when:
- ✅ All services show as "Running" in status
- ✅ Health checks pass for all services
- ✅ Database connection test succeeds
- ✅ Frontend loads at http://localhost:3000
- ✅ Backend responds at http://localhost:8000/health
- ✅ Logs show no critical errors

---

**Version**: 2.0.0  
**Last Updated**: 2025-07-20  
**System**: DhafnckMCP Docker Development Environment