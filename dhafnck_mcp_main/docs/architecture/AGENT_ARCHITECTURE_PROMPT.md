# 🤖 Agent Architecture Implementation Guide

## Executive Summary for AI Agents

**YOUR MISSION**: Implement features following the correct DDD architecture with proper repository switching (SQLite for tests, Supabase for production), optional Redis caching, and clean separation of concerns.

## 🏗️ Architecture Overview

```
┌──────────────────────────────────────────────────────┐
│                  MCP Request Entry                    │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│         INTERFACE LAYER (Controllers)                 │
│  • Receive MCP requests                               │
│  • Validate input parameters                          │
│  • Format responses                                   │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│      APPLICATION LAYER (Facades & Use Cases)          │
│  • Orchestrate business logic                         │
│  • Manage transactions                                │
│  • Coordinate between services                        │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│         DOMAIN LAYER (Entities & Services)            │
│  • Business rules and logic                           │
│  • Domain entities and value objects                  │
│  • Repository interfaces (abstractions)               │
└────────────────────┬─────────────────────────────────┘
                     ↓
┌──────────────────────────────────────────────────────┐
│     INFRASTRUCTURE LAYER (Implementations)            │
│                                                        │
│  ┌─────────────────────────────────────────┐         │
│  │         Repository Factory               │         │
│  │  Decides which implementation to use     │         │
│  └──────────────┬──────────────────────────┘         │
│                 ↓                                     │
│  ┌──────────────────────────────────────────┐        │
│  │     Environment Detection                 │        │
│  └──────┬───────────────────┬───────────────┘        │
│         ↓                   ↓                         │
│    TEST MODE           PRODUCTION MODE                │
│         ↓                   ↓                         │
│  ┌──────────────┐   ┌──────────────┐                │
│  │   SQLite     │   │   Supabase   │                │
│  │  Repository  │   │  Repository  │                │
│  └──────────────┘   └───────┬──────┘                │
│                             ↓                         │
│                    ┌─────────────────┐               │
│                    │ Cache Enabled?  │               │
│                    └────┬──────┬─────┘               │
│                        YES     NO                     │
│                         ↓       ↓                     │
│                  ┌─────────┐  ┌──────────┐          │
│                  │  Redis  │  │  Direct  │          │
│                  │  Cache  │  │ Database │          │
│                  └─────────┘  └──────────┘          │
└──────────────────────────────────────────────────────┘
```

## 📋 Step-by-Step Implementation Guide

### Step 1: Understand the Request Flow

```python
# REQUEST FLOW PATTERN:
MCP Request → Controller → Facade → Use Case → Repository Factory → Repository → Cache/Database

# NEVER DO THIS:
MCP Request → Repository  # ❌ Skipping layers
Controller → Database     # ❌ Direct database access
```

### Step 2: Controller Implementation (Interface Layer)

```python
# src/fastmcp/task_management/interface/controllers/task_mcp_controller.py

class TaskMCPController:
    """
    RESPONSIBILITIES:
    - Receive and parse MCP requests
    - Validate input parameters
    - Call appropriate facade methods
    - Format responses in MCP format
    - Handle errors gracefully
    """
    
    def __init__(self):
        # Controllers ONLY talk to facades, never to repositories directly
        self.facade = TaskApplicationFacade()
        self.response_formatter = StandardResponseFormatter()
    
    async def manage_task(self, **params):
        """Handle MCP task management request"""
        try:
            # 1. Parse and validate request
            request = self._parse_request(params)
            
            # 2. Delegate to facade (business logic)
            result = await self.facade.execute(request)
            
            # 3. Format response for MCP
            return self.response_formatter.format_success(result)
            
        except ValidationException as e:
            return self.response_formatter.format_error(e)
```

### Step 3: Facade Implementation (Application Layer)

