# Git Branch Test Fixes - 2025-08-30

## Issues Identified

### 1. UUID Format Issues in Tests
**Problem**: Tests were using invalid string IDs like "test-branch-id" instead of proper UUIDs.
**Impact**: PostgreSQL database rejects invalid UUID format causing tests to fail.
**Resolution**: Updated test fixtures to use valid UUID format (e.g., "550e8400-e29b-41d4-a716-446655440001")

### 2. Repository Factory Not Properly Mocked
**Problem**: The facade's `_find_git_branch_by_id` method creates a real repository connection using RepositoryFactory.get_git_branch_repository() which tries to connect to the actual database.
**Impact**: Unit tests are not isolated and fail when database is not available or configured differently.
**Resolution**: Tests need to mock the RepositoryFactory at a deeper level.

### 3. Test Assertions Incorrect for Not Found Case
**Problem**: Test expected success=True for a not-found case, but the actual implementation returns success=False.
**Impact**: Test fails due to incorrect expectations.
**Resolution**: Fixed assertion to expect success=False and check for error message.

## Code Changes Applied

### 1. Fixed UUID Format in Test Fixtures
```python
# Before
git_branch.id = "test-branch-id"
project.id = "test-project-id"

# After
git_branch.id = "550e8400-e29b-41d4-a716-446655440001"
project.id = "550e8400-e29b-41d4-a716-446655440000"
```

### 2. Fixed Test Assertions
```python
# Before (test_find_git_branch_by_id_not_found)
assert result["success"] is True
assert result["git_branch"]["id"] == "unknown-branch-id"

# After
assert result["success"] is False
assert "not found" in result["error"].lower()
```

## Remaining Issues

### 1. Repository Factory Mocking
The test `test_find_git_branch_by_id_in_memory` needs proper mocking of the RepositoryFactory. The current approach doesn't work because:
- The facade creates its own repository instance inside `_find_git_branch_by_id`
- The RepositoryFactory.get_git_branch_repository() is not being mocked properly

### Recommended Fix
```python
@pytest.mark.asyncio
async def test_find_git_branch_by_id_in_memory(self, facade):
    """Test _find_git_branch_by_id finding branch in memory."""
    mock_repo = MagicMock()
    
    # Create a mock result that the repository would return
    async def mock_get_git_branch_by_id(branch_id):
        if branch_id == "550e8400-e29b-41d4-a716-446655440001":
            return {
                "success": True,
                "git_branch": {
                    "id": "550e8400-e29b-41d4-a716-446655440001",
                    "name": "test-branch",
                    "description": "Test branch description",
                    "project_id": "550e8400-e29b-41d4-a716-446655440000"
                }
            }
        return {"success": False, "error": "Not found"}
    
    mock_repo.get_git_branch_by_id = mock_get_git_branch_by_id
    
    with patch('fastmcp.task_management.infrastructure.repositories.repository_factory.RepositoryFactory.get_git_branch_repository') as mock_factory:
        mock_factory.return_value = mock_repo
        
        result = await facade._find_git_branch_by_id("550e8400-e29b-41d4-a716-446655440001")
        
        assert result["success"] is True
        assert result["git_branch"]["id"] == "550e8400-e29b-41d4-a716-446655440001"
```

## DDD Architecture Compliance Issues

1. **Facade Testing Internal Methods**: The test is accessing private method `_find_git_branch_by_id` which violates encapsulation.
2. **Direct Repository Access**: The facade should use services, not create repositories directly.
3. **Missing Service Layer Abstraction**: The facade is tightly coupled to the repository factory.

## Recommendations

1. **Refactor Tests**: Test public methods only, not internal implementation details.
2. **Use Dependency Injection**: Pass repository or service as dependencies instead of creating them internally.
3. **Mock at Service Level**: Mock the GitBranchService instead of trying to mock deep infrastructure components.
4. **Integration Tests**: Move database-dependent tests to integration test suite.

## Test Status

- ✅ 1 test fixed (test_find_git_branch_by_id_not_found)
- ❌ 2 tests still failing (need deeper mocking refactor)
- Total: 10/13 tests passing in the file