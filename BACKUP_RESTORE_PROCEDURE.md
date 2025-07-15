# DhafnckMCP Database Backup/Restore Procedure

## Problem Previously Encountered
After database restore, the frontend showed 0 tasks/subtasks even though the data was correctly restored. This was caused by an outdated frontend container, not the database restore process.

## Root Cause Analysis
1. ✅ Database restore worked correctly (verified via container database queries)
2. ❌ Frontend container was built from old code without latest API improvements
3. ❌ Working directory mismatch between development (`dhafnck-frontend-backup-full-api`) and production (`dhafnck-frontend`)

## Permanent Solution

### 1. Database Backup/Restore Process (Already Working)
The existing process in `dhafnck_mcp_main/docker/mcp-docker.py` works correctly:
- Select "Import/Restore SQLite DB"
- Choose database file (e.g., `dhafnck_mcp.db.bak-20250715-230833`)
- The script automatically fixes permissions after import

### 2. After Database Restore - Frontend Update Process
**ALWAYS rebuild the frontend container after any significant database restore:**

```bash
# Stop frontend container
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml down dhafnck-frontend

# Rebuild frontend with latest code (no cache to ensure fresh build)
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml build dhafnck-frontend --no-cache

# Start updated frontend
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml up -d dhafnck-frontend
```

### 3. Verification Steps
After restore and frontend rebuild:

```bash
# Check all containers are running
docker ps

# Verify frontend is accessible
curl -s http://localhost:3800 | grep -o "<title>.*</title>"

# Check backend is responding
curl -X POST http://localhost:8000/mcp \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -H "User-Agent: MCP-Client/1.0" \
  -d '{"jsonrpc":"2.0","method":"tools/call","params":{"name":"manage_project","arguments":{"action":"list"}},"id":1}'
```

### 4. Development Workflow Best Practices

1. **Single Source of Truth**: Always work in `/dhafnck-frontend/` directory (not backup directories)
2. **Container Rebuilds**: After significant frontend changes, rebuild containers
3. **Database Verification**: After restore, verify data exists via container queries before assuming frontend issues

### 5. Quick Container Management Commands

```bash
# Full system restart (nuclear option)
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml down
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml up -d

# Backend only restart
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml restart dhafnck-mcp-server

# Frontend only rebuild and restart
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml down dhafnck-frontend
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml build dhafnck-frontend --no-cache
docker-compose -f dhafnck_mcp_main/docker/docker-compose.yml up -d dhafnck-frontend
```

## Summary
- ✅ Database backup/restore process is reliable
- ✅ Always rebuild frontend container after major changes or restores
- ✅ Verify both backend data and frontend display after operations
- ✅ Use single development directory (`/dhafnck-frontend/`) to avoid confusion

The issue was **never** with the database restore - it was with outdated frontend code in the container.