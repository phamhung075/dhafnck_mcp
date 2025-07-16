# Fix 3: Home Directory Permission Errors

**Date**: 2025-07-16  
**Issue**: Next task feature fails with permission denied error for /home/daihungpham  
**Status**: RESOLVED ✅

## Problem Description

The dhafnck_mcp_http system had hardcoded paths to `/home/daihungpham/agentic-project` throughout the codebase. This caused permission errors when:

- Running in Docker containers (different user/environment)
- Running on different machines or by different users
- Attempting to access the hardcoded home directory path

The error manifested as:
```
Error: [Errno 13] Permission denied: '/home/daihungpham'
```

## Root Cause

Multiple files contained hardcoded fallback paths:
```python
return Path("/home/daihungpham/agentic-project")
```

These hardcoded paths were used as fallbacks when the system couldn't determine the project root dynamically.

## Solution

Replaced all hardcoded paths with environment-aware code that:

1. **Uses environment variables** - Respects `DHAFNCK_DATA_PATH` environment variable
2. **Attempts dynamic discovery** - Tries to find project root from current location
3. **Safe fallback** - Uses `/tmp/dhafnck_project` instead of home directory

### Code Changes

Modified 11 files to replace hardcoded paths with:

```python
# Use environment variable or default data path
data_path = os.environ.get('DHAFNCK_DATA_PATH', '/data')
# If running in development, try to find project root
if not os.path.exists(data_path):
    # Try current working directory
    cwd = Path.cwd()
    if (cwd / "dhafnck_mcp_main").exists():
        return cwd
    # Try parent directories
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "dhafnck_mcp_main").exists():
            return current
        current = current.parent
    # Fall back to temp directory for safety
    return Path("/tmp/dhafnck_project")
return Path(data_path)
```

### Files Modified

1. `infrastructure/services/agent_doc_generator.py`
2. `infrastructure/database/database_initializer.py`
3. `infrastructure/utilities/directory_utils.py`
4. `infrastructure/repositories/task_repository_factory.py`
5. `infrastructure/repositories/subtask_repository_factory.py`
6. `infrastructure/repositories/sqlite/git_branch_repository.py`
7. `infrastructure/repositories/sqlite/template_repository.py`
8. `infrastructure/repositories/template_repository_factory.py`
9. `infrastructure/repositories/hierarchical_context_repository_factory.py`
10. `application/use_cases/call_agent.py`
11. `interface/cursor_rules_tools_ddd.py`

### Docker Configuration

Added `DHAFNCK_DATA_PATH` environment variable to `docker-compose.yml`:
```yaml
environment:
  DHAFNCK_DATA_PATH: /data
```

## Testing Results

After implementing the fix and restarting the Docker container:

- ✅ **Next task feature**: Now works without permission errors
- ✅ **Context resolution**: Successfully resolves and creates contexts
- ✅ **File operations**: Use proper data paths instead of home directory
- ✅ **Cross-environment**: Works in Docker and local environments

### Verification Test

Successfully called `manage_task(action="next")`:
- No permission errors
- Retrieved task with full context data
- Context includes hierarchical inheritance

## Impact

This fix ensures:
1. **Portability** - System works across different environments
2. **Security** - No inappropriate access to user home directories
3. **Container compatibility** - Works properly in Docker containers
4. **Multi-user support** - Different users can run the system

## Deployment Notes

1. Changes require Docker container restart to take effect
2. Environment variable `DHAFNCK_DATA_PATH` is now available for customization
3. Backward compatible - still attempts to find project root dynamically
4. Safe fallback to temp directory prevents permission errors

## Lessons Learned

- Never hardcode absolute paths, especially to user directories
- Use environment variables for configurable paths
- Provide safe fallbacks that won't cause permission errors
- Dynamic path discovery should be the primary approach
- Container environments require special consideration for file paths

## Best Practices Applied

1. **Environment awareness** - Respects container vs local environments
2. **Dynamic discovery** - Attempts to find paths intelligently
3. **Safe defaults** - Falls back to accessible locations
4. **Configuration options** - Allows path customization via environment
5. **Error prevention** - Avoids permission-denied scenarios