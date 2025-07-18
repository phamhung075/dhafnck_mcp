# Testing Guide

## Overview

This guide covers testing strategies, patterns, and best practices for the DhafnckMCP system. The testing approach follows Test-Driven Development (TDD) principles with comprehensive coverage across unit, integration, and end-to-end tests.

## Testing Architecture

### Test Structure
```
src/tests/
├── unit/                    # Unit tests for individual components
│   ├── domain/             # Domain logic tests
│   ├── application/        # Application service tests
│   └── infrastructure/     # Infrastructure layer tests
├── integration/            # Integration tests
│   ├── database/          # Database integration tests
│   ├── mcp_tools/         # MCP tool integration tests
│   └── facades/           # Facade integration tests
├── e2e/                   # End-to-end workflow tests
│   ├── task_workflows/    # Complete task workflows
│   ├── project_workflows/ # Project management workflows
│   └── agent_workflows/   # Agent orchestration workflows
├── performance/           # Performance and load tests
└── fixtures/             # Test data and utilities
```

### Test Categories

#### 1. Unit Tests
**Purpose**: Test individual components in isolation
- Domain entities and value objects
- Domain services
- Repository interfaces
- Utility functions

#### 2. Integration Tests  
**Purpose**: Test component interactions
- Database operations
- MCP tool integrations
- Service layer interactions
- Cache behavior

#### 3. End-to-End Tests
**Purpose**: Test complete workflows
- Task creation to completion
- Project setup and management
- Agent assignment and execution
- Context inheritance and delegation

#### 4. Performance Tests
**Purpose**: Validate system performance
- Load testing for concurrent operations
- Memory usage and leak detection
- Database query performance
- Cache efficiency

## Testing Framework

### Core Technologies
- **pytest**: Primary testing framework
- **pytest-asyncio**: Async test support
- **pytest-mock**: Mocking and patching
- **pytest-cov**: Coverage reporting
- **factory_boy**: Test data factories
- **SQLAlchemy**: Database test utilities

### Test Configuration
```python
# conftest.py
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from fastmcp.task_management.infrastructure.database import get_session

@pytest.fixture
async def test_db():
    """Test database with isolated transactions"""
    engine = create_async_engine(
        "sqlite+aiosqlite:///test_dhafnck_mcp.db",
        echo=False
    )
    async with engine.begin() as conn:
        # Create tables
        await conn.run_sync(Base.metadata.create_all)
    
    async with AsyncSession(engine) as session:
        yield session
    
    # Cleanup
    await engine.dispose()

@pytest.fixture
def mock_context_facade():
    """Mock hierarchical context facade"""
    facade = Mock(spec=HierarchicalContextFacade)
    facade.resolve_context.return_value = ResolvedContext(
        context_id="test-context",
        level="task", 
        data=ContextData(title="Test Task"),
        inheritance_chain=["global", "project", "task"],
        dependency_hash="test-hash",
        resolved_at=datetime.utcnow(),
        cache_status="miss"
    )
    return facade
```

## Unit Testing Patterns

### Domain Entity Testing
```python
# test_task_entity.py
class TestTaskEntity:
    """Test task domain entity"""
    
    def test_task_creation(self):
        """Test task creation with valid data"""
        # Arrange
        task_data = {
            "title": "Test task",
            "description": "Test description",
            "git_branch_id": "branch-uuid-123"
        }
        
        # Act
        task = Task.create(**task_data)
        
        # Assert
        assert task.title == "Test task"
        assert task.status == TaskStatus.TODO
        assert task.id is not None
    
    def test_task_status_transition(self):
        """Test valid status transitions"""
        # Arrange
        task = Task.create("Test task", "branch-uuid")
        
        # Act & Assert
        task.start()
        assert task.status == TaskStatus.IN_PROGRESS
        
        task.complete(CompletionSummary("Task completed"))
        assert task.status == TaskStatus.DONE
    
    def test_invalid_status_transition(self):
        """Test invalid status transitions raise errors"""
        # Arrange
        task = Task.create("Test task", "branch-uuid")
        
        # Act & Assert
        with pytest.raises(InvalidStatusTransitionError):
            task.complete(CompletionSummary("Invalid transition"))
```

