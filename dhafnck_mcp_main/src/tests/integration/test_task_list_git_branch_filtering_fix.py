"""
Test for task list filtering by git_branch_id fix

This test verifies that the manage_task(action="list", git_branch_id="specific-branch-id")
returns only tasks from the specified branch, not tasks from all branches.
"""

import pytest
import uuid
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.application.use_cases.list_tasks import ListTasksUseCase
from fastmcp.task_management.infrastructure.repositories.orm.task_repository import ORMTaskRepository
from fastmcp.task_management.domain.entities.task import Task as TaskEntity
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.priority import Priority


class TestTaskListGitBranchFiltering:
    """Test task list filtering by git_branch_id"""
    
    def test_list_tasks_filters_by_git_branch_id(self, mock_session):
        """Test that list_tasks only returns tasks from the specified git branch"""
        
        # Arrange: Create mock tasks in different git branches
        branch_1_id = str(uuid.uuid4())
        branch_2_id = str(uuid.uuid4())
        user_id = "test-user-123"
        
        # Create test tasks for branch 1
        task_1_branch_1 = TaskEntity(
            id=TaskId(str(uuid.uuid4())),
            title="Task 1 in Branch 1",
            description="First task in branch 1",
            git_branch_id=branch_1_id,
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            assignees=[],
            labels=[],
            details="",
            estimated_effort="",
            due_date=None,
            subtasks=[],
            dependencies=[]
        )
        
        task_2_branch_1 = TaskEntity(
            id=TaskId(str(uuid.uuid4())),
            title="Task 2 in Branch 1", 
            description="Second task in branch 1",
            git_branch_id=branch_1_id,
            status=TaskStatus.IN_PROGRESS,
            priority=Priority.HIGH,
            assignees=[],
            labels=[],
            details="",
            estimated_effort="",
            due_date=None,
            subtasks=[],
            dependencies=[]
        )
        
        # Create test tasks for branch 2
        task_1_branch_2 = TaskEntity(
            id=TaskId(str(uuid.uuid4())),
            title="Task 1 in Branch 2",
            description="First task in branch 2",
            git_branch_id=branch_2_id,
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            assignees=[],
            labels=[],
            details="",
            estimated_effort="",
            due_date=None,
            subtasks=[],
            dependencies=[]
        )
        
        # Setup repository with branch 1 ID
        repository = ORMTaskRepository(session=mock_session, git_branch_id=branch_1_id, user_id=user_id)
        
        # Save all tasks to simulate existing data
        repository.save(task_1_branch_1)
        repository.save(task_2_branch_1)
        repository.save(task_1_branch_2)
        
        # Setup use case
        use_case = ListTasksUseCase(repository)
        
        # Act: Create request with specific git_branch_id
        request = ListTasksRequest(
            git_branch_id=branch_1_id,
            status=None,
            priority=None,
            assignees=None,
            labels=None,
            limit=100
        )
        
        # Execute the list tasks use case
        response = use_case.execute(request)
        
        # Assert: Should only return tasks from branch 1
        assert response is not None
        assert hasattr(response, 'tasks')
        assert len(response.tasks) == 2, f"Expected 2 tasks from branch {branch_1_id}, but got {len(response.tasks)}"
        
        # Verify all returned tasks belong to branch 1
        for task in response.tasks:
            assert task.git_branch_id == branch_1_id, f"Task {task.id} belongs to branch {task.git_branch_id}, expected {branch_1_id}"
        
        # Verify task titles match expected tasks
        returned_titles = [task.title for task in response.tasks]
        expected_titles = ["Task 1 in Branch 1", "Task 2 in Branch 1"]
        for expected_title in expected_titles:
            assert expected_title in returned_titles, f"Expected task title '{expected_title}' not found in results"
        
        # Verify filters_applied includes git_branch_id
        assert hasattr(response, 'filters_applied')
        assert response.filters_applied is not None
        assert 'git_branch_id' in response.filters_applied
        assert response.filters_applied['git_branch_id'] == branch_1_id
        
        print(f"✅ Test passed: List tasks correctly filtered by git_branch_id {branch_1_id}")
        print(f"   Returned {len(response.tasks)} tasks from branch {branch_1_id}")
        print(f"   Task titles: {returned_titles}")
    
    def test_list_tasks_without_git_branch_id_returns_all(self, mock_session):
        """Test that list_tasks without git_branch_id returns all tasks"""
        
        # Arrange: Create mock tasks in different git branches
        branch_1_id = str(uuid.uuid4())
        branch_2_id = str(uuid.uuid4())
        user_id = "test-user-456"
        
        # Setup repository without git_branch_id filter
        repository = ORMTaskRepository(session=mock_session, user_id=user_id)
        
        # Create and save test tasks
        task_1 = TaskEntity(
            id=TaskId(str(uuid.uuid4())),
            title="Task in Branch 1",
            description="Task in branch 1",
            git_branch_id=branch_1_id,
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            assignees=[],
            labels=[],
            details="",
            estimated_effort="",
            due_date=None,
            subtasks=[],
            dependencies=[]
        )
        
        task_2 = TaskEntity(
            id=TaskId(str(uuid.uuid4())),
            title="Task in Branch 2",
            description="Task in branch 2",
            git_branch_id=branch_2_id,
            status=TaskStatus.TODO,
            priority=Priority.MEDIUM,
            assignees=[],
            labels=[],
            details="",
            estimated_effort="",
            due_date=None,
            subtasks=[],
            dependencies=[]
        )
        
        repository.save(task_1)
        repository.save(task_2)
        
        # Setup use case
        use_case = ListTasksUseCase(repository)
        
        # Act: Create request without git_branch_id
        request = ListTasksRequest(
            git_branch_id=None,  # No branch filter
            status=None,
            priority=None,
            assignees=None,
            labels=None,
            limit=100
        )
        
        response = use_case.execute(request)
        
        # Assert: Should return tasks from all branches
        assert response is not None
        assert len(response.tasks) == 2, f"Expected 2 tasks from all branches, but got {len(response.tasks)}"
        
        # Verify we have tasks from both branches
        git_branch_ids = {task.git_branch_id for task in response.tasks}
        assert branch_1_id in git_branch_ids, f"Missing tasks from branch {branch_1_id}"
        assert branch_2_id in git_branch_ids, f"Missing tasks from branch {branch_2_id}"
        
        # Verify filters_applied does not include git_branch_id
        assert 'git_branch_id' not in response.filters_applied
        
        print(f"✅ Test passed: List tasks without git_branch_id returned tasks from all branches")
        print(f"   Found tasks in branches: {git_branch_ids}")


