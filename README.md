# DhafnckMCP - Agentic Project Platform

[![Architecture Status](https://img.shields.io/badge/Architecture-Production%20Ready-brightgreen)](https://github.com/dhafnck/dhafnck_mcp)
[![MCP Version](https://img.shields.io/badge/MCP-2.1.0-blue)](https://github.com/dhafnck/dhafnck_mcp)
[![Docker Support](https://img.shields.io/badge/Docker-Multi%20Mode-orange)](https://github.com/dhafnck/dhafnck_mcp)
[![Scale Target](https://img.shields.io/badge/Scale-1M%2B%20RPS-red)](https://github.com/dhafnck/dhafnck_mcp)

## 🎯 **Project Overview**

DhafnckMCP is an enterprise-grade Model Context Protocol (MCP) platform designed for agentic project management and multi-agent orchestration. The platform provides comprehensive task management, project coordination, and AI agent collaboration capabilities with cloud-scale architecture.

### 🏗️ **Core Architecture**

- **MCP Server**: FastMCP-based server with streamable HTTP transport
- **Task Management**: Comprehensive DDD-compliant task lifecycle management
- **Agent Orchestration**: Multi-agent coordination with role-based switching
- **Project Management**: Hierarchical project organization with context inheritance
- **Frontend Dashboard**: React-based monitoring and control interface
- **Docker Infrastructure**: Multi-mode containerized deployment

## 🚀 **Quick Start**

### Prerequisites

- **Python 3.8+** with virtual environment support
- **Docker & Docker Compose** for containerized deployment
- **Node.js 18+** for frontend development (optional)
- **WSL2** (Windows users) or **Linux/macOS**

### 🐳 **Docker Setup (Recommended)**

The project includes a sophisticated Docker management system with multiple operational modes:

```bash
# Clone the repository
git clone <repository-url>
cd agentic-project

# Quick start with Docker (interactive menu)
./run_docker.sh

# Or run in development mode with hot reload
./run_docker.sh --dev
```

#### Available Docker Modes

| Mode | Command | Description | Use Case |
|------|---------|-------------|----------|
| **Normal** | `./run_docker.sh` | Production-ready stable setup | Production deployment |
| **Development** | `./run_docker.sh --dev` | Debug mode with hot reload + MCP inspector | Active development |
| **Local** | Docker menu → Local | No auth, simplified for testing | Local development |
| **Redis** | Docker menu → Redis | Session persistence with Redis | Stateful applications |

### 🔧 **Development Setup**

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # Linux/Mac
# or .venv\Scripts\activate  # Windows

# Install dependencies
cd dhafnck_mcp_main
pip install -e .

# Run MCP server directly
./run_mcp_server.sh

# Check server health
curl http://localhost:8000/health
```

### 📊 **Frontend Dashboard**

The project includes a comprehensive React-based dashboard:

```bash
# Access via Docker (automatic)
# Frontend available at: http://localhost:3800

# Or run locally
cd dhafnck-frontend
npm install
npm start
```

## 🛠️ **MCP Tools & Capabilities**

### Core MCP Tools

The platform provides 50+ MCP tools organized into functional categories:

#### 🎯 **Task Management**
- `mcp__dhafnck_mcp_http__manage_task`: Complete task lifecycle management
- `mcp__dhafnck_mcp_http__manage_subtask`: Subtask creation and tracking
- `mcp__dhafnck_mcp_http__manage_dependencies`: Task dependency management
- `mcp__dhafnck_mcp_http__manage_git_branch`: Hierarchical task organization

#### 🤖 **Agent Orchestration**
- `mcp__dhafnck_mcp_http__call_agent`: Dynamic agent role switching
- `mcp__dhafnck_mcp_http__manage_agent`: Agent registration and management
- `mcp__dhafnck_mcp_http__agent_coordination`: Multi-agent collaboration

#### 📋 **Project Management**
- `mcp__dhafnck_mcp_http__manage_project`: Project creation and management
- `mcp__dhafnck_mcp_http__manage_git_branch`: Git branch coordination
- `mcp__dhafnck_mcp_http__manage_hierarchical_context`: Context inheritance

#### 🔄 **Context Management**
- `mcp__dhafnck_mcp_http__manage_context`: Context creation and updates
- `mcp__dhafnck_mcp_http__manage_delegation_queue`: Context delegation
- `mcp__dhafnck_mcp_http__validate_context_inheritance`: Context validation

#### 🛡️ **Security & Compliance**
- `mcp__dhafnck_mcp_http__manage_compliance`: Compliance tracking
- `mcp__dhafnck_mcp_http__validate_token`: Authentication validation
- `mcp__dhafnck_mcp_http__manage_connection`: Connection management

### 🎨 **Agent Roles & Specializations**

The platform supports 20+ specialized AI agents:

| Agent | Role | Specialization |
|-------|------|----------------|
| `@uber_orchestrator_agent` | System Orchestrator | Complex task coordination |
| `@coding_agent` | Development | Code implementation |
| `@debugger_agent` | Debugging | Error resolution |
| `@test_orchestrator_agent` | Testing | QA and validation |
| `@ui_designer_agent` | Design | UI/UX development |
| `@security_auditor_agent` | Security | Security assessment |
| `@devops_agent` | DevOps | Infrastructure management |
| `@documentation_agent` | Documentation | Technical writing |
| `@deep_research_agent` | Research | Analysis and investigation |
| `@task_planning_agent` | Planning | Project planning |

## 🐳 **Docker Management**

### Advanced Docker Operations

The `run_docker.sh` script provides comprehensive Docker management:

```bash
# Interactive Docker menu
./run_docker.sh

# Development mode with MCP inspector
./run_docker.sh --dev

# Python-based Docker management
python dhafnck_mcp_main/docker/mcp-docker.py
```

### Docker Management Features

#### 🔄 **Container Operations**
- **Start/Stop**: Multi-mode container management
- **Restart**: Graceful container restart with mode selection
- **Rebuild**: Selective or full container rebuild
- **Logs**: Real-time log monitoring across modes
- **Shell Access**: Direct container shell access

#### 🗄️ **Database Management**
- **Import/Export**: SQLite database backup and restore
- **Permissions Fix**: Automatic database permission correction
- **Health Checks**: Database connectivity validation

#### 🔍 **Development Tools**
- **MCP Inspector**: Interactive MCP server debugging
- **E2E Testing**: Automated end-to-end test execution
- **Health Monitoring**: Container health status tracking

### Docker Compose Architecture

```yaml
# Base Services (docker-compose.yml)
- dhafnck-mcp-server: MCP server backend
- dhafnck-frontend: React dashboard
- dhafnck-postgres: PostgreSQL database (optional)

# Development Extensions (docker-compose.dev.yml)
- Volume mounts for hot reload
- Debug port exposure
- Development environment variables

# Redis Extension (docker-compose.redis.yml)
- dhafnck-redis: Session persistence
- Redis configuration
- Cache optimization
```

## 🏗️ **Architecture Overview**

### System Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Dashboard                        │
│                 (React + TypeScript)                        │
│                  Port: 3800                                 │
└─────────────────────┬───────────────────────────────────────┘
                      │ HTTP/WebSocket
┌─────────────────────▼───────────────────────────────────────┐
│                  MCP Server                                 │
│              (FastMCP + Python)                             │
│                  Port: 8000                                 │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Task Mgmt   │ │ Agent Orch  │ │ Project Mgmt│          │
│  │             │ │             │ │             │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────┬───────────────────────────────────────┘
                      │ SQLite/PostgreSQL
┌─────────────────────▼───────────────────────────────────────┐
│                  Database Layer                             │
│            (SQLite + Redis Cache)                          │
│                                                             │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐          │
│  │ Tasks       │ │ Projects    │ │ Agents      │          │
│  │ Context     │ │ Rules       │ │ Sessions    │          │
│  └─────────────┘ └─────────────┘ └─────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

### DDD Architecture

The platform follows Domain-Driven Design principles:

```
Interface Layer (MCP Controllers)
    ↓
Application Layer (Facades & Use Cases)
    ↓
Domain Layer (Entities & Business Logic)
    ↓
Infrastructure Layer (Repositories & Services)
```

## 📊 **Performance & Scaling**

### Current Performance Metrics

- **Scale**: 50-100 RPS (Python monolith)
- **Response Time**: <200ms average
- **Concurrent Users**: 10-50 users
- **Database**: SQLite with Redis cache
- **Availability**: 95%+

### Scaling Roadmap

| Tier | Target RPS | Architecture | Timeline | Investment |
|------|------------|--------------|----------|------------|
| **MVP** | 100 | Docker + SQLite | Current | $0 |
| **Tier 1** | 1K | Microservices | 3 months | $210K |
| **Tier 2** | 10K | Service Mesh | 6 months | $580K |
| **Tier 4** | 1M+ | Global Edge | 12 months | $2.24M |

## 🔒 **Security & Authentication**

### Security Features

- **Token-based Authentication**: JWT with Supabase integration
- **Rate Limiting**: Per-user and per-endpoint limits
- **Access Control**: Role-based permissions
- **Audit Logging**: Comprehensive security event tracking
- **Connection Security**: TLS/SSL encryption

### Authentication Flow

```bash
# Generate authentication token
curl -X POST http://localhost:8000/auth/token

# Use token in MCP calls
mcp__dhafnck_mcp_http__validate_token(token="your-token-here")

# Check authentication status
mcp__dhafnck_mcp_http__get_auth_status()
```

## 🧪 **Testing & Quality Assurance**

### Test Categories

- **Unit Tests**: Domain logic and business rules
- **Integration Tests**: MCP tool integration
- **E2E Tests**: Full workflow testing
- **Performance Tests**: Load and stress testing
- **Security Tests**: Penetration testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src

# Run E2E tests in Docker
docker exec -it dhafnck-mcp-server pytest /app/tests/e2e

# Performance testing
python tests/performance/mcp_performance_tests.py
```

## 📈 **Monitoring & Observability**

### Health Monitoring

```bash
# Server health check
curl http://localhost:8000/health

# Connection diagnostics
./diagnose_mcp_connection.sh

# MCP inspector (development mode)
npx @modelcontextprotocol/inspector http://localhost:8000/mcp/
```

### Monitoring Dashboard

The React frontend provides real-time monitoring:

- **System Health**: Server status and performance metrics
- **Task Analytics**: Task completion rates and bottlenecks
- **Agent Performance**: Agent utilization and effectiveness
- **Connection Status**: MCP connection health and statistics

## 🛠️ **Development Guide**

### Project Structure

```
agentic-project/
├── dhafnck_mcp_main/           # MCP server implementation
│   ├── src/fastmcp/            # FastMCP framework
│   │   ├── task_management/    # Task management domain
│   │   ├── server/             # MCP server core
│   │   └── auth/               # Authentication system
│   ├── docker/                 # Docker configuration
│   ├── tests/                  # Test suites
│   └── scripts/                # Utility scripts
├── dhafnck-frontend/           # React dashboard
│   ├── src/                    # Frontend source
│   ├── public/                 # Static assets
│   └── docker/                 # Frontend Docker config
├── run_docker.sh               # Docker management script
└── README.md                   # This file
```

### Development Workflow

1. **Setup Environment**
   ```bash
   ./run_docker.sh --dev
   ```

2. **Make Changes**
   - Backend: Edit files in `dhafnck_mcp_main/src/`
   - Frontend: Edit files in `dhafnck-frontend/src/`
   - Hot reload enabled in development mode

3. **Test Changes**
   ```bash
   pytest tests/
   ```

4. **Debug Issues**
   - Use MCP inspector at http://localhost:5173
   - Check logs via Docker menu
   - Debug with container shell access

### Contributing Guidelines

1. **Code Style**: Follow PEP 8 for Python, ESLint for TypeScript
2. **Testing**: Maintain 80%+ test coverage
3. **Documentation**: Update README and inline docs
4. **Security**: Follow security best practices
5. **Performance**: Consider performance impact of changes

## 🚀 **Deployment**

### Production Deployment

```bash
# Normal production mode
./run_docker.sh
# Select "Start (normal - production mode)"

# Or direct docker-compose
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml up -d
```

### Environment Configuration

```bash
# Key environment variables
FASTMCP_TRANSPORT=streamable-http
FASTMCP_HOST=0.0.0.0
FASTMCP_PORT=8000
DHAFNCK_AUTH_ENABLED=true
SUPABASE_URL=your-supabase-url
SUPABASE_KEY=your-supabase-key
```

### Health Checks

The platform includes comprehensive health monitoring:

```bash
# Container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Application health
curl http://localhost:8000/health

# Database health
docker exec dhafnck-mcp-server sqlite3 /data/dhafnck_mcp.db ".tables"
```

## 📞 **Support & Troubleshooting**

### Common Issues

1. **Port Conflicts**: Change ports in docker-compose files
2. **Database Permissions**: Use "Fix Database Permissions" in Docker menu
3. **Memory Issues**: Increase Docker memory allocation
4. **SSL Errors**: Check network configuration and certificates

### Troubleshooting Tools

- **MCP Inspector**: Debug MCP server communication
- **Container Logs**: Real-time log monitoring
- **Health Endpoints**: System status validation
- **Database Tools**: Direct database access and repair

### Getting Help

- **Documentation**: Check `/docs` directory for detailed guides
- **Logs**: Use Docker menu to view real-time logs
- **Community**: Join our Discord/Slack channels
- **Issues**: Report bugs on GitHub issues

## 🎯 **Roadmap**

### Current Phase: Production Ready MVP

- ✅ **Core MCP Tools**: 50+ tools implemented
- ✅ **Docker Infrastructure**: Multi-mode deployment
- ✅ **Agent Orchestration**: 20+ specialized agents
- ✅ **Frontend Dashboard**: React-based monitoring
- ✅ **Security Framework**: Authentication and authorization

### Next Phase: Scaling (Q2 2025)

- 🎯 **Microservices**: Break monolith into services
- 🎯 **Kubernetes**: Container orchestration
- 🎯 **API Gateway**: Centralized API management
- 🎯 **Monitoring**: Prometheus + Grafana
- 🎯 **CI/CD**: Automated deployment pipelines

### Future Phase: Enterprise (Q3-Q4 2025)

- 🔮 **Global CDN**: Edge deployment
- 🔮 **Auto-scaling**: Dynamic resource allocation
- 🔮 **AI Enhancement**: ML-powered optimization
- 🔮 **Enterprise Integration**: SSO and compliance
- 🔮 **Multi-tenant**: SaaS deployment model

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤝 **Contributing**

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details on how to get started.

---

**Last Updated**: 2025-01-15  
**Version**: 2.1.0  
**Status**: Production Ready MVP  
**Next Milestone**: Microservices Architecture (Q2 2025)

---

### 🔗 **Quick Links**

- **Frontend Dashboard**: http://localhost:3800
- **MCP Server**: http://localhost:8000
- **Health Check**: http://localhost:8000/health  
- **MCP Inspector**: http://localhost:5173 (dev mode)
- **Docker Management**: `./run_docker.sh`

### 📊 **Key Metrics**

- **MCP Tools**: 50+ implemented
- **Agent Roles**: 20+ specialized agents
- **Docker Modes**: 4 operational modes
- **Test Coverage**: 80%+ across all components
- **Performance**: 100 RPS current, 1M+ RPS target