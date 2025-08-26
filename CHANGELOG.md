# Changelog

All notable changes to the DhafnckMCP AI Agent Orchestration Platform.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | Versioning: [Semantic](https://semver.org/spec/v1.0.0.html)

## [Unreleased]

### Fixed
- **Removed Default User ID Fallback** (2025-08-26)
  - Eliminated all default user ID fallback code per security requirements
  - Fixed warning "User context middleware not available - using default user ID" 
  - Updated all MCP controllers to require authentication with no fallbacks:
    - `agent_mcp_controller.py` - Now raises UserAuthenticationRequiredError instead of using None
    - `task_mcp_controller.py` - Uses auth_helper as fallback, no default user
    - `project_mcp_controller.py` - Uses get_authenticated_user_id from auth_helper
    - `git_branch_mcp_controller.py` - Uses get_authenticated_user_id from auth_helper
    - `subtask_mcp_controller.py` - Uses get_authenticated_user_id from auth_helper
  - Authentication is now strictly required for all operations - no exceptions

- **Docker Warning Fixes** (2025-08-26)
  - Fixed database schema validation sync/async handling error in `schema_validator.py`
  - Added `_validate_model_sync()` method to properly handle synchronous database connections
  - Removed obsolete `HierarchicalContext` migration code from `init_database.py`
  - Created resources directory at `dhafnck_mcp_main/data/resources/` to prevent warnings
  - Fixed `UserContextMiddleware` import warnings by aliasing to `RequestContextMiddleware`
  - Updated `auth/mcp_integration/__init__.py` and `server_config.py` for backward compatibility
  - Created minimal `config/vision_hierarchy.json` to prevent vision hierarchy loading errors
  - All Docker container warnings now resolved

- **Server Startup Error Resolution** (2025-08-26)
  - Fixed server boot loop caused by import of deleted `bearer_env` module
  - Removed `EnvBearerAuthProvider` import from `server.py` line 51
  - Removed usage of `EnvBearerAuthProvider()` fallback in server initialization
  - Server now starts successfully with DualAuthMiddleware handling all authentication
  - Backend container health check passing, server operational on port 8000

### Changed
- **Unified Single-Token Authentication** (2025-08-26)
  - Simplified DualAuthMiddleware to accept ONE token for all request types
  - Eliminated need to pass different tokens for frontend vs MCP requests
  - Implemented unified token validation with automatic fallback chain:
    - Tries Supabase JWT validation first
    - Falls back to local JWT validation
    - Finally tries MCP token validation
  - Token extraction from multiple sources: Bearer header, cookies, custom headers
  - Updated authentication documentation to reflect single-token approach
  - Key benefit: Pass one token, access everything - no token conversion needed

### Added
- **Authentication Documentation** (2025-08-26)
  - Created comprehensive authentication architecture documentation
  - Added detailed token flow documentation with diagrams
  - Created auth system README with quick start guide
  - Documented dual-token system (Supabase for users, MCP for tools)
  - Added security best practices and troubleshooting guides
  - Included migration guide from single to dual token system

### Removed
- **Authentication System Cleanup** (2025-08-26)
  - Removed unused authentication systems to simplify codebase
  - Deleted `auth/bridge/` - FastAPI auth bridge (server uses Starlette directly)
  - Deleted `auth/api/dev_endpoints.py` - Development-only auth endpoints
  - Deleted `auth/interface/dev_auth.py` - Development auth interface
  - Deleted `auth/interface/fastapi_auth.py` - FastAPI auth interface (unused)
  - Deleted `auth/services/mcp_token_service.py` - Legacy MCP token service
  - Deleted `auth/middleware.py` - Legacy middleware file (replaced by modular middleware)
  - Deleted `auth/mcp_integration/thread_context_manager.py` - Thread context (async doesn't need it)
  - Deleted `auth/mcp_integration/user_context_middleware.py` - Duplicate of RequestContextMiddleware
  - Deleted `server/auth/providers/bearer_env.py` - Simple bearer token provider
  - Simplified to JWT + Supabase authentication only
  - Kept minimal OAuth stub for import compatibility

### Added
- **React 19 Upgrade with Vite Migration** (2025-08-25)
  - Updated to React 19.1.1 and React DOM 19.1.1 with TypeScript support
  - Migrated from react-scripts to Vite 7.1.3 for better performance
  - Created `vite.config.ts` with React plugin and Vitest setup
  - Moved `index.html` to root with ES module imports
  - Resolved all npm security vulnerabilities (10 → 0)
  - Significantly faster development builds and hot reload

- **Context Management v2 API** (2025-08-25)
  - Complete REST API with user authentication and isolation
  - Endpoints: GET/POST/PUT/DELETE `/api/v2/contexts/{level}/{context_id}`
  - Integrates with Supabase authentication system
  - User-scoped contexts preventing cross-user access
  - Comprehensive integration test suite

- **Enhanced Test Coverage** (2025-08-25)
  - New comprehensive test suites for unified context system
  - 5 new test files with 100+ test methods total
  - Repository tests with user scoping and UUID validation
  - Factory pattern tests with dependency injection
  - Hierarchy validation logic tests

### Fixed
- **CRITICAL AUTHENTICATION CONTEXT PROPAGATION FIX**: Resolved JWT token validation but authentication failure in MCP handlers (2025-08-26)
  - **Root Cause**: DualAuthMiddleware successfully validated JWT tokens but authentication context was not propagating to MCP request handlers, causing 401 errors
  - **Solution**: Implemented RequestContextMiddleware for authentication context propagation
  - **Implementation**:
    - Created `RequestContextMiddleware` at `src/fastmcp/auth/middleware/request_context_middleware.py` using contextvars for thread-safe storage
    - Updated `auth_helper.py` to use context variables with priority fallback chain
    - Fixed middleware ordering in `mcp_entry_point.py` (DualAuthMiddleware → RequestContextMiddleware)
    - Added comprehensive test suites for context propagation and integration
  - **Authentication Flow Now**: RequestContextMiddleware initializes → DualAuthMiddleware validates JWT → RequestContextMiddleware captures context → auth_helper reads from context → MCP handlers get authenticated user
  - **Files Modified**: 
    - `src/fastmcp/auth/middleware/request_context_middleware.py` (NEW)
    - `src/fastmcp/task_management/interface/controllers/auth_helper.py`  
    - `src/fastmcp/server/mcp_entry_point.py`
  - **Tests Added**:
    - `src/tests/fastmcp/auth/middleware/test_request_context_middleware.py`
    - `src/tests/task_management/interface/controllers/test_auth_helper_request_context_integration.py`
  - **Impact**: MCP operations now work correctly with JWT tokens, no more 401 errors despite valid authentication

- **CRITICAL AUTHENTICATION FIX**: Resolved global context user isolation authentication issue (2025-08-26)
  - **Root Cause**: JWT authentication succeeded in DualAuthMiddleware but MCP tools returned 401 "Authentication required"
  - **Fix 1**: Fixed RequestContextMiddleware ordering - moved from last to first position (ContextVar propagation issue)
  - **Fix 2**: Enforced user isolation for global contexts - removed None user_id exception  
  - **Fix 3**: Enhanced authentication debugging with comprehensive logging
  - Created comprehensive validation test suite (4/4 tests pass)
  - Files: `src/fastmcp/server/http_server.py`, `src/fastmcp/auth/mcp_integration/repository_filter.py`, `src/fastmcp/task_management/interface/controllers/auth_helper.py`
  - Documentation: `docs/troubleshooting-guides/global-context-authentication-fix.md`
  - **Impact**: MCP context operations now work correctly with JWT authentication, user isolation fully enforced

- **CRITICAL SECURITY FIX**: Resolved authentication bypass vulnerability (2025-08-26)
  - Fixed DualAuthMiddleware not loading when auth_enabled was misconfigured
  - Verified proper JWT token processing and validation
  - Confirmed authentication rejection of invalid tokens
  - Tested end-to-end authentication flow with Supabase JWT tokens
  - All authentication security tests now pass
  - Files: `dhafnck_mcp_main/src/fastmcp/server/mcp_entry_point.py`, `.env`, `docker-system/docker-compose.yml`

- **GLOBAL CONTEXT USER ISOLATION IMPLEMENTATION** (2025-08-26)
  - Implemented RequestContextMiddleware for authentication context propagation
  - Fixed JWT authentication context not being available to MCP request handlers
  - Created comprehensive multi-layer solution covering database schema, DDD layers, and frontend
  - Global context now properly auto-creates one unique context per user
  - Supports update/get operations only, deletion protected for data integrity
  - Complete test suite with TDD approach covering all layers
  - Files: `src/fastmcp/auth/middleware/request_context_middleware.py`, `src/fastmcp/task_management/interface/controllers/auth_helper.py`, multiple test files

- **Frontend Test Suite Updates** (2025-08-26)
  - Updated 7 test files to match current component implementations
  - Fixed GlobalContextDialog.test.tsx: Complete rewrite for shadcn/ui components
  - Fixed Header.test.tsx: Removed improper BrowserRouter mock
  - Fixed LazyTaskList.test.tsx: Added RefreshButton mock, updated subtask display format
  - Fixed SignupForm.test.tsx: Updated to async userEvent API, fixed import.meta.env usage
  - Fixed index.test.tsx: Removed non-existent tailwindcss import mock
  - Modernized all tests to use proper async/await patterns
- **Frontend Development Environment** (2025-08-25)
  - Fixed Node.js version compatibility: Updated from 18.20.8 to 20.x for Vite 7.1.3
  - Resolved ESM module import issues in Docker containers
  - Standardized port configuration on 3800 throughout the stack
  - Created development-focused Dockerfile with hot reload support
  - Updated docker-compose.yml with proper volume mounts and environment variables
  - Files modified: 6 files, Files created: 3 files
  - Environment test script: `docker-system/test-frontend-dev.sh`

- **Authentication Context Propagation** (2025-08-26)
  - Fixed "UserAuthenticationRequiredError" in frontend global context loading
  - Added `RequestContextMiddleware` to middleware stack
  - Resolves auth context availability for MCP operations

- **Frontend Build Optimization** (2025-08-25)
  - Fixed all ESLint warnings across 15+ frontend files
  - Removed unused imports and variables
  - Fixed React hook dependencies and exhaustive-deps warnings
  - Implemented code splitting with optimized chunk limits
  - Bundle size reduction with 15+ smaller chunks

- **JWT Authentication Chain** (2025-08-25)
  - Fixed JWT token processing for global context retrieval
  - Replaced `MCPAuthMiddleware` with `DualAuthMiddleware`
  - Enhanced auth_helper.py error handling for missing contexts
  - Dual secret support for SUPABASE_JWT_SECRET compatibility

- **Context System Fixes** (2025-08-25)
  - Fixed user ID isolation - contexts now properly scoped to users
  - Fixed serialization errors across all context levels
  - Fixed context hierarchy validation with user-scoped repositories
  - Fixed branch context foreign key constraint violations
  - Implemented proper CRUD operations with user isolation

### Security  
- **Documentation Security Audit Complete** (2025-08-25)
  - Updated 10+ guides reflecting resolved CVSS vulnerabilities (9.8, 8.9, 8.5)
  - All authentication bypass mechanisms completely eliminated
  - Documentation accurately reflects secured system state
  - Removed all fallback authentication references

### Architecture
- **Docker Configuration Consolidation** (2025-08-25)
  - Unified Docker Compose configurations
  - Multi-database support (PostgreSQL, Supabase, Redis)
  - Enhanced container orchestration

## [v0.0.2] - 2025-08-10

### Vision System & Architecture
- **Unified Context Management** - 4-tier hierarchy (Global→Project→Branch→Task)
- **Vision System Integration** - AI enrichment with <5ms overhead  
- **60+ Specialized Agents** - Task planning, debugging, UI design, security audit
- **15 MCP Tool Categories** - Comprehensive task/project/agent management

### Key Features
- Docker multi-configuration support (PostgreSQL, Supabase, Redis)
- React/TypeScript frontend (port 3800)
- FastMCP/DDD backend (port 8000)
- Automatic context inheritance and delegation
- Real-time progress tracking and workflow hints

### Performance
- 604x facade speedup optimization
- Connection pooling and async operations
- Singleton patterns implementation

### Testing
- Comprehensive test suite (unit/integration/e2e/performance)
- 500+ tests across all categories
- Performance testing with load simulation

## [v0.0.1] - 2025-06-15

### Breaking Changes
- Complete architecture redesign with DDD patterns
- New MCP protocol implementation  
- Hierarchical context system introduction

### Major Features
- Database migration to PostgreSQL/Supabase support
- Authentication system with JWT and bcrypt
- Multi-agent coordination system
- Task management with subtask support

## [v0.0.0] - 2025-01-06

### Initial Release
- Basic MCP server implementation
- SQLite database foundation
- Core task management features
- Initial agent system

## Migration Notes

### From v0.0.1 to v0.0.2
1. Update database configuration (PostgreSQL required)
2. Migrate authentication to new JWT system
3. Update MCP tool configurations
4. Test agent integrations

### From v0.0.0 to v0.0.1  
1. Migrate from SQLite to PostgreSQL/Supabase
2. Update API endpoints to DDD structure
3. Reconfigure agent definitions
4. Update context management calls

## Quick Stats
- **Total Agents**: 60+ specialized agents
- **MCP Tools**: 15 categories  
- **Performance**: <5ms Vision System overhead, 604x facade speedup
- **Test Coverage**: 500+ tests across all categories
- **Docker Configs**: 5 deployment options
- **Languages**: Python (backend), TypeScript (frontend)
- **Database**: PostgreSQL/Supabase with user isolation
- **Authentication**: JWT with dual-auth middleware support