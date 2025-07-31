# PostgreSQL Test Failure Fixes

This document provides solutions for common test failures when using PostgreSQL.

## Common Issues and Solutions

### 1. Duplicate Key Violations

**Error**: `sqlalchemy.exc.IntegrityError: (psycopg2.errors.UniqueViolation) duplicate key value violates unique constraint`

**Cause**: PostgreSQL persists data between test runs, unlike SQLite which uses in-memory databases.

**Solutions**:

#### Option A: Use the `postgresql_clean_db` fixture
```python
from tests.conftest_postgresql_fix import postgresql_clean_db

def test_something(postgresql_clean_db):
    # Test has clean database state
    pass
```

#### Option B: Use the `postgresql_transactional_db` fixture for complete isolation
```python
from tests.conftest_postgresql_fix import postgresql_transactional_db

def test_something(postgresql_transactional_db):
    session = postgresql_transactional_db
    # All changes will be rolled back after test
```

#### Option C: Use ON CONFLICT clauses
```python
session.execute(text("""
    INSERT INTO global_contexts (id, data, ...) 
    VALUES ('test-id', '{}', ...)
    ON CONFLICT (id) DO UPDATE SET data = EXCLUDED.data
"""))
```

### 2. Async Function Errors

**Error**: `Failed: async def functions are not natively supported`

**Cause**: pytest doesn't run async functions without proper setup.

**Solution**: Use `pytest-asyncio` and mark async tests:
```python
import pytest

@pytest.mark.asyncio
async def test_async_function():
    result = await some_async_function()
    assert result is not None
```

Or convert to sync tests if async isn't needed:
```python
def test_sync_function():
    # Use sync versions of functions
    result = some_sync_function()
    assert result is not None
```

### 3. Missing Import Errors

**Error**: `ModuleNotFoundError: No module named 'src'`

**Cause**: Import paths are incorrect.

**Solution**: Use absolute imports from `fastmcp`:
```python
# Wrong
from src.task_management.domain.entities import Task

# Correct
from fastmcp.task_management.domain.entities import Task
```

### 4. NameError: `_initialize_test_database` not defined

**Error**: `NameError: name '_initialize_test_database' is not defined`

**Cause**: Tests trying to use SQLite initialization function with PostgreSQL.

**Solution**: Remove SQLite-specific initialization:
```python
# Remove this line
_initialize_test_database(test_db_path)

# The PostgreSQL fixture handles initialization automatically
```

### 5. AttributeError in Use Case Tests

**Error**: `AttributeError: <module '...' has no attribute '...'>`

**Cause**: Tests expecting class instances but getting modules.

**Solution**: Import and instantiate the class:
```python
# Wrong
from fastmcp.task_management.application.use_cases import update_task
update_task._sync_task_context_after_update()

# Correct
from fastmcp.task_management.application.use_cases.update_task import UpdateTaskUseCase
use_case = UpdateTaskUseCase(repo1, repo2, ...)
use_case._sync_task_context_after_update()
```

## Best Practices for PostgreSQL Tests

### 1. Test Isolation

Always use one of these approaches:

1. **Clean Database Fixture** (Recommended for most tests):
   ```python
   def test_something(postgresql_clean_db):
       # Database is cleaned before and after test
   ```

2. **Transactional Fixture** (For tests needing complete isolation):
   ```python
   def test_something(postgresql_transactional_db):
       session = postgresql_transactional_db
       # Everything is rolled back after test
   ```

3. **Manual Cleanup**:
   ```python
   def test_something():
       try:
           # Test code
       finally:
           # Clean up test data
           session.execute(text("DELETE FROM table WHERE id LIKE 'test-%'"))
   ```

### 2. Handling Test Data

1. **Use unique IDs for test data**:
   ```python
   import uuid
   test_id = f'test-{uuid.uuid4()}'
   ```

2. **Clean up in reverse dependency order**:
   ```python
   # Delete in this order to avoid foreign key violations
   session.execute(text("DELETE FROM subtasks WHERE ..."))
   session.execute(text("DELETE FROM tasks WHERE ..."))
   session.execute(text("DELETE FROM projects WHERE ..."))
   ```

3. **Use CASCADE when appropriate**:
   ```sql
   TRUNCATE TABLE tasks CASCADE;
   ```

### 3. Performance Optimization

1. **Use session-scoped fixtures for read-only tests**:
   ```python
   @pytest.fixture(scope="session")
   def shared_test_data():
       # Create data once for all read-only tests
   ```

2. **Batch operations**:
   ```python
   # Instead of multiple inserts
   session.execute(text("""
       INSERT INTO table (col1, col2) VALUES 
       ('val1', 'val2'),
       ('val3', 'val4'),
       ('val5', 'val6')
   """))
   ```

### 4. Debugging Test Failures

1. **Check for leftover data**:
   ```python
   result = session.execute(text("""
       SELECT table_name, count(*) 
       FROM information_schema.tables t
       JOIN (
           SELECT 'projects' as tbl, COUNT(*) as cnt FROM projects
           UNION ALL
           SELECT 'tasks', COUNT(*) FROM tasks
           -- etc
       ) counts ON t.table_name = counts.tbl
   """))
   ```

2. **Enable SQL logging**:
   ```python
   import logging
   logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)
   ```

3. **Use savepoints for debugging**:
   ```python
   savepoint = session.begin_nested()
   try:
       # Test operations
       savepoint.commit()
   except:
       savepoint.rollback()
       # Examine state
   ```

## Migration Checklist

When migrating tests from SQLite to PostgreSQL:

- [ ] Replace `_initialize_test_database` calls
- [ ] Add ON CONFLICT clauses for INSERT statements
- [ ] Use PostgreSQL-specific fixtures
- [ ] Fix import paths (remove 'src.' prefix)
- [ ] Add `@pytest.mark.asyncio` for async tests
- [ ] Handle CASCADE deletes properly
- [ ] Test cleanup in reverse dependency order

## Example: Fixing a Typical Test

### Before (SQLite):
```python
def test_create_project():
    test_db = Path("test.db")
    _initialize_test_database(test_db)
    
    session = get_session()
    project = Project(id="test-1", name="Test")
    session.add(project)
    session.commit()
```

### After (PostgreSQL):
```python
from tests.conftest_postgresql_fix import postgresql_clean_db

def test_create_project(postgresql_clean_db):
    from fastmcp.task_management.infrastructure.database.database_config import get_db_config
    
    db_config = get_db_config()
    with db_config.get_session() as session:
        project = Project(id=f"test-{uuid.uuid4()}", name="Test")
        session.add(project)
        session.commit()
```