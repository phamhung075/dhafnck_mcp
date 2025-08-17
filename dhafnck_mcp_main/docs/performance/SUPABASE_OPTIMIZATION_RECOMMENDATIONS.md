# Supabase Performance Optimization Recommendations

## Critical Issues Found

### 1. Timezone Query Overhead (24.5% of total query time)
**Problem**: `SELECT name FROM pg_timezone_names` is called 85 times, consuming 12.3 seconds
**Root Cause**: Timezone validation happening on every authentication/connection
**Solution**:
```python
# Cache timezone data at application startup
class TimezoneCache:
    _timezones = None
    
    @classmethod
    def get_timezones(cls):
        if cls._timezones is None:
            # Load once at startup
            cls._timezones = load_timezones()
        return cls._timezones
```

### 2. Connection Pool Inefficiency (8.7% of query time)
**Problem**: pgbouncer authentication called 15,701 times
**Solution**:
- Increase connection pool minimum size
- Implement connection keepalive
- Use prepared statements

### 3. Schema Introspection Overhead (11.6% combined)
**Problem**: PostgREST schema cache queries are expensive and frequent
**Solution**:
- Increase PostgREST schema cache TTL
- Implement application-level schema caching
- Consider using direct SQL instead of PostgREST for hot paths

### 4. N+1 Query Pattern in Projects (6.5%)
**Problem**: Loading projects with all git branches using LEFT OUTER JOIN
**Current Query Pattern**:
```sql
SELECT projects.*, project_git_branchs_1.* 
FROM projects 
LEFT OUTER JOIN project_git_branchs AS project_git_branchs_1 
ON projects.id = project_git_branchs_1.project_id
```

**Optimized Solution**:
```python
# Use separate queries with batching
def get_projects_optimized():
    # 1. Get projects
    projects = session.query(Project).all()
    project_ids = [p.id for p in projects]
    
    # 2. Get branches in single query
    branches = session.query(GitBranch).filter(
        GitBranch.project_id.in_(project_ids)
    ).all()
    
    # 3. Group branches by project
    branches_by_project = defaultdict(list)
    for branch in branches:
        branches_by_project[branch.project_id].append(branch)
    
    # 4. Attach to projects
    for project in projects:
        project.branches = branches_by_project.get(project.id, [])
    
    return projects
```

## Implementation Priority

### Phase 1: Quick Wins (1-2 days)
1. **Cache timezone data** - Eliminate 24.5% of query time
2. **Increase connection pool size** - Reduce authentication overhead
3. **Add query result caching** for frequently accessed data

### Phase 2: Query Optimization (3-5 days)
1. **Refactor N+1 queries** to use batch loading
2. **Create materialized views** for complex aggregations
3. **Add missing indexes** based on query patterns

### Phase 3: Architecture Changes (1 week)
1. **Implement Redis caching layer** for frequently accessed data
2. **Use prepared statements** for all repeated queries
3. **Consider GraphQL DataLoader pattern** for relationship loading

## Specific Code Changes

### 1. Connection Manager Enhancement
```python
# dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/database/connection_manager.py

class ConnectionManager:
    def __init__(self):
        # Increase pool size for Supabase
        self._engine = create_engine(
            database_url,
            pool_size=20,  # Increased from 15
            max_overflow=30,  # Increased from 25
            pool_pre_ping=True,  # Verify connections
            pool_recycle=3600,  # Recycle connections hourly
            connect_args={
                "keepalives": 1,
                "keepalives_idle": 30,
                "keepalives_interval": 10,
                "keepalives_count": 5,
                "prepare_threshold": 5,  # Use prepared statements
            }
        )
```

### 2. Query Result Caching
```python
# New file: dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/cache/query_cache.py

from functools import lru_cache
from datetime import datetime, timedelta
import hashlib
import json

class QueryCache:
    def __init__(self, ttl_seconds=60):
        self.ttl = ttl_seconds
        self._cache = {}
    
    def get_or_fetch(self, query_key, fetch_func):
        # Create cache key
        cache_key = hashlib.md5(
            json.dumps(query_key, sort_keys=True).encode()
        ).hexdigest()
        
        # Check cache
        if cache_key in self._cache:
            result, timestamp = self._cache[cache_key]
            if datetime.now() - timestamp < timedelta(seconds=self.ttl):
                return result
        
        # Fetch and cache
        result = fetch_func()
        self._cache[cache_key] = (result, datetime.now())
        return result
```

### 3. Optimized Task Repository
```python
# Update: dhafnck_mcp_main/src/fastmcp/task_management/infrastructure/repositories/orm/supabase_optimized_repository.py

class SupabaseOptimizedRepository(BaseORMRepository):
    def __init__(self):
        super().__init__()
        self.query_cache = QueryCache(ttl_seconds=30)
        self._timezone_cache = None
    
    def list_tasks_with_counts_cached(self, git_branch_id, limit=50, offset=0):
        cache_key = {
            'method': 'list_tasks_with_counts',
            'git_branch_id': git_branch_id,
            'limit': limit,
            'offset': offset
        }
        
        return self.query_cache.get_or_fetch(
            cache_key,
            lambda: self._list_tasks_with_counts_internal(
                git_branch_id, limit, offset
            )
        )
```

## Monitoring Improvements

### Add Performance Metrics
```python
import time
from contextlib import contextmanager

@contextmanager
def query_timer(operation_name):
    start = time.time()
    try:
        yield
    finally:
        duration = time.time() - start
        if duration > 0.5:  # Log slow queries
            logger.warning(
                f"Slow query detected: {operation_name} took {duration:.2f}s"
            )
```

## Expected Results

After implementing these optimizations:

| Metric | Current | Target | Improvement |
|--------|---------|--------|-------------|
| Average Response Time | 200-300ms | 50-100ms | 75% reduction |
| Timezone Query Time | 12.3s | ~0s (cached) | 100% reduction |
| Connection Pool Efficiency | 15,701 auth calls | <1,000 | 93% reduction |
| N+1 Query Impact | 17,724 calls | <100 | 99% reduction |

## Testing Strategy

1. **Load Testing**
   ```bash
   # Use Apache Bench to test endpoints
   ab -n 1000 -c 10 http://localhost:8000/api/tasks/summaries
   ```

2. **Query Monitoring**
   ```sql
   -- Monitor query performance in Supabase
   SELECT 
     query,
     calls,
     total_time,
     mean_time,
     max_time
   FROM pg_stat_statements
   WHERE query NOT LIKE '%pg_stat%'
   ORDER BY total_time DESC
   LIMIT 20;
   ```

3. **Connection Pool Monitoring**
   ```sql
   -- Check connection pool stats
   SELECT 
     state,
     count(*)
   FROM pg_stat_activity
   GROUP BY state;
   ```

## Next Steps

1. **Immediate**: Implement timezone caching (24.5% improvement)
2. **This Week**: Optimize connection pooling and add query caching
3. **Next Sprint**: Refactor N+1 queries and add Redis caching
4. **Long Term**: Consider read replicas for heavy read operations

## Conclusion

The main bottlenecks are:
1. Repeated timezone queries (easily cacheable)
2. Inefficient connection pooling
3. N+1 query patterns
4. Lack of query result caching

Implementing these optimizations should reduce response times by 75-80% and significantly reduce database load.