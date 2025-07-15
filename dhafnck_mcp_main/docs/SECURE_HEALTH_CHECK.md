# Secure Health Check Implementation

## Overview

This document describes the secure health check system implemented to prevent sensitive server information from being exposed to clients. The system provides different levels of information based on user access levels.

## Security Problem

The original health check system exposed sensitive information to all clients, including:

- **Internal file paths** (`/app/src`, `/data/tasks`, `/app/agent-library`)
- **Environment variables** and configuration details
- **Database connection information**
- **System architecture details**
- **Authentication system internals**

This information could be used by malicious actors for:
- Path traversal attacks
- System fingerprinting
- Reconnaissance for targeted attacks
- Understanding internal architecture for exploit development

## Solution: Role-Based Information Filtering

### Access Levels

The secure health check system implements three access levels:

#### 1. CLIENT (Default - Production Safe)
**For**: Public/external health checks, monitoring systems, untrusted clients

**Returns**:
```json
{
  "success": true,
  "status": "healthy",
  "timestamp": 1751473067.7065842
}
```

**Security**: No sensitive information exposed

#### 2. AUTHENTICATED (Limited Details)
**For**: Logged-in users, internal monitoring, basic diagnostics

**Returns**:
```json
{
  "success": true,
  "status": "healthy",
  "server_name": "DhafnckMCP Server",
  "version": "2.1.0",
  "uptime_seconds": 3600,
  "active_connections": 2,
  "timestamp": 1751473067.7065842
}
```

**Security**: Basic operational info, no sensitive paths

#### 3. ADMIN (Full Details)
**For**: Administrators, internal systems, debugging

**Returns**: Complete system information including environment, paths, and configuration

**Security**: Full diagnostic information for authorized personnel only

## Implementation

### Core Components

1. **`SecureHealthChecker`**: Main class handling security-filtered health checks
2. **`SecurityContext`**: Determines access level based on user credentials
3. **`AccessLevel`**: Enum defining the three security levels
4. **Integration**: Updated existing health check endpoints to use secure filtering

### Key Files

- `src/fastmcp/server/secure_health_check.py` - Core secure health check implementation
- `src/fastmcp/server/secure_connection_tool.py` - MCP tool with access level control
- `src/fastmcp/server/manage_connection_tool.py` - Updated to use secure filtering
- `examples/security_demonstration.py` - Demonstration script

### Usage Examples

#### Client-Safe Health Check
```python
from fastmcp.server.secure_health_check import client_health_check

result = await client_health_check()
# Returns minimal information safe for public consumption
```

#### Authenticated Health Check
```python
from fastmcp.server.secure_health_check import secure_health_check

result = await secure_health_check(
    user_id="user123",
    is_admin=False,
    is_internal=False
)
# Returns limited operational details
```

#### Admin Health Check
```python
from fastmcp.server.secure_health_check import admin_health_check

result = await admin_health_check(user_id="admin")
# Returns full diagnostic information
```

### MCP Tool Usage

The secure health check is available as an MCP tool:

```python
# Client access (default)
secure_health_check(access_level="client")

# Authenticated access
secure_health_check(access_level="authenticated")

# Admin access
secure_health_check(access_level="admin")
```

## Security Features

### Information Filtering
- **Path Sanitization**: No internal file paths exposed to clients
- **Configuration Hiding**: Environment variables filtered by access level
- **Error Handling**: Generic error messages for clients, detailed for admins
- **Response Size**: Minimal client responses reduce attack surface

### Access Control
- **Role-Based**: Different information based on user role
- **Environment-Aware**: Production vs development filtering
- **Authentication Integration**: Works with existing auth systems
- **Default Secure**: Defaults to minimal information disclosure

### Production Safety
- **Fail-Safe**: Errors default to minimal information exposure
- **Backward Compatible**: Existing systems continue to work
- **Performance**: Minimal overhead for security filtering
- **Logging**: Security events logged for audit trails

## Migration Guide

### For Existing Systems

1. **Replace Direct Health Checks**:
   ```python
   # Old (insecure)
   result = await old_health_check()
   
   # New (secure)
   result = await client_health_check()  # For clients
   result = await admin_health_check()   # For admins
   ```

2. **Update MCP Tools**:
   ```python
   # Old
   manage_connection(action="health_check")
   
   # New
   secure_health_check(access_level="client")
   ```

3. **Configure Access Levels**:
   ```python
   # Determine access level based on authentication
   if user.is_admin:
       access_level = "admin"
   elif user.is_authenticated:
       access_level = "authenticated"
   else:
       access_level = "client"
   ```

### For New Systems

Use the secure health check from the start:

```python
from fastmcp.server.secure_health_check import secure_health_check

async def health_endpoint(request):
    # Determine access level from request
    access_level = get_access_level(request)
    
    result = await secure_health_check(
        user_id=request.user_id,
        is_admin=access_level == "admin",
        is_internal=request.is_internal
    )
    
    return result
```

## Testing

Run the security demonstration to see the differences:

```bash
cd /home/daihungpham/agentic-project/dhafnck_mcp_main
python examples/security_demonstration.py
```

This will show:
- Information returned at each access level
- Security improvements over legacy system
- Sensitive information exposure analysis

## Best Practices

### For Developers
1. **Always use client-safe health checks for public endpoints**
2. **Implement proper authentication before using higher access levels**
3. **Log security-relevant health check requests**
4. **Test with different access levels during development**
5. **Never expose admin-level information to untrusted clients**

### For Administrators
1. **Monitor health check access patterns**
2. **Regularly audit what information is exposed at each level**
3. **Use admin-level checks only for internal diagnostics**
4. **Implement rate limiting on health check endpoints**
5. **Keep security filtering rules up to date**

### For Production Deployment
1. **Default to client-level access for external endpoints**
2. **Implement proper authentication for higher access levels**
3. **Use environment-based filtering (production vs development)**
4. **Monitor for suspicious health check patterns**
5. **Regularly review and update security policies**

## Security Considerations

### Threat Model
- **Information Disclosure**: Prevents sensitive path/config exposure
- **Reconnaissance**: Limits information available for attack planning
- **Privilege Escalation**: Proper access control prevents unauthorized information access
- **Social Engineering**: Minimal information reduces social engineering vectors

### Limitations
- **Authentication Required**: Higher access levels require proper authentication
- **Configuration Dependent**: Security depends on proper access level configuration
- **Legacy Compatibility**: Some legacy systems may need updates
- **Performance Impact**: Minimal but measurable filtering overhead

### Future Enhancements
- **Dynamic Filtering**: Rules-based information filtering
- **Audit Logging**: Enhanced logging of security-relevant requests
- **Rate Limiting**: Built-in rate limiting for health check endpoints
- **Anomaly Detection**: Detection of unusual health check patterns

## Conclusion

The secure health check system provides essential security improvements while maintaining functionality. By implementing role-based information filtering, we prevent sensitive information disclosure while still providing necessary diagnostic capabilities for authorized users.

Key benefits:
- ✅ **Prevents information disclosure** to untrusted clients
- ✅ **Maintains diagnostic capabilities** for administrators
- ✅ **Backward compatible** with existing systems
- ✅ **Production ready** with secure defaults
- ✅ **Scalable** access control system

This implementation follows security best practices and provides a foundation for secure health monitoring in production environments. 