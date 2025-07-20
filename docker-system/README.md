# DhafnckMCP Docker CLI System

A comprehensive, PostgreSQL-first Docker orchestration system for the DhafnckMCP platform.

## 🚀 Quick Start

```bash
# Make the CLI executable
chmod +x docker-cli.sh

# Setup development environment
./docker-cli.sh workflow dev-setup

# Start all services
./docker-cli.sh start

# Check status
./docker-cli.sh status
```

## 📋 Features

- **Unified CLI**: All 24 operations accessible via command line
- **PostgreSQL-First**: Primary database with factory pattern for future extensibility
- **Hot Reload**: Development mode with automatic code reloading
- **Comprehensive Monitoring**: Real-time health checks and resource monitoring
- **Automated Backups**: Full system backup and restore capabilities
- **Production Ready**: Security hardening, SSL/TLS support, and scaling
- **Workflow Automation**: Pre-configured workflows for common tasks

## 🏗️ Architecture

```
docker-system/
├── docker-cli.sh           # Main entry point
├── lib/                    # Modular command libraries
│   ├── common.sh          # Shared utilities
│   ├── core.sh            # Core Docker operations
│   ├── database/          # Database abstraction layer
│   │   ├── interface.sh   # Factory pattern interface
│   │   └── postgresql.sh  # PostgreSQL implementation
│   ├── development.sh     # Development commands
│   ├── deployment.sh      # Deployment and scaling
│   ├── monitoring.sh      # Real-time monitoring
│   ├── health.sh         # Health checks
│   ├── backup.sh         # Backup/restore operations
│   ├── maintenance.sh    # System maintenance
│   ├── configuration.sh  # Config management
│   ├── troubleshooting.sh # Diagnostics
│   └── workflows.sh      # Automated workflows
├── environments/         # Environment configurations
│   ├── dev.env          # Development settings
│   ├── staging.env      # Staging settings
│   └── production.env   # Production settings
├── docker/              # Docker configurations
│   ├── docker-compose.yml     # Base configuration
│   ├── docker-compose.dev.yml # Development overrides
│   └── docker-compose.prod.yml # Production overrides
└── test/               # Testing framework
```

## 📚 Command Reference

### Core Commands
```bash
./docker-cli.sh start              # Start all services
./docker-cli.sh stop               # Stop all services
./docker-cli.sh restart            # Restart all services
./docker-cli.sh status             # Show service status
./docker-cli.sh logs [service]     # View service logs
./docker-cli.sh shell [service]    # Access service shell
```

### Database Commands
```bash
./docker-cli.sh db status          # Show database status
./docker-cli.sh db init            # Initialize database
./docker-cli.sh db migrate         # Run migrations
./docker-cli.sh db backup          # Create database backup
./docker-cli.sh db restore [file]  # Restore from backup
./docker-cli.sh db shell           # Access database shell
./docker-cli.sh db reset           # Reset database (WARNING)
```

### Development Commands
```bash
./docker-cli.sh dev setup          # Setup development environment
./docker-cli.sh dev reset          # Reset development data
./docker-cli.sh dev seed           # Seed development data
./docker-cli.sh build [service]    # Build service images
./docker-cli.sh test [type]        # Run tests
```

### Deployment Commands
```bash
./docker-cli.sh deploy [env]       # Deploy to environment
./docker-cli.sh scale [service] N  # Scale service replicas
./docker-cli.sh health             # System health check
./docker-cli.sh monitor            # Real-time monitoring
```

### Maintenance Commands
```bash
./docker-cli.sh backup create      # Create full backup
./docker-cli.sh backup restore     # Restore from backup
./docker-cli.sh backup list        # List backups
./docker-cli.sh cleanup            # Clean unused resources
./docker-cli.sh update             # Update system
```

### Configuration Commands
```bash
./docker-cli.sh config show        # Show configuration
./docker-cli.sh config set K V     # Set config value
./docker-cli.sh config validate    # Validate config
./docker-cli.sh env [environment]  # Switch environment
```