```python
# src/fastmcp/task_management/application/facades/task_application_facade.py

class TaskApplicationFacade:
    """
    RESPONSIBILITIES:
    - Orchestrate use cases
    - Manage transactions
    - Coordinate between multiple services
    - Use repository factory to get appropriate repository
    """
    
    def __init__(self):
        # Facades use factory to get repositories
        self.repo_factory = RepositoryFactory()
        self.cache_manager = CacheManager()
        
    async def create_task(self, request: CreateTaskRequest):
        """Create a new task with proper repository and caching"""
        
        # 1. Get appropriate repository based on environment
        repository = self.repo_factory.get_task_repository()
        
        # 2. Check cache if enabled
        if self.cache_manager.is_enabled:
            cached = await self.cache_manager.get(f"task:{request.id}")
            if cached:
                return cached
        
        # 3. Execute business logic via use case
        use_case = CreateTaskUseCase(repository)
        result = await use_case.execute(request)
        
        # 4. Update cache if enabled
        if self.cache_manager.is_enabled:
            await self.cache_manager.set(f"task:{result.id}", result, ttl=300)
            
        return result
```

### Step 4: Repository Factory Pattern (Critical!)

```python
# src/fastmcp/task_management/infrastructure/repositories/repository_factory.py

import os
from typing import Optional

class RepositoryFactory:
    """
    CRITICAL COMPONENT: Decides which repository implementation to use
    based on environment configuration.
    
    Decision Logic:
    - TEST MODE (ENVIRONMENT=test) → SQLite Repository
    - PRODUCTION MODE (DATABASE_TYPE=supabase) → Supabase Repository
    - CACHE ENABLED (REDIS_ENABLED=true) → Wrap with Redis Cache
    """
    
    @staticmethod
    def get_task_repository() -> TaskRepository:
        """
        Returns appropriate repository based on environment.
        This is the ONLY place where repository selection happens!
        """
        # 1. Check environment mode
        env = os.getenv('ENVIRONMENT', 'production')
        db_type = os.getenv('DATABASE_TYPE', 'supabase')
        
        # 2. Select base repository
        if env == 'test':
            # ALWAYS use SQLite for testing
            base_repo = SQLiteTaskRepository()
        elif db_type == 'supabase':
            # Production uses Supabase
            base_repo = SupabaseTaskRepository()
        elif db_type == 'postgresql':
            # Alternative production database
            base_repo = PostgreSQLTaskRepository()
        else:
            raise ValueError(f"Unknown DATABASE_TYPE: {db_type}")
        
        # 3. Check if Redis caching should be enabled
        redis_enabled = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
        
        if redis_enabled and env != 'test':  # Never cache in test mode
            # Wrap repository with cache layer
            return CachedTaskRepository(base_repo)
        else:
            # Direct database access without cache
            return base_repo
    
    @staticmethod
    def get_context_repository() -> ContextRepository:
        """Similar pattern for context repositories"""
        base_repo = RepositoryFactory._get_base_context_repository()
        
        if os.getenv('REDIS_ENABLED', 'true').lower() == 'true':
            return CachedContextRepository(base_repo)
        else:
            return base_repo
```

### Step 5: Repository Implementations

#### SQLite Repository (Testing Only)

```python
# src/fastmcp/task_management/infrastructure/repositories/sqlite/sqlite_task_repository.py

class SQLiteTaskRepository(BaseORMRepository, TaskRepository):
    """
    PURPOSE: Used ONLY for testing
    DATABASE: Local SQLite file
    FEATURES: Fast, isolated, no external dependencies
    """
    
    def __init__(self):
        # SQLite uses local file database
        self.db_path = os.getenv('SQLITE_DB_PATH', './test.db')
        super().__init__(TaskModel)
    
    def create_task(self, task: Task) -> Task:
        """Create task in SQLite database"""
        with self.get_db_session() as session:
            db_model = TaskModel(**task.to_dict())
            session.add(db_model)
            session.commit()
            return Task.from_model(db_model)
```

#### Supabase Repository (Production)

```python
# src/fastmcp/task_management/infrastructure/repositories/supabase/supabase_task_repository.py

class SupabaseTaskRepository(BaseORMRepository, TaskRepository):
    """
    PURPOSE: Production data persistence
    DATABASE: Supabase (PostgreSQL in cloud)
    FEATURES: Scalable, reliable, cloud-hosted
    """
    
    def __init__(self):
        # Supabase uses cloud PostgreSQL
        self.supabase_url = os.getenv('SUPABASE_URL')
        self.supabase_key = os.getenv('SUPABASE_ANON_KEY')
        self.client = create_client(self.supabase_url, self.supabase_key)
        super().__init__(TaskModel)
    
    def create_task(self, task: Task) -> Task:
        """Create task in Supabase"""
        result = self.client.table('tasks').insert(task.to_dict()).execute()
        return Task.from_dict(result.data[0])
```

