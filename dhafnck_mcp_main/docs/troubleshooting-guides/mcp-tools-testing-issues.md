# MCP Tools Testing Issues Report

**Date**: 2025-08-30
**Environment**: DhafnckMCP v2.1.0
**Test Scope**: Direct MCP tool actions testing

## Issues Found During Testing

### 1. Database Connection Timeout

**Severity**: Critical
**Component**: All database operations (project, task, branch management)
**Error Message**: 
```
Database operation failed: (psycopg2.OperationalError) connection to server at "aws-0-eu-north-1.pooler.supabase.com" (13.48.169.15), port 5432 failed: timeout expired
```

**Affected Operations**:
- `manage_project` - create, list, get, update
- `manage_git_branch` - all operations 
- `manage_task` - all operations
- `manage_subtask` - all operations
- `manage_context` - all database-dependent operations

**Root Cause Analysis**:
- Supabase cloud database connection timing out
- Possible causes:
  1. Network connectivity issues
  2. Supabase service downtime
  3. Connection pool exhaustion
  4. Incorrect database credentials in .env file
  5. Firewall/security group blocking connection

**Workaround**: 
- Switch to local PostgreSQL or SQLite database
- Use Docker menu system to select different database configuration

---

## Fix Prompts for Issues

### Issue 1: Database Connection Timeout Fix

**Prompt for New Chat Session**:
```
I need help fixing a Supabase database connection timeout issue in the DhafnckMCP project. The error is:

"Database operation failed: (psycopg2.OperationalError) connection to server at "aws-0-eu-north-1.pooler.supabase.com", port 5432 failed: timeout expired"

Please help me:
1. Check the .env file for correct Supabase credentials
2. Verify the Supabase project is active and accessible
3. Test the connection using psql or another database client
4. If Supabase is down, switch to local PostgreSQL using docker-system/docker-menu.sh
5. Update the connection pool settings if needed
6. Add retry logic with exponential backoff for database connections

The project uses FastMCP with SQLAlchemy and the database configuration is in dhafnck_mcp_main/src/fastmcp/database_config.py
```

---

## Testing Progress Summary

### Completed Tests
- ✅ Connection health check (server healthy, database unhealthy)

### Blocked Tests (Due to Database Issue)
- ❌ Project creation
- ❌ Project listing
- ❌ Project updates
- ❌ Git branch operations
- ❌ Task management
- ❌ Subtask management
- ❌ Context management with database persistence

### Recommendations
1. **Immediate**: Switch to local database for testing
2. **Short-term**: Fix Supabase connection or update credentials
3. **Long-term**: Implement fallback database strategy
4. **Testing**: Add database connection validation before operations

---

## Environment Details
- Python Path: Multiple duplicates detected (needs cleanup)
- MVP Mode: Enabled (authentication disabled)
- Supabase Configured: True (but not connecting)
- Tasks JSON Path: /data/tasks
- Projects File Path: /data/projects/projects.json
- Agent Library Dir: /app/agent-library

## Next Steps
1. Fix database connection issue
2. Re-run all blocked tests
3. Complete remaining test scenarios
4. Update global context with testing results