### Troubleshooting Commands
```bash
./docker-cli.sh diagnose           # Run diagnostics
./docker-cli.sh fix-permissions    # Fix permissions
./docker-cli.sh emergency-backup   # Emergency backup
./docker-cli.sh support-bundle     # Generate support bundle
```

### Workflow Commands
```bash
./docker-cli.sh workflow dev-setup      # Complete dev setup
./docker-cli.sh workflow prod-deploy    # Production deployment
./docker-cli.sh workflow backup-restore # Backup/restore workflow
./docker-cli.sh workflow health-check   # Comprehensive health check
```

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the project root:

```bash
# Database Configuration
DATABASE_TYPE=postgresql
DATABASE_HOST=postgres
DATABASE_PORT=5432
DATABASE_NAME=dhafnck_mcp
DATABASE_USER=dhafnck_user
DATABASE_PASSWORD=your_secure_password

# Application Configuration
BACKEND_URL=http://localhost:8000
FRONTEND_URL=http://localhost:3000
SECRET_KEY=your_secret_key
JWT_SECRET=your_jwt_secret

# Redis Configuration
REDIS_URL=redis://redis:6379/0
```

### Switching Environments

```bash
# Show current environment
./docker-cli.sh env

# Switch to production
./docker-cli.sh env production
```

## 🐳 Docker Compose Override

The system uses Docker Compose with environment-specific overrides:

- Base: `docker/docker-compose.yml`
- Development: `docker/docker-compose.dev.yml`
- Production: `docker/docker-compose.prod.yml`

## 🔒 Security

### Production Deployment

1. Generate secure secrets:
```bash
./docker-cli.sh workflow prod-deploy
```

2. Configure SSL certificates in `nginx/ssl/`

3. Set up firewall rules for ports 80, 443

4. Enable Docker Content Trust:
```bash
export DOCKER_CONTENT_TRUST=1
```

## 🧪 Testing

Run the comprehensive test suite:

```bash
# Run all tests
./docker-cli.sh test all

# Run specific test type
./docker-cli.sh test unit
./docker-cli.sh test integration
./docker-cli.sh test e2e
./docker-cli.sh test performance
```

## 📊 Monitoring

Real-time monitoring dashboard:

```bash
# Start monitoring dashboard
./docker-cli.sh monitor

# One-time health check
./docker-cli.sh health
```

## 🔄 Backup & Restore

### Creating Backups

```bash
# Full backup (database + volumes + configs)
./docker-cli.sh backup create full

# Database only
./docker-cli.sh backup create database

# List backups
./docker-cli.sh backup list
```

### Restoring from Backup

```bash
# Restore from specific backup
./docker-cli.sh backup restore backups/backup-20240120.tar.gz

# Restore latest backup
./docker-cli.sh backup restore latest
```

## 🚨 Troubleshooting

### Common Issues

1. **Services won't start**
```bash
./docker-cli.sh diagnose
./docker-cli.sh fix-permissions
```

2. **Database connection issues**
```bash
./docker-cli.sh db status
./docker-cli.sh db test-connection
```

3. **Out of disk space**
```bash
./docker-cli.sh cleanup
docker system prune -a
```

### Generate Support Bundle

```bash
./docker-cli.sh support-bundle
```

This creates a comprehensive diagnostic package for troubleshooting.

## 🔄 Migration from Old System

Run the migration script:

```bash
./migrate-to-new-system.sh
```

This will:
1. Backup existing data
2. Archive old system
3. Install new CLI
4. Convert SQLite to PostgreSQL (if applicable)
5. Verify migration

## 📈 Future Enhancements

- [ ] Kubernetes deployment support
- [ ] Supabase integration (PostgreSQL in cloud)
- [ ] Multi-region deployment
- [ ] Advanced monitoring with Prometheus/Grafana
- [ ] Automated performance tuning
- [ ] GitOps integration

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

Built with PostgreSQL, Docker, Docker Compose, and shell scripting best practices.