#### Cached Repository Wrapper

```python
# src/fastmcp/task_management/infrastructure/repositories/cached_repository.py

class CachedTaskRepository(TaskRepository):
    """
    PURPOSE: Add caching layer to any repository
    CACHE: Redis (when enabled)
    PATTERN: Cache-aside with write-through invalidation
    """
    
    def __init__(self, base_repository: TaskRepository):
        self.base_repo = base_repository
        self.cache = CacheStrategy()
    
    def get_task(self, task_id: str) -> Optional[Task]:
        """Get task with cache-aside pattern"""
        
        # 1. Try cache first
        cache_key = f"task:{task_id}"
        cached = self.cache.get(cache_key)
        if cached:
            return Task.from_dict(cached)
        
        # 2. Fetch from database
        task = self.base_repo.get_task(task_id)
        
        # 3. Update cache if found
        if task and self.cache.is_enabled:
            self.cache.set(cache_key, task.to_dict(), ttl=300)
        
        return task
    
    def update_task(self, task: Task) -> Task:
        """Update task with cache invalidation"""
        
        # 1. Update in database
        result = self.base_repo.update_task(task)
        
        # 2. Invalidate cache entries
        self.cache.invalidate(f"task:{task.id}")
        self.cache.invalidate(f"task:list:*")  # Invalidate list caches
        
        return result
```

### Step 6: Cache Strategy Implementation

```python
# src/fastmcp/task_management/infrastructure/cache/cache_strategy.py

class CacheStrategy:
    """
    PURPOSE: Intelligent caching with Redis
    FEATURES:
    - Automatic enable/disable based on environment
    - Graceful fallback if Redis unavailable
    - TTL management
    - Pattern-based invalidation
    """
    
    def __init__(self):
        self.redis_enabled = os.getenv('REDIS_ENABLED', 'true').lower() == 'true'
        self.redis_client = self._init_redis() if self.redis_enabled else None
    
    def _init_redis(self):
        """Initialize Redis with fallback"""
        try:
            client = redis.Redis(
                host=os.getenv('REDIS_HOST', 'localhost'),
                port=int(os.getenv('REDIS_PORT', 6379)),
                password=os.getenv('REDIS_PASSWORD'),
                db=int(os.getenv('REDIS_DB', 0))
            )
            # Test connection
            client.ping()
            return client
        except Exception as e:
            print(f"Redis not available: {e}")
            # Graceful fallback - system works without cache
            return None
    
    @property
    def is_enabled(self) -> bool:
        """Check if caching is actually available"""
        return self.redis_client is not None
    
    def get(self, key: str) -> Optional[dict]:
        """Get from cache if available"""
        if not self.is_enabled:
            return None
        
        try:
            cached = self.redis_client.get(key)
            return json.loads(cached) if cached else None
        except:
            return None  # Fail silently
    
    def set(self, key: str, value: dict, ttl: int = 300):
        """Set cache with TTL if available"""
        if not self.is_enabled:
            return
        
        try:
            self.redis_client.setex(key, ttl, json.dumps(value))
        except:
            pass  # Fail silently
    
    def invalidate(self, pattern: str):
        """Invalidate cache entries by pattern"""
        if not self.is_enabled:
            return
        
        try:
            for key in self.redis_client.scan_iter(pattern):
                self.redis_client.delete(key)
        except:
            pass  # Fail silently
```

## 🔧 Environment Configuration

```bash
# .env file - Controls entire system behavior

# ENVIRONMENT MODE (determines repository selection)
ENVIRONMENT=production  # Options: 'production', 'test'

# DATABASE TYPE (for production mode)
DATABASE_TYPE=supabase  # Options: 'supabase', 'postgresql', 'sqlite'

# SUPABASE CONFIGURATION (production database)
SUPABASE_URL=https://xxxxx.supabase.co
SUPABASE_ANON_KEY=xxxxx
SUPABASE_SERVICE_KEY=xxxxx

# REDIS CACHE CONFIGURATION
REDIS_ENABLED=true     # Set to 'false' to disable caching completely
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=dev_redis_password_123
REDIS_DB=0

# SQLITE CONFIGURATION (test mode only)
SQLITE_DB_PATH=./test.db
```

## 🎯 Decision Tree for Agents

