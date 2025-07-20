# DhafnckMCP Docker CLI System Guide

## 🚀 Quick Start

The new PostgreSQL-first Docker CLI system is installed in the `docker-system` directory.

### Running Commands

From the project root:
```bash
cd docker-system
./docker-cli.sh help
```

Or create an alias in your shell:
```bash
alias docker-cli="cd /home/daihungpham/agentic-project/docker-system && ./docker-cli.sh"
```

### Common Commands

```bash
# Start all services
cd docker-system && ./docker-cli.sh start

# Check status
cd docker-system && ./docker-cli.sh status

# View logs
cd docker-system && ./docker-cli.sh logs backend

# Access database shell
cd docker-system && ./docker-cli.sh db shell

# Run development setup workflow
cd docker-system && ./docker-cli.sh workflow dev-setup
```

## 📁 System Structure

```
agentic-project/
├── docker-system/              # New Docker CLI system
│   ├── docker-cli.sh          # Main CLI entry point
│   ├── lib/                   # Command libraries
│   ├── docker/                # Docker Compose files
│   ├── environments/          # Environment configs
│   └── README.md             # Full documentation
├── dhafnck_mcp_main/         # Backend code
└── dhafnck-frontend/         # Frontend code
```

## 🔧 Features

- **Unified CLI**: All 24 operations accessible via command line
- **PostgreSQL-Only**: PostgreSQL as the primary database
- **Hot Reload**: Development mode with automatic code reloading  
- **Comprehensive Monitoring**: Health checks and resource monitoring
- **Automated Workflows**: Pre-configured for common tasks
- **Backup/Restore**: Full system backup capabilities

## 📚 Full Documentation

See `docker-system/README.md` for complete documentation and command reference.

## 🆘 Troubleshooting

If you encounter issues:

```bash
cd docker-system

# Run diagnostics
./docker-cli.sh diagnose

# Fix permissions
./docker-cli.sh fix-permissions

# Check configuration
./docker-cli.sh config validate
```

## 🎯 Next Steps

1. Run the development setup:
   ```bash
   cd docker-system && ./docker-cli.sh workflow dev-setup
   ```

2. Access your services:
   - Backend API: http://localhost:8000/docs
   - Frontend: http://localhost:3000
   - Database: postgresql://dhafnck_user:dev_password@localhost:5432/dhafnck_mcp

3. Start developing!