# Database Mode Configuration

## Overview

The DhafnckMCP system uses a database source manager to automatically select the appropriate database based on the execution context. This ensures data consistency between MCP calls and the frontend while maintaining isolation for tests.

## Database Modes

### 1. TEST Mode (pytest)
- **Path**: `dhafnck_mcp_main/database/data/dhafnck_mcp_test.db`
- **When**: Running pytest tests
- **Purpose**: Test isolation and data safety

### 2. NORMAL Mode (local development)
- **Path**: `/data/dhafnck_mcp.db` (same as Docker database)
- **When**: Regular local development
- **Purpose**: Local development using the same database as Docker for consistency

### 3. DOCKER Mode (inside container)
- **Path**: `/data/dhafnck_mcp.db`
- **When**: Running inside Docker container
- **Purpose**: Production/containerized deployment

### 4. STDIN Mode (MCP calls)
- **Path**: `dhafnck_mcp_main/database/data/dhafnck_mcp.db` (local database)
- **When**: MCP server context (detected via stdin)
- **Purpose**: **MCP stdin communication uses local database (cannot access Docker database)**

## Key Behavior

### Database Consistency Strategy
- **Docker container and local development** MUST use the Docker database (`/data/dhafnck_mcp.db`) for consistency
- **MCP STDIN mode** uses local database (cannot access Docker database due to stdin communication)
- **Frontend** connects to Docker container, so it uses the Docker database
- **Error handling**: Server will fail to start if Docker database is not accessible for Docker/Local modes

### Test Database Isolation
- Tests always use the isolated test database (`dhafnck_mcp_test.db`)
- This prevents test data from interfering with development or production data
- Tests remain completely isolated regardless of Docker database availability

### Local Development
- Local development MUST use the Docker database (`/data/dhafnck_mcp.db`) for consistency
- Server will fail to start if Docker database is not accessible
- This ensures strict consistency between local development and frontend
- **Requirement**: Docker container must be running for local development

## Configuration

### Environment Variables
- `MCP_DB_PATH`: Override database path explicitly
- `DOCKER_DB_PATH`: Override Docker database path (default: `/data/dhafnck_mcp.db`)

### Docker Volume Mapping
The Docker container mounts the database volume:
```yaml
volumes:
  - dhafnck_data:/data
```

## Troubleshooting

### Problem: Server fails to start with "Docker database not accessible"
**Solution**: Start Docker container first: `docker-compose up -d`

### Problem: Local development fails with Docker database error
**Solution**: 
1. Ensure Docker container is running
2. Check Docker volume is mounted correctly
3. Verify `/data/dhafnck_mcp.db` path exists in container

### Problem: Tests interfere with development data
**Solution**: Ensure pytest is detected properly (should use test database automatically)

### Problem: Frontend and local development show different data
**Solution**: Both should use Docker database - if not, check Docker container status

## Summary

**Database Usage by Mode:**
- **Tests**: `dhafnck_mcp_test.db` (isolated)
- **Docker Container**: `/data/dhafnck_mcp.db` (Docker database)
- **Local Development**: `/data/dhafnck_mcp.db` (Docker database for consistency)
- **MCP STDIN**: local `dhafnck_mcp.db` (cannot access Docker database)

This configuration ensures:
1. **Strict consistency** between local development, frontend, and Docker container
2. **Test isolation** to prevent interference with development data
3. **Technical limitations** handled appropriately (MCP STDIN uses local database)
4. **Fail-fast behavior** when Docker database is not accessible (prevents data inconsistency)

## Verification

Check the current database mode and path:
```bash
python -c "
import sys; sys.path.insert(0, 'src')
from fastmcp.task_management.infrastructure.database.database_source_manager import get_database_path, get_database_mode
print('Mode:', get_database_mode().value)
print('Path:', get_database_path())
"
```