```python
def determine_repository_configuration():
    """
    Decision logic for repository and cache configuration
    """
    
    # 1. Check environment mode
    if ENVIRONMENT == 'test':
        # Testing mode
        repository = SQLiteRepository()
        cache = None  # No caching in tests
        return repository
    
    # 2. Production mode - check database type
    if DATABASE_TYPE == 'supabase':
        repository = SupabaseRepository()
    elif DATABASE_TYPE == 'postgresql':
        repository = PostgreSQLRepository()
    else:
        raise ConfigurationError(f"Invalid DATABASE_TYPE: {DATABASE_TYPE}")
    
    # 3. Check if caching should be enabled
    if REDIS_ENABLED == 'true':
        # Try to connect to Redis
        if redis_connection_successful():
            repository = CachedRepository(repository)
        else:
            # Redis not available, continue without cache
            print("Warning: Redis not available, running without cache")
    
    return repository
```

## ⚠️ Critical Rules for Agents

### NEVER DO:
1. **Hardcode repository implementations**
   ```python
   # ❌ WRONG - Never do this
   repository = SupabaseTaskRepository()
   
   # ✅ CORRECT - Always use factory
   repository = RepositoryFactory.get_task_repository()
   ```

2. **Assume cache is always available**
   ```python
   # ❌ WRONG - Will crash if Redis is down
   redis_client.set(key, value)
   
   # ✅ CORRECT - Check if cache is enabled
   if cache_strategy.is_enabled:
       cache_strategy.set(key, value)
   ```

3. **Mix architectural layers**
   ```python
   # ❌ WRONG - Controller directly accessing repository
   class Controller:
       def handle(self):
           repo = TaskRepository()  # Direct repository access
   
   # ✅ CORRECT - Controller uses facade
   class Controller:
       def handle(self):
           self.facade.execute()  # Delegate to facade
   ```

4. **Forget cache invalidation**
   ```python
   # ❌ WRONG - Update without invalidating cache
   def update_task(self, task):
       self.db.update(task)
   
   # ✅ CORRECT - Always invalidate after updates
   def update_task(self, task):
       self.db.update(task)
       self.cache.invalidate(f"task:{task.id}")
   ```

### ALWAYS DO:
1. **Follow the layer hierarchy**
   - Controller → Facade → Use Case → Repository Factory → Repository

2. **Use environment variables for configuration**
   - Never hardcode database connections or cache settings

3. **Handle cache failures gracefully**
   - System must work even if Redis is unavailable

4. **Invalidate cache on data changes**
   - CREATE, UPDATE, DELETE must invalidate relevant cache entries

5. **Use factory pattern for repository selection**
   - Let RepositoryFactory decide which implementation to use

## 📊 Implementation Checklist

When implementing a new feature, follow this checklist:

- [ ] Create Controller in `/interface/controllers/`
- [ ] Create Facade in `/application/facades/`
- [ ] Create Use Case in `/application/use_cases/`
- [ ] Define Repository Interface in `/domain/repositories/`
- [ ] Implement SQLite Repository in `/infrastructure/repositories/sqlite/`
- [ ] Implement Supabase Repository in `/infrastructure/repositories/supabase/`
- [ ] Add to RepositoryFactory in `/infrastructure/repositories/repository_factory.py`
- [ ] Implement Cache Strategy in `/infrastructure/cache/`
- [ ] Add Cache Invalidation logic
- [ ] Configure environment variables
- [ ] Write tests using SQLite repository
- [ ] Test production with Supabase
- [ ] Test with Redis enabled and disabled

## 🚀 Quick Implementation Example

Here's a complete example of implementing a new "Project" feature:

