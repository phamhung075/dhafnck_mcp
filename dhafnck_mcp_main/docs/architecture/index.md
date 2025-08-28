# Architecture Documentation Index

## Overview
This directory contains comprehensive architecture documentation for the DhafnckMCP system, focusing on proper implementation patterns, repository management, and caching strategies.

## 📚 Documentation Structure

### Core Architecture Guides

#### 1. [MCP Server Architecture Guide](MCP_SERVER_ARCHITECTURE_GUIDE.md)
**Purpose**: Complete architecture overview and implementation instructions for agents
- Request flow patterns (Controller → Facade → Use Case → Repository)
- Layer responsibilities and separation of concerns
- Repository Factory pattern implementation
- Cache Strategy with Redis on/off toggle
- Environment configuration management
- Implementation checklist and best practices

#### 2. [Agent Architecture Implementation Guide](AGENT_ARCHITECTURE_PROMPT.md) ⭐ **NEW**
**Purpose**: Comprehensive prompt for AI agents to follow correct architecture
- Executive summary with mission statement
- Visual architecture diagrams with complete flow
- Step-by-step implementation guide for each layer
- Repository switching logic (SQLite/Supabase)
- Cache management with Redis toggle
- Critical rules and anti-patterns to avoid
- Performance considerations and debugging guide

#### 3. [Repository Switching Strategy Guide](REPOSITORY_SWITCHING_GUIDE.md) ⭐ **NEW**
**Purpose**: Detailed guide on automatic repository selection based on environment
- Repository selection matrix
- Configuration examples for all scenarios
- Repository Factory implementation patterns
- Docker Compose configurations
- Testing strategies for different configurations
- Monitoring and troubleshooting guide

#### 4. [Repository Layer Architecture Analysis](REPOSITORY_LAYER_ARCHITECTURE_ANALYSIS.md)
**Purpose**: Verification that repository layer correctly implements DDD, ORM, and Redis cache
- DDD architecture compliance checklist
- ORM implementation patterns
- Redis cache integration analysis
- Security and isolation features
- Performance optimizations
- Architecture score: 95/100

## 🎯 Quick Reference

### For AI Agents Starting New Work
1. Read [Agent Architecture Implementation Guide](AGENT_ARCHITECTURE_PROMPT.md) first
2. Understand the flow: Controller → Facade → Use Case → Repository Factory → Repository
3. Follow the implementation checklist
4. Never hardcode repository implementations

### For Understanding Repository Selection
1. Check [Repository Switching Strategy Guide](REPOSITORY_SWITCHING_GUIDE.md)
2. See the selection matrix for different environments
3. Understand factory pattern implementation
4. Configure environment variables correctly

### For Architecture Verification
1. Review [Repository Layer Architecture Analysis](REPOSITORY_LAYER_ARCHITECTURE_ANALYSIS.md)
2. Verify DDD compliance
3. Check cache invalidation implementation
4. Ensure proper layer separation

## 🔑 Key Concepts

### Repository Factory Pattern
```python
# Central decision point for repository selection
RepositoryFactory.get_task_repository()
  ├── if ENVIRONMENT=test → SQLiteRepository
  └── if ENVIRONMENT=production
      ├── if DATABASE_TYPE=supabase → SupabaseRepository
      └── if REDIS_ENABLED=true → Wrap with CachedRepository
```

### Environment Variables Control Everything
```bash
ENVIRONMENT=test|production  # Determines SQLite vs Production DB
DATABASE_TYPE=supabase|postgresql  # Production database type
REDIS_ENABLED=true|false  # Cache layer on/off
```

### Cache Invalidation Pattern
```python
# Always invalidate after data changes
def update_entity(entity):
    result = repository.update(entity)
    cache.invalidate(f"entity:{entity.id}")
    return result
```

## ⚠️ Critical Rules

### NEVER DO:
- ❌ Hardcode repository implementations
- ❌ Skip architectural layers
- ❌ Assume cache is always available
- ❌ Forget cache invalidation on updates/deletes
- ❌ Mix test and production databases

### ALWAYS DO:
- ✅ Use RepositoryFactory for all repository creation
- ✅ Follow layer hierarchy strictly
- ✅ Check cache availability before using
- ✅ Invalidate cache after data changes
- ✅ Handle cache failures gracefully

## 📊 Architecture Compliance Status

| Component | Status | Score | Notes |
|-----------|--------|-------|-------|
| DDD Implementation | ✅ Complete | 95% | Proper separation of concerns |
| Repository Pattern | ✅ Complete | 100% | Abstract interfaces, concrete implementations |
| Factory Pattern | ✅ Complete | 100% | Environment-based selection |
| ORM Abstraction | ✅ Complete | 95% | SQLAlchemy with proper patterns |
| Redis Cache | ✅ Complete | 90% | Optional layer with fallback |
| Cache Invalidation | ✅ Fixed | 100% | All repositories now invalidate properly |

## 🚀 Recent Updates (2025-08-28)

### Fixed Issues
1. **Cache Invalidation**: Previously commented out code has been fixed across all repositories
2. **CacheInvalidationMixin**: Created reusable mixin for consistent implementation
3. **Context Repositories**: All 4 levels (Global/Project/Branch/Task) now properly invalidate cache

### New Documentation
1. **Agent Architecture Prompt**: Comprehensive guide for AI agents
2. **Repository Switching Guide**: Detailed environment-based selection documentation
3. **Architecture Index**: This index file for easy navigation

## 📝 Next Steps

For developers and AI agents working on this system:

1. **Always consult these guides** before implementing new features
2. **Follow the factory pattern** for repository creation
3. **Test with different configurations** (cache on/off, different databases)
4. **Monitor repository selection** using logging and health checks
5. **Update documentation** when making architectural changes

## 🔗 Related Documentation

- [Main Documentation Index](/docs/index.md)
- [Vision System Documentation](/docs/vision/)
- [Development Guides](/docs/DEVELOPMENT GUIDES/)
- [Troubleshooting Guides](/docs/troubleshooting-guides/)

---

*Last Updated: 2025-08-28*
*Architecture Version: 2.0*
*Cache Strategy: Redis with Optional Toggle*
*Repository Pattern: Factory-based Selection*