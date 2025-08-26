# Changelog

All notable changes to the DhafnckMCP AI Agent Orchestration Platform.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | Versioning: [Semantic](https://semver.org/spec/v1.0.0.html)

## [Unreleased]

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