```python
# 1. Controller (interface layer)
# src/fastmcp/task_management/interface/controllers/project_mcp_controller.py
class ProjectMCPController:
    def __init__(self):
        self.facade = ProjectApplicationFacade()
    
    def manage_project(self, action: str, **params):
        if action == "create":
            return self.facade.create_project(params)

# 2. Facade (application layer)
# src/fastmcp/task_management/application/facades/project_application_facade.py
class ProjectApplicationFacade:
    def __init__(self):
        self.repo_factory = RepositoryFactory()
    
    def create_project(self, request):
        repository = self.repo_factory.get_project_repository()
        use_case = CreateProjectUseCase(repository)
        return use_case.execute(request)

# 3. Repository Factory
# src/fastmcp/task_management/infrastructure/repositories/repository_factory.py
class RepositoryFactory:
    @staticmethod
    def get_project_repository():
        env = os.getenv('ENVIRONMENT', 'production')
        
        if env == 'test':
            base_repo = SQLiteProjectRepository()
        else:
            base_repo = SupabaseProjectRepository()
        
        if os.getenv('REDIS_ENABLED', 'true') == 'true':
            return CachedProjectRepository(base_repo)
        return base_repo

# 4. SQLite Repository (testing)
# src/fastmcp/task_management/infrastructure/repositories/sqlite/sqlite_project_repository.py
class SQLiteProjectRepository(ProjectRepository):
    def create_project(self, project):
        # SQLite implementation
        pass

# 5. Supabase Repository (production)
# src/fastmcp/task_management/infrastructure/repositories/supabase/supabase_project_repository.py
class SupabaseProjectRepository(ProjectRepository):
    def create_project(self, project):
        # Supabase implementation
        pass

# 6. Cached Repository Wrapper
# src/fastmcp/task_management/infrastructure/repositories/cached_project_repository.py
class CachedProjectRepository(ProjectRepository):
    def __init__(self, base_repo):
        self.base_repo = base_repo
        self.cache = CacheStrategy()
    
    def create_project(self, project):
        result = self.base_repo.create_project(project)
        self.cache.invalidate("projects:*")
        return result
```

## 📈 Performance Considerations

### With Redis Enabled (REDIS_ENABLED=true)
- **Read Performance**: ~1-5ms (cache hit), ~50-100ms (cache miss)
- **Write Performance**: ~50-100ms + cache invalidation overhead
- **Memory Usage**: Higher due to Redis cache
- **Best For**: High read/write ratio applications

### Without Redis (REDIS_ENABLED=false)
- **Read Performance**: ~50-100ms (direct database)
- **Write Performance**: ~50-100ms (no cache overhead)
- **Memory Usage**: Lower, no cache storage
- **Best For**: Low traffic or write-heavy applications

### Test Mode (ENVIRONMENT=test)
- **Database**: SQLite (local file)
- **Cache**: Always disabled
- **Performance**: Fast for testing
- **Isolation**: Complete test isolation

## 🔍 Debugging Guide

### How to verify correct repository is being used:

```python
# Add logging to RepositoryFactory
import logging
logger = logging.getLogger(__name__)

class RepositoryFactory:
    @staticmethod
    def get_task_repository():
        env = os.getenv('ENVIRONMENT', 'production')
        db_type = os.getenv('DATABASE_TYPE', 'supabase')
        redis_enabled = os.getenv('REDIS_ENABLED', 'true')
        
        logger.info(f"Repository selection: ENV={env}, DB={db_type}, REDIS={redis_enabled}")
        
        # ... repository selection logic ...
        
        logger.info(f"Selected repository: {repository.__class__.__name__}")
        return repository
```

### Common Issues and Solutions:

1. **Cache not invalidating**
   - Check REDIS_ENABLED environment variable
   - Verify Redis connection is successful
   - Ensure invalidation code is not commented out

2. **Wrong database being used**
   - Check ENVIRONMENT variable
   - Verify DATABASE_TYPE is set correctly
   - Check RepositoryFactory logic

3. **Tests using production database**
   - Ensure ENVIRONMENT=test for test runs
   - Check test configuration files

## 🎓 Summary for AI Agents

**Remember these key points:**

1. **Architecture Flow**: Controller → Facade → Use Case → Repository Factory → Repository → Database/Cache
2. **Repository Selection**: Factory pattern decides based on environment
3. **Cache Management**: Optional Redis layer with graceful fallback
4. **Test Isolation**: SQLite for tests, Supabase for production
5. **Cache Invalidation**: MUST invalidate on CREATE, UPDATE, DELETE

**Your implementation should:**
- ✅ Use RepositoryFactory for all repository creation
- ✅ Check cache availability before using
- ✅ Invalidate cache after data changes
- ✅ Follow the architectural layers strictly
- ✅ Handle cache failures gracefully

**Never:**
- ❌ Hardcode repository implementations
- ❌ Skip architectural layers
- ❌ Assume cache is always available
- ❌ Forget cache invalidation
- ❌ Mix test and production databases

This architecture ensures clean separation, testability, flexibility, and performance optimization while maintaining simplicity and reliability.