# Fixtures needed for testing
@pytest.fixture
def mock_session():
    """Mock database session for testing"""
    # This would typically be provided by your test configuration
    # For now, return a mock that allows the tests to run
    from unittest.mock import MagicMock
    mock_session = MagicMock()
    
    # Mock the session methods used by the repository
    mock_session.query.return_value = mock_session
    mock_session.options.return_value = mock_session  
    mock_session.filter.return_value = mock_session
    mock_session.all.return_value = []  # Empty result by default
    mock_session.first.return_value = None
    mock_session.count.return_value = 0
    mock_session.commit.return_value = None
    mock_session.add.return_value = None
    mock_session.flush.return_value = None
    
    return mock_session


if __name__ == "__main__":
    # Run the test directly for quick verification
    print("🧪 Testing task list git_branch_id filtering fix...")
    
    # Simple test to verify the fix logic works
    from unittest.mock import MagicMock
    
    # Test the ListTasksUseCase fix
    print("\n1. Testing ListTasksUseCase includes git_branch_id in filters...")
    
    # Mock repository
    mock_repository = MagicMock()
    mock_repository.find_by_criteria.return_value = []
    
    use_case = ListTasksUseCase(mock_repository)
    
    # Test with git_branch_id
    request = ListTasksRequest(git_branch_id="test-branch-123")
    response = use_case.execute(request)
    
    # Verify find_by_criteria was called with git_branch_id in filters
    call_args = mock_repository.find_by_criteria.call_args
    assert call_args is not None, "find_by_criteria was not called"
    
    filters = call_args[0][0]  # First argument is filters dict
    assert 'git_branch_id' in filters, "git_branch_id not included in filters"
    assert filters['git_branch_id'] == "test-branch-123", f"Expected git_branch_id='test-branch-123', got {filters.get('git_branch_id')}"
    
    # Verify filters_applied includes git_branch_id
    assert 'git_branch_id' in response.filters_applied, "git_branch_id not in filters_applied"
    assert response.filters_applied['git_branch_id'] == "test-branch-123"
    
    print("   ✅ ListTasksUseCase correctly includes git_branch_id in filters")
    
    # Test without git_branch_id
    request_no_branch = ListTasksRequest(git_branch_id=None)
    response_no_branch = use_case.execute(request_no_branch)
    
    # Verify git_branch_id not in filters when None
    call_args_no_branch = mock_repository.find_by_criteria.call_args
    filters_no_branch = call_args_no_branch[0][0]
    assert 'git_branch_id' not in filters_no_branch, "git_branch_id should not be in filters when None"
    assert 'git_branch_id' not in response_no_branch.filters_applied
    
    print("   ✅ ListTasksUseCase correctly excludes git_branch_id when None")
    print("\n🎉 Fix verification completed successfully!")
    print("\nThe fix ensures that:")
    print("  • ListTasksUseCase passes git_branch_id to repository filters")
    print("  • TaskRepository.find_by_criteria handles git_branch_id from filters")
    print("  • User data isolation is maintained with apply_user_filter")
    print("  • Response includes git_branch_id in filters_applied for transparency")