# DhafnckMCP Documentation

Welcome to the DhafnckMCP Multi-Project AI Orchestration Platform documentation.

## Table of Contents

### Getting Started
- [README](../README.md) - Project overview and quick start
- [Database Setup](../DATABASE_SETUP.md) - Database configuration guide

### Core Concepts
- [Architecture](architecture.md) - System architecture overview
- [Domain-Driven Design](domain-driven-design.md) - DDD implementation details
- [Hierarchical Context System](hierarchical-context.md) - Context inheritance and delegation
- [Hierarchical Context Migration](HIERARCHICAL_CONTEXT_MIGRATION.md) - Migration guide from basic to hierarchical context

### Development Guides
- [Error Handling and Logging](error-handling-and-logging.md) - Comprehensive error handling patterns
- [API Reference](api-reference.md) - MCP tools and HTTP API documentation
- [Testing Guide](testing.md) - Unit and integration testing strategies
- [ORM Agent Repository Implementation](orm-agent-repository-implementation.md) - ORM-based agent repository guide
- [Context Auto-Detection Fix](CONTEXT_AUTO_DETECTION_FIX.md) - Enhanced auto-detection with error handling

### Operations
- [Docker Deployment](docker-deployment.md) - Running with Docker
- [Configuration](configuration.md) - Environment variables and settings

### Troubleshooting
- [Comprehensive Troubleshooting Guide](COMPREHENSIVE_TROUBLESHOOTING_GUIDE.md) - Systematic problem diagnosis and solutions
- [Troubleshooting](TROUBLESHOOTING.md) - Common issues and quick fixes

## Quick Links

- **Error Handling**: See [Error Handling and Logging](error-handling-and-logging.md) for comprehensive error management
- **Database Setup**: See [Database Setup Guide](../DATABASE_SETUP.md) for SQLite/PostgreSQL configuration
- **API Documentation**: See [API Reference](api-reference.md) for MCP tools documentation

## Recent Updates

- Added comprehensive error handling and logging system
- PostgreSQL support with JSONB for better performance
- Enhanced hierarchical context system with custom data fields
- Improved caching with proper async/sync handling
- **NEW**: ORM-based agent repository implementation with comprehensive test suite
- **NEW**: Completed migration to 4-tier hierarchical context system (Global → Project → Branch → Task)
- **NEW**: Updated all tools to use UUID-based git_branch_id instead of branch names
- **NEW**: Enhanced context auto-detection with comprehensive error handling and fallback options
- **NEW**: Complete documentation overhaul with architecture guides, API reference, and troubleshooting
- **NEW**: Comprehensive testing guide with TDD patterns and performance testing
- **NEW**: Docker deployment guide with production-ready configurations

## Contributing

Please see [CONTRIBUTING.md](../CONTRIBUTING.md) for guidelines on contributing to this project.