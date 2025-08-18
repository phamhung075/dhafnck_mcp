# Changelog (Condensed)

All notable changes to the DhafnckMCP AI Agent Orchestration Platform.

Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) | Versioning: [Semantic](https://semver.org/spec/v1.0.0.html)

## [Unreleased]

### Security
- **PostgreSQL Credentials Exposure Fix** (2025-08-18)
  - Updated `database_config.py` to use environment variables instead of hardcoded strings
  - Created secure configuration template `.env.secure.example`
  - Added `SECURITY_INCIDENT_RESPONSE.md` with remediation steps

### Fixed
- **Frontend Signup Auth API Integration** (2025-08-18) - Integrated auth endpoints into MCP server (port 8000)
- **3-second Facade Initialization Delay** (2025-08-18) - Singleton pattern optimization (604.7x speedup)
- **Parameter Type Coercion Bug** (2025-08-18) - Fixed manage_subtask type validation

### Changed
- **OAuth2PasswordBearer Migration** (2025-08-18) - Replaced custom middleware with FastAPI built-in auth
  - 50% code reduction, standards-compliant OAuth2, automatic API documentation

### Added
- **Complete Authentication System** (2025-08-17) - DDD-pattern backend with JWT, bcrypt, session management

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

## [v0.0.0] - 2025-01-06

### Major Updates
- **Database Migration** - PostgreSQL/Supabase support, removed SQLite
- **Performance** - Connection pooling, async operations, singleton patterns
- **Testing** - Comprehensive test suite (unit/integration/e2e/performance)

## [v0.0.1] - 2025-06-15

### Breaking Changes
- Complete architecture redesign with DDD patterns
- New MCP protocol implementation
- Hierarchical context system introduction

## Quick Stats
- **Total Agents**: 60+ specialized agents
- **MCP Tools**: 15 categories
- **Performance**: <5ms Vision System overhead, 604x facade speedup
- **Test Coverage**: 500+ tests across all categories
- **Docker Configs**: 5 deployment options
- **Languages**: Python (backend), TypeScript (frontend)

## Migration Notes

### From v0.0.1 to v0.0.x
1. Update database configuration (PostgreSQL required)
2. Run migration scripts in `database/migrations/`
3. Update environment variables per `.env.secure.example`

### From v0.0.x to v0.0.x 
Complete rewrite - refer to migration guide in `docs/migration-guides/`

## Documentation
- **Core**: `/dhafnck_mcp_main/docs/`
- **Vision System**: `/dhafnck_mcp_main/docs/vision/` (CRITICAL)
- **API**: `/dhafnck_mcp_main/docs/api-integration/`
- **Operations**: `/dhafnck_mcp_main/docs/operations/`

---
For detailed changes, see [CHANGELOG.md](./CHANGELOG.md)