### Domain Service Testing
```python
# test_task_completion_service.py
class TestTaskCompletionService:
    """Test task completion domain service"""
    
    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_context_facade):
        """Test successful task completion"""
        # Arrange
        task = Task.create("Test task", "branch-uuid")
        task.start()
        completion_summary = CompletionSummary("Task completed successfully")
        service = TaskCompletionService()
        
        # Act
        result = await service.complete_task(
            task, completion_summary, mock_context_facade
        )
        
        # Assert
        assert result.is_success
        assert task.status == TaskStatus.DONE
        assert task.completion_summary == completion_summary
        mock_context_facade.resolve_context.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_complete_task_without_context_fails(self, mock_context_facade):
        """Test task completion fails without context"""
        # Arrange
        task = Task.create("Test task", "branch-uuid")
        task.start()
        mock_context_facade.resolve_context.side_effect = ContextNotFoundError()
        service = TaskCompletionService()
        
        # Act & Assert
        with pytest.raises(TaskCompletionError) as exc_info:
            await service.complete_task(
                task, CompletionSummary("Test"), mock_context_facade
            )
        
        assert "context must be created first" in str(exc_info.value)
```

### Repository Testing
```python
# test_task_repository.py  
class TestTaskRepository:
    """Test task repository implementation"""
    
    @pytest.mark.asyncio
    async def test_save_and_find_task(self, test_db):
        """Test saving and retrieving tasks"""
        # Arrange
        repo = SQLAlchemyTaskRepository(test_db)
        task = Task.create("Test task", "branch-uuid-123")
        
        # Act
        await repo.save(task)
        found_task = await repo.find_by_id(task.id)
        
        # Assert
        assert found_task is not None
        assert found_task.id == task.id
        assert found_task.title == task.title
    
    @pytest.mark.asyncio
    async def test_find_by_status(self, test_db):
        """Test finding tasks by status"""
        # Arrange
        repo = SQLAlchemyTaskRepository(test_db)
        task1 = Task.create("Task 1", "branch-uuid")
        task2 = Task.create("Task 2", "branch-uuid")
        task1.start()
        
        await repo.save(task1)
        await repo.save(task2)
        
        # Act
        in_progress_tasks = await repo.find_by_status(TaskStatus.IN_PROGRESS)
        todo_tasks = await repo.find_by_status(TaskStatus.TODO)
        
        # Assert
        assert len(in_progress_tasks) == 1
        assert len(todo_tasks) == 1
        assert in_progress_tasks[0].id == task1.id
```

## Integration Testing Patterns

### MCP Tool Integration Testing
```python
# test_task_mcp_controller.py
class TestTaskMCPController:
    """Test MCP controller integration"""
    
    @pytest.mark.asyncio
    async def test_create_task_integration(self, test_db, mock_context_facade):
        """Test complete task creation flow"""
        # Arrange
        controller = TaskMCPController(test_db)
        request_data = {
            "action": "create",
            "git_branch_id": "branch-uuid-123",
            "title": "Integration test task",
            "description": "Test task creation"
        }
        
        # Act
        response = await controller.handle_request(request_data)
        
        # Assert
        assert response["success"] is True
        assert "task_id" in response
        assert response["task"]["title"] == "Integration test task"
    
    @pytest.mark.asyncio
    async def test_complete_task_with_context_validation(self, test_db):
        """Test task completion with context validation"""
        # Arrange
        controller = TaskMCPController(test_db)
        
        # Create task
        create_response = await controller.handle_request({
            "action": "create",
            "git_branch_id": "branch-uuid-123",
            "title": "Test task"
        })
        task_id = create_response["task_id"]
        
        # Update status
        await controller.handle_request({
            "action": "update",
            "task_id": task_id,
            "status": "in_progress"
        })
        
        # Act - try to complete without context (should fail)
        complete_response = await controller.handle_request({
            "action": "complete",
            "task_id": task_id,
            "completion_summary": "Test completion"
        })
        
        # Assert
        assert complete_response["success"] is False
        assert "context must be created first" in complete_response["error"]
```

### Database Integration Testing
```python
# test_database_integration.py
class TestDatabaseIntegration:
    """Test database operations and constraints"""
    
    @pytest.mark.asyncio
    async def test_foreign_key_constraints(self, test_db):
        """Test foreign key constraint enforcement"""
        # Arrange
        task_repo = SQLAlchemyTaskRepository(test_db)
        
        # Act & Assert - should fail with invalid branch_id
        with pytest.raises(IntegrityError):
            task = Task.create("Test task", "invalid-branch-uuid")
            await task_repo.save(task)
    
    @pytest.mark.asyncio
    async def test_cascade_deletion(self, test_db):
        """Test cascade deletion behavior"""
        # Arrange
        project_repo = SQLAlchemyProjectRepository(test_db)
        branch_repo = SQLAlchemyGitBranchRepository(test_db)
        task_repo = SQLAlchemyTaskRepository(test_db)
        
        # Create project → branch → task hierarchy
        project = Project.create("Test Project")
        await project_repo.save(project)
        
        branch = GitBranch.create("feature/test", project.id)
        await branch_repo.save(branch)
        
        task = Task.create("Test Task", branch.id)
        await task_repo.save(task)
        
        # Act - delete project
        await project_repo.delete(project.id)
        
        # Assert - task and branch should be deleted
        assert await task_repo.find_by_id(task.id) is None
        assert await branch_repo.find_by_id(branch.id) is None
```

