# MCP System Fix Tasks - Critical Issues - 2025-08-29

Based on comprehensive testing, the following tasks must be completed to restore MCP system functionality.

## 🔴 CRITICAL TASK 1: Fix Expired Authentication Tokens

**Priority**: URGENT  
**Estimated Time**: 30 minutes  
**Impact**: Blocks all API testing and development  

### Problem
All test tokens in environment are expired (expired 2025-08-23, current 2025-08-29):
- `TEST_JWT_TOKEN`: Expired
- `DEBUG_JWT_TOKEN`: Expired  
- Cannot access any authenticated endpoints

### Fix Steps
1. **Generate new valid tokens**:
   ```bash
   cd dhafnck_mcp_main
   python3 -c "
   import jwt, os
   from datetime import datetime, timedelta
   
   jwt_secret = os.environ.get('SUPABASE_JWT_SECRET', os.environ.get('JWT_SECRET_KEY'))
   payload = {
       'token_id': 'tok_dev_' + str(hash('dev') % 100000),
       'user_id': '65d733e9-04d6-4dda-9536-688c3a59448e',
       'scopes': ['read:tasks', 'read:context', 'write:context', 'write:tasks', 'read:agents', 'write:agents', 'execute:mcp'],
       'exp': int((datetime.now() + timedelta(days=90)).timestamp()),
       'iat': int(datetime.now().timestamp()),
       'type': 'api_token'
   }
   token = jwt.encode(payload, jwt_secret, algorithm='HS256')
   print(f'NEW_TOKEN={token}')
   "
   ```

2. **Update .env file** with new tokens
3. **Test token validation** endpoint
4. **Verify API access** with new token

### Success Criteria
- [ ] New token passes validation endpoint
- [ ] Can access `GET /api/v2/projects/` with 200 response
- [ ] Can create test project successfully

---

## 🔴 CRITICAL TASK 2: Fix JWT Signature Verification Mismatch

**Priority**: URGENT  
**Estimated Time**: 45 minutes  
**Impact**: Authentication system completely broken  

### Problem
Token validation returns "Signature verification failed" even with correctly generated tokens.

### Investigation Steps
1. **Check server JWT configuration**:
   - Review `fastmcp/auth/middleware/dual_auth_middleware.py`
   - Check which JWT secret is used for verification
   - Compare with token generation secret

2. **Test with each JWT secret**:
   - `JWT_SECRET_KEY`
   - `SUPABASE_JWT_SECRET` 
   - `TEST_LOCAL_JWT_SECRET`

3. **Check middleware order**:
   - Verify DualAuthMiddleware configuration
   - Check request processing pipeline

### Fix Steps
1. **Identify correct JWT secret** used by server
2. **Generate tokens with matching secret**
3. **Update environment configuration** if needed
4. **Test authentication flow** end-to-end

### Success Criteria
- [ ] Token validation endpoint returns `{"valid": true}`
- [ ] All API endpoints accept generated tokens
- [ ] Authentication middleware works correctly

---

## 🔴 CRITICAL TASK 3: Set Up MCP Server for MCP Tools

**Priority**: HIGH  
**Estimated Time**: 60 minutes  
**Impact**: MCP tools from documentation unavailable  

### Problem
MCP tools (`mcp__dhafnck_mcp_http__*`) not available because MCP server not running in MCP protocol mode.

### Investigation Steps
1. **Check current MCP server status**:
   ```bash
   ps aux | grep mcp
   ```

2. **Test MCP server startup**:
   ```bash
   cd dhafnck_mcp_main
   export PYTHONPATH="src:$PYTHONPATH"
   python3 -m fastmcp.server.mcp_entry_point
   ```

3. **Check MCP configuration**:
   - Review `configuration/mcp.json`
   - Check `configuration/mcp_project_template.json`

### Fix Steps
1. **Set up proper Python path**
2. **Start MCP server in MCP mode**:
   ```bash
   cd dhafnck_mcp_main
   export PYTHONPATH="src:$PYTHONPATH"
   python3 -m fastmcp.server.mcp_entry_point --transport=stdio
   ```

3. **Test MCP tools availability**:
   - Try calling `mcp__dhafnck_mcp_http__manage_connection`
   - Test `mcp__dhafnck_mcp_http__manage_project`

4. **Create MCP server startup script**

### Success Criteria
- [ ] MCP server starts without errors
- [ ] MCP tools become available in function list
- [ ] Can call `mcp__dhafnck_mcp_http__manage_connection(action="health_check")`
- [ ] Can list projects via MCP tools

---

## 🟡 MEDIUM TASK 4: Add Authentication Bootstrap

**Priority**: MEDIUM  
**Estimated Time**: 30 minutes  
**Impact**: Improves development workflow  

### Problem
Circular dependency: need token to generate tokens.

### Fix Steps
1. **Add bootstrap endpoint** that doesn't require authentication:
   ```python
   @server.custom_route("/bootstrap/token", methods=["POST"])
   async def bootstrap_token(request):
       # Only allow in development mode
       if os.environ.get("DHAFNCK_ENV") != "development":
           return JSONResponse({"error": "Bootstrap only available in development"}, 403)
       # Generate token logic
   ```

2. **Add development authentication bypass**:
   ```python
   if os.environ.get("DHAFNCK_AUTH_ENABLED") == "false":
       # Bypass authentication
   ```

3. **Create token generation script** for local development

### Success Criteria
- [ ] Bootstrap endpoint works in development mode
- [ ] Can generate initial tokens without existing authentication
- [ ] Development workflow improved

---

## 🟡 LOW TASK 5: Update Documentation and Test Examples

**Priority**: LOW  
**Estimated Time**: 20 minutes  
**Impact**: Prevents future confusion  

### Fix Steps
1. **Update CLAUDE.md** with working token examples
2. **Update test documentation** with current tokens
3. **Add troubleshooting section** for authentication issues
4. **Document MCP server startup process**

### Success Criteria
- [ ] Documentation examples work with current system
- [ ] New developers can follow setup instructions
- [ ] Troubleshooting guide available

---

## Execution Order

1. **TASK 2** (JWT verification) - Root cause
2. **TASK 1** (Generate tokens) - Immediate unblock  
3. **TASK 3** (MCP server) - Restore MCP functionality
4. **TASK 4** (Bootstrap) - Improve workflow
5. **TASK 5** (Documentation) - Prevent future issues

## Testing Checklist

After completing fixes, verify:
- [ ] Health endpoint: `GET /health` ✅ 200
- [ ] Token validation: `POST /api/v2/tokens/validate` ✅ `{"valid": true}`
- [ ] List projects: `GET /api/v2/projects/` ✅ 200
- [ ] Create project: `POST /api/v2/projects/` ✅ 201
- [ ] List tasks: `GET /api/v2/tasks/` ✅ 200
- [ ] MCP connection: `mcp__dhafnck_mcp_http__manage_connection` ✅ Working
- [ ] MCP project tools: `mcp__dhafnck_mcp_http__manage_project` ✅ Working

## Files to Modify

1. `.env` - Update test tokens
2. `fastmcp/auth/middleware/dual_auth_middleware.py` - Check JWT config
3. `fastmcp/server/mcp_entry_point.py` - Add bootstrap endpoint
4. `CLAUDE.md` - Update documentation
5. `configuration/mcp.json` - MCP server config

---

**Created**: 2025-08-29 07:50:00 UTC  
**Total Estimated Time**: 3 hours  
**Priority**: 3 Critical, 1 Medium, 1 Low