### Context System Integration Testing
```python
# test_context_integration.py
class TestContextSystemIntegration:
    """Test hierarchical context system integration"""
    
    @pytest.mark.asyncio
    async def test_context_inheritance_chain(self, test_db):
        """Test complete inheritance chain resolution"""
        # Arrange
        facade_factory = HierarchicalContextFacadeFactory()
        facade = facade_factory.create_facade(
            user_id="test-user",
            project_id="project-uuid",
            git_branch_id="branch-uuid",
            db_session=test_db
        )
        
        # Create context hierarchy
        await facade.create_context("global", "global_singleton", {
            "coding_standards": {"python": "black"}
        })
        await facade.create_context("project", "project-uuid", {
            "team_conventions": {"testing": "pytest"}
        })
        await facade.create_context("task", "task-uuid", {
            "task_progress": "50%"
        })
        
        # Act
        resolved = await facade.resolve_context("task", "task-uuid")
        
        # Assert
        assert resolved.data.metadata["coding_standards"]["python"] == "black"
        assert resolved.data.metadata["team_conventions"]["testing"] == "pytest"
        assert resolved.data.metadata["task_progress"] == "50%"
        assert resolved.inheritance_chain == ["global", "project", "task"]
```

## End-to-End Testing Patterns

### Complete Workflow Testing
```python
# test_e2e_task_workflow.py
class TestTaskWorkflowE2E:
    """End-to-end task workflow testing"""
    
    @pytest.mark.asyncio
    async def test_complete_task_lifecycle(self, test_db):
        """Test complete task lifecycle from creation to completion"""
        # Arrange - setup project and branch
        project_controller = ProjectMCPController(test_db)
        branch_controller = GitBranchMCPController(test_db)
        task_controller = TaskMCPController(test_db)
        context_controller = ContextMCPController(test_db)
        
        # Act 1: Create project
        project_response = await project_controller.handle_request({
            "action": "create",
            "name": "E2E Test Project",
            "description": "End-to-end testing project"
        })
        project_id = project_response["project"]["id"]
        
        # Act 2: Create branch
        branch_response = await branch_controller.handle_request({
            "action": "create",
            "project_id": project_id,
            "git_branch_name": "feature/e2e-test",
            "git_branch_description": "E2E test branch"
        })
        branch_id = branch_response["git_branch"]["id"]
        
        # Act 3: Create task
        task_response = await task_controller.handle_request({
            "action": "create",
            "git_branch_id": branch_id,
            "title": "E2E test task",
            "description": "Complete task workflow test"
        })
        task_id = task_response["task_id"]
        
        # Act 4: Update task status
        await task_controller.handle_request({
            "action": "update",
            "task_id": task_id,
            "status": "in_progress"
        })
        
        # Act 5: Update context
        await context_controller.handle_request({
            "action": "update",
            "task_id": task_id,
            "data_title": "Updated task title",
            "data_status": "in_progress"
        })
        
        # Act 6: Complete task
        completion_response = await task_controller.handle_request({
            "action": "complete",
            "task_id": task_id,
            "completion_summary": "E2E workflow completed successfully",
            "testing_notes": "All workflow steps validated"
        })
        
        # Assert
        assert completion_response["success"] is True
        
        # Verify final state
        final_task = await task_controller.handle_request({
            "action": "get",
            "task_id": task_id
        })
        assert final_task["task"]["status"] == "done"
        assert final_task["task"]["completion_summary"] == "E2E workflow completed successfully"
```

### Agent Workflow Testing
```python
# test_e2e_agent_workflow.py
class TestAgentWorkflowE2E:
    """End-to-end agent workflow testing"""
    
    @pytest.mark.asyncio
    async def test_agent_assignment_and_execution(self, test_db):
        """Test complete agent assignment and execution workflow"""
        # Arrange
        agent_controller = AgentMCPController(test_db)
        call_agent_controller = CallAgentController()
        
        # Act 1: Register agent
        register_response = await agent_controller.handle_request({
            "action": "register",
            "project_id": "project-uuid",
            "name": "test_coding_agent"
        })
        agent_id = register_response["agent"]["id"]
        
        # Act 2: Assign agent to branch
        await agent_controller.handle_request({
            "action": "assign",
            "project_id": "project-uuid",
            "agent_id": agent_id,
            "git_branch_id": "branch-uuid"
        })
        
        # Act 3: Call agent
        call_response = await call_agent_controller.handle_request({
            "name_agent": "@coding_agent"
        })
        
        # Assert
        assert call_response["success"] is True
        assert call_response["agent_info"]["name"] == "coding_agent"
```

## Performance Testing

### Load Testing
```python
# test_performance_load.py
class TestPerformanceLoad:
    """Performance and load testing"""
    
    @pytest.mark.asyncio
    async def test_concurrent_task_creation(self, test_db):
        """Test system performance under concurrent task creation"""
        import asyncio
        import time
        
        # Arrange
        controller = TaskMCPController(test_db)
        num_concurrent = 50
        
        async def create_task(index):
            return await controller.handle_request({
                "action": "create",
                "git_branch_id": "branch-uuid-123",
                "title": f"Load test task {index}",
                "description": f"Performance test task {index}"
            })
        
        # Act
        start_time = time.time()
        tasks = [create_task(i) for i in range(num_concurrent)]
        results = await asyncio.gather(*tasks)
        end_time = time.time()
        
        # Assert
        assert len(results) == num_concurrent
        assert all(result["success"] for result in results)
        
        # Performance assertion
        total_time = end_time - start_time
        assert total_time < 10.0  # Should complete within 10 seconds
        
        avg_time = total_time / num_concurrent
        assert avg_time < 0.2  # Average time per task should be < 200ms
    
    @pytest.mark.asyncio
    async def test_context_resolution_performance(self, test_db):
        """Test context resolution performance with inheritance"""
        # Arrange
        facade = create_test_facade(test_db)
        
        # Create deep inheritance hierarchy
        await facade.create_context("global", "global_singleton", {"global": "data"})
        await facade.create_context("project", "project-uuid", {"project": "data"})
        await facade.create_context("branch", "branch-uuid", {"branch": "data"})
        await facade.create_context("task", "task-uuid", {"task": "data"})
        
        # Act - measure resolution time
        start_time = time.time()
        for _ in range(100):
            await facade.resolve_context("task", "task-uuid")
        end_time = time.time()
        
        # Assert
        avg_resolution_time = (end_time - start_time) / 100
        assert avg_resolution_time < 0.01  # Should be < 10ms per resolution
```

### Memory Testing
```python
# test_performance_memory.py
class TestMemoryPerformance:
    """Memory usage and leak testing"""
    
    @pytest.mark.asyncio
    async def test_memory_usage_under_load(self, test_db):
        """Test memory usage under sustained load"""
        import psutil
        import gc
        
        # Arrange
        process = psutil.Process()
        controller = TaskMCPController(test_db)
        
        # Measure baseline memory
        gc.collect()
        baseline_memory = process.memory_info().rss
        
        # Act - create many tasks
        for i in range(1000):
            await controller.handle_request({
                "action": "create",
                "git_branch_id": "branch-uuid-123",
                "title": f"Memory test task {i}"
            })
            
            if i % 100 == 0:
                gc.collect()
        
        # Measure final memory
        gc.collect()
        final_memory = process.memory_info().rss
        
        # Assert - memory growth should be reasonable
        memory_growth = final_memory - baseline_memory
        memory_growth_mb = memory_growth / (1024 * 1024)
        
        assert memory_growth_mb < 100  # Should not grow more than 100MB
```

## Test Data Management

### Factories
```python
# test_factories.py
import factory
from factory.faker import Faker

class TaskFactory(factory.Factory):
    """Factory for creating test tasks"""
    class Meta:
        model = Task
    
    title = Faker('sentence', nb_words=4)
    description = Faker('text', max_nb_chars=200)
    git_branch_id = factory.LazyFunction(lambda: str(uuid.uuid4()))
    status = TaskStatus.TODO
    priority = "medium"

class ProjectFactory(factory.Factory):
    """Factory for creating test projects"""
    class Meta:
        model = Project
    
    name = Faker('company')
    description = Faker('catch_phrase')

# Usage in tests
def test_with_factory_data():
    task = TaskFactory()
    assert task.title is not None
    assert task.git_branch_id is not None
```

### Fixtures
```python
# test_fixtures.py
@pytest.fixture
async def sample_project(test_db):
    """Fixture providing a sample project"""
    project = Project.create("Test Project", "Sample project for testing")
    repo = SQLAlchemyProjectRepository(test_db)
    await repo.save(project)
    return project

@pytest.fixture
async def sample_task_hierarchy(test_db, sample_project):
    """Fixture providing complete task hierarchy"""
    # Create branch
    branch = GitBranch.create("feature/test", sample_project.id)
    branch_repo = SQLAlchemyGitBranchRepository(test_db)
    await branch_repo.save(branch)
    
    # Create task
    task = Task.create("Test Task", branch.id)
    task_repo = SQLAlchemyTaskRepository(test_db)
    await task_repo.save(task)
    
    return {
        "project": sample_project,
        "branch": branch,
        "task": task
    }
```

## Coverage and Reporting

### Coverage Configuration
```ini
# .coveragerc
[run]
source = src/fastmcp/task_management
omit = 
    */tests/*
    */migrations/*
    */conftest.py

[report]
exclude_lines =
    pragma: no cover
    def __repr__
    raise AssertionError
    raise NotImplementedError
```

### Running Tests with Coverage
```bash
# Run all tests with coverage
pytest --cov=src/fastmcp/task_management --cov-report=html --cov-report=term

# Run specific test categories
pytest src/tests/unit/ -v
pytest src/tests/integration/ -v
pytest src/tests/e2e/ -v

# Run with markers
pytest -m "not performance" -v  # Skip performance tests
pytest -m "database" -v         # Run only database tests
```

### Test Markers
```python
# pytest.ini
[tool:pytest]
markers =
    unit: Unit tests
    integration: Integration tests
    e2e: End-to-end tests
    performance: Performance tests
    database: Database-related tests
    slow: Tests that take longer than 1 second
```

## Continuous Integration

### GitHub Actions Configuration
```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:13
        env:
          POSTGRES_PASSWORD: test
          POSTGRES_DB: test_dhafnck_mcp
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v2
    
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: 3.11
    
    - name: Install dependencies
      run: |
        pip install -r requirements-test.txt
    
    - name: Run tests
      run: |
        pytest --cov=src/fastmcp/task_management \
               --cov-report=xml \
               --cov-report=term
    
    - name: Upload coverage
      uses: codecov/codecov-action@v1
      with:
        file: ./coverage.xml
```

## Best Practices

### 1. Test Organization
- **One class per test file** for complex entities
- **Group related tests** in test classes
- **Use descriptive test names** that explain the scenario
- **Follow AAA pattern** (Arrange, Act, Assert)

### 2. Test Isolation
- **Use fresh database** for each test
- **Mock external dependencies** properly
- **Clean up resources** in fixtures
- **Avoid test interdependencies**

### 3. Data Management
- **Use factories** for test data creation
- **Create minimal data** needed for tests
- **Use realistic data** that matches production patterns
- **Avoid hardcoded values** where possible

### 4. Performance Considerations
- **Mark slow tests** appropriately
- **Use database transactions** for speed
- **Mock expensive operations** in unit tests
- **Profile test execution** regularly

### 5. Maintainability
- **Keep tests simple** and focused
- **Refactor test code** like production code
- **Update tests** when requirements change
- **Document complex test scenarios**

## Debugging Tests

### Common Issues and Solutions

#### Test Database Issues
```python
# Issue: Database state leaking between tests
# Solution: Use transaction rollback
@pytest.fixture
async def test_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        async with AsyncSession(bind=conn) as session:
            transaction = await session.begin()
            yield session
            await transaction.rollback()
```

#### Async Test Issues
```python
# Issue: Async context not properly awaited
# Solution: Use pytest-asyncio properly
@pytest.mark.asyncio
async def test_async_operation():
    result = await async_function()
    assert result is not None
```

#### Mock Issues
```python
# Issue: Mocks not behaving as expected
# Solution: Use proper mock configuration
@pytest.fixture
def mock_service():
    mock = Mock(spec=TaskCompletionService)
    mock.complete_task.return_value = TaskCompletionResult(success=True)
    return mock
```

### Test Debugging Commands
```bash
# Run single test with verbose output
pytest tests/unit/test_task_entity.py::TestTaskEntity::test_task_creation -v -s

# Run tests with debugging
pytest --pdb tests/unit/test_task_entity.py

# Run tests with coverage and HTML report
pytest --cov=src --cov-report=html tests/

# Profile test performance
pytest --durations=10 tests/
```

## Conclusion

This testing guide provides comprehensive patterns and practices for testing the DhafnckMCP system. The approach ensures:

- **High Quality**: Comprehensive test coverage across all system layers
- **Maintainability**: Clear testing patterns and well-organized test code
- **Performance**: Efficient test execution and performance validation
- **Reliability**: Consistent test results and proper isolation
- **Documentation**: Tests serve as living documentation of system behavior

Regular testing practices, combined with proper CI/CD integration, ensure the system remains robust and reliable as it evolves.