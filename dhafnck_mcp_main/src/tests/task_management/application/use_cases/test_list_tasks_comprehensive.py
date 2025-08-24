"""Comprehensive test suite for List Tasks Use Case"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List

from fastmcp.task_management.application.use_cases.list_tasks import ListTasksUseCase
from fastmcp.task_management.application.dtos.task import ListTasksRequest, TaskListResponse
from fastmcp.task_management.domain import TaskRepository, TaskStatus, Priority
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.value_objects.task_id import TaskId


class TestListTasksUseCase:
    """Test suite for ListTasksUseCase"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        return Mock(spec=TaskRepository)
    
    @pytest.fixture
    def use_case(self, mock_task_repository):
        """Create a ListTasksUseCase instance"""
        return ListTasksUseCase(mock_task_repository)
    
    @pytest.fixture
    def sample_tasks(self):
        """Create sample tasks for testing"""
        return [
            Task(
                id=TaskId.from_string("task-001"),
                title="First Task",
                description="First task description",
                status=TaskStatus.todo(),
                priority=Priority.high(),
                git_branch_id="branch-123",
                assignees=["user1"],
                labels=["backend", "urgent"],
                progress=0
            ),
            Task(
                id=TaskId.from_string("task-002"),
                title="Second Task",
                description="Second task description",
                status=TaskStatus.in_progress(),
                priority=Priority.medium(),
                git_branch_id="branch-123",
                assignees=["user2"],
                labels=["frontend"],
                progress=50
            ),
            Task(
                id=TaskId.from_string("task-003"),
                title="Third Task",
                description="Third task description",
                status=TaskStatus.done(),
                priority=Priority.low(),
                git_branch_id="branch-456",
                assignees=["user1", "user2"],
                labels=["testing"],
                progress=100
            )
        ]
    
    def test_init(self, mock_task_repository):
        """Test use case initialization"""
        use_case = ListTasksUseCase(mock_task_repository)
        assert use_case._task_repository == mock_task_repository
    
    def test_execute_no_filters(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks without any filters"""
        # Mock repository response
        mock_task_repository.find_by_criteria.return_value = sample_tasks
        
        # Create request
        request = ListTasksRequest()
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with empty filters
        mock_task_repository.find_by_criteria.assert_called_once_with({}, limit=None)
        
        # Verify response
        assert isinstance(response, TaskListResponse)
        assert len(response.tasks) == 3
        assert response.total_count == 3
        assert response.filters_applied == {}
    
    def test_execute_with_git_branch_filter(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by git branch ID"""
        # Filter tasks for branch-123
        filtered_tasks = [t for t in sample_tasks if t.git_branch_id == "branch-123"]
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with git_branch_id
        request = ListTasksRequest(git_branch_id="branch-123")
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with git_branch_id filter
        expected_filters = {'git_branch_id': 'branch-123'}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 2
        assert all(task.git_branch_id == "branch-123" for task in response.tasks)
        assert response.filters_applied == {'git_branch_id': 'branch-123'}
    
    def test_execute_with_status_filter(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by status"""
        # Filter tasks with 'todo' status
        filtered_tasks = [sample_tasks[0]]  # Only first task has 'todo' status
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with status filter
        request = ListTasksRequest(status="todo")
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with status filter
        expected_filters = {'status': TaskStatus.todo()}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 1
        assert response.tasks[0].status == "todo"
        assert response.filters_applied == {'status': 'todo'}
    
    def test_execute_with_priority_filter(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by priority"""
        # Filter tasks with 'high' priority
        filtered_tasks = [sample_tasks[0]]  # Only first task has 'high' priority
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with priority filter
        request = ListTasksRequest(priority="high")
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with priority filter
        expected_filters = {'priority': Priority.high()}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 1
        assert response.tasks[0].priority == "high"
        assert response.filters_applied == {'priority': 'high'}
    
    def test_execute_with_assignees_filter_new_field(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by assignees (new field)"""
        # Filter tasks assigned to user1
        filtered_tasks = [sample_tasks[0], sample_tasks[2]]  # Tasks assigned to user1
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with assignees filter
        request = ListTasksRequest(assignees=["user1"])
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with assignees filter
        expected_filters = {'assignees': ['user1']}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 2
        assert response.filters_applied == {'assignees': ['user1']}
    
    def test_execute_with_assignee_filter_legacy_field(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by assignee (legacy field)"""
        # Filter tasks assigned to user2
        filtered_tasks = [sample_tasks[1], sample_tasks[2]]  # Tasks with user2
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with legacy assignee filter
        request = ListTasksRequest()
        request.assignee = "user2"  # Set legacy field directly
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with assignee filter
        expected_filters = {'assignee': 'user2'}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 2
        assert response.filters_applied == {'assignee': 'user2'}
    
    def test_execute_with_labels_filter(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks filtered by labels"""
        # Filter tasks with 'backend' label
        filtered_tasks = [sample_tasks[0]]  # Only first task has 'backend' label
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with labels filter
        request = ListTasksRequest(labels=["backend"])
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with labels filter
        expected_filters = {'labels': ['backend']}
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=None)
        
        # Verify response
        assert len(response.tasks) == 1
        assert "backend" in response.tasks[0].labels
        assert response.filters_applied == {'labels': ['backend']}
    
    def test_execute_with_limit(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks with limit"""
        # Return only first 2 tasks
        limited_tasks = sample_tasks[:2]
        mock_task_repository.find_by_criteria.return_value = limited_tasks
        
        # Create request with limit
        request = ListTasksRequest(limit=2)
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with limit
        mock_task_repository.find_by_criteria.assert_called_once_with({}, limit=2)
        
        # Verify response
        assert len(response.tasks) == 2
        assert response.filters_applied == {'limit': 2}
    
    def test_execute_with_multiple_filters(self, use_case, mock_task_repository, sample_tasks):
        """Test listing tasks with multiple filters"""
        # Filter tasks with multiple criteria
        filtered_tasks = [sample_tasks[0]]  # First task matches all criteria
        mock_task_repository.find_by_criteria.return_value = filtered_tasks
        
        # Create request with multiple filters
        request = ListTasksRequest(
            git_branch_id="branch-123",
            status="todo",
            priority="high",
            assignees=["user1"],
            labels=["backend"],
            limit=10
        )
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify repository called with all filters
        expected_filters = {
            'git_branch_id': 'branch-123',
            'status': TaskStatus.todo(),
            'priority': Priority.high(),
            'assignees': ['user1'],
            'labels': ['backend']
        }
        mock_task_repository.find_by_criteria.assert_called_once_with(expected_filters, limit=10)
        
        # Verify response
        assert len(response.tasks) == 1
        assert response.filters_applied == {
            'git_branch_id': 'branch-123',
            'status': 'todo',
            'priority': 'high',
            'assignees': ['user1'],
            'labels': ['backend'],
            'limit': 10
        }
    
    def test_execute_empty_result(self, use_case, mock_task_repository):
        """Test listing tasks when no tasks match filters"""
        # Mock repository to return empty list
        mock_task_repository.find_by_criteria.return_value = []
        
        # Create request
        request = ListTasksRequest(status="cancelled")
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify response
        assert len(response.tasks) == 0
        assert response.total_count == 0
        assert response.filters_applied == {'status': 'cancelled'}
    
    def test_execute_none_result_handling(self, use_case, mock_task_repository):
        """Test handling when repository returns None"""
        # Mock repository to return None
        mock_task_repository.find_by_criteria.return_value = None
        
        # Create request
        request = ListTasksRequest()
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify response handles None gracefully
        assert len(response.tasks) == 0
        assert response.total_count == 0
    
    def test_execute_filter_building_logic(self, use_case, mock_task_repository):
        """Test the filter building logic in detail"""
        # Mock repository
        mock_task_repository.find_by_criteria.return_value = []
        
        # Test various filter combinations
        test_cases = [
            # (request_params, expected_filters)
            ({'status': 'in_progress'}, {'status': TaskStatus.in_progress()}),
            ({'priority': 'low'}, {'priority': Priority.low()}),
            ({'assignees': ['user1', 'user2']}, {'assignees': ['user1', 'user2']}),
            ({'labels': ['bug', 'critical']}, {'labels': ['bug', 'critical']}),
            ({'git_branch_id': 'branch-789'}, {'git_branch_id': 'branch-789'}),
        ]
        
        for request_params, expected_filters in test_cases:
            # Reset mock
            mock_task_repository.reset_mock()
            
            # Create request
            request = ListTasksRequest(**request_params)
            
            # Execute use case
            use_case.execute(request)
            
            # Verify filters
            mock_task_repository.find_by_criteria.assert_called_once_with(
                expected_filters, 
                limit=None
            )
    
    def test_execute_filters_applied_in_response(self, use_case, mock_task_repository):
        """Test that filters_applied in response matches request parameters"""
        # Mock repository
        mock_task_repository.find_by_criteria.return_value = []
        
        # Create request with various filters
        request = ListTasksRequest(
            git_branch_id="branch-999",
            status="review",
            priority="urgent",
            assignees=["reviewer1"],
            labels=["needs-review"],
            limit=5
        )
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify filters_applied includes all request parameters
        assert response.filters_applied == {
            'git_branch_id': 'branch-999',
            'status': 'review',
            'priority': 'urgent',
            'assignees': ['reviewer1'],
            'labels': ['needs-review'],
            'limit': 5
        }
    
    def test_execute_assignees_priority(self, use_case, mock_task_repository):
        """Test that new assignees field takes priority over legacy assignee"""
        # Mock repository
        mock_task_repository.find_by_criteria.return_value = []
        
        # Create request with both assignees and assignee
        request = ListTasksRequest(assignees=["user1", "user2"])
        request.assignee = "legacy_user"  # Set legacy field
        
        # Execute use case
        use_case.execute(request)
        
        # Verify only assignees filter is used, not assignee
        expected_filters = {'assignees': ['user1', 'user2']}
        mock_task_repository.find_by_criteria.assert_called_once_with(
            expected_filters, 
            limit=None
        )
    
    def test_execute_response_dto_conversion(self, use_case, mock_task_repository, sample_tasks):
        """Test that tasks are properly converted to response DTOs"""
        # Mock repository response
        mock_task_repository.find_by_criteria.return_value = sample_tasks
        
        # Create request
        request = ListTasksRequest()
        
        # Execute use case
        response = use_case.execute(request)
        
        # Verify each task is properly converted
        for i, task_dto in enumerate(response.tasks):
            original_task = sample_tasks[i]
            assert task_dto.id == str(original_task.id.value)
            assert task_dto.title == original_task.title
            assert task_dto.description == original_task.description
            assert task_dto.status == str(original_task.status)
            assert task_dto.priority == str(original_task.priority)
            assert task_dto.git_branch_id == original_task.git_branch_id
            assert task_dto.assignees == original_task.assignees
            assert task_dto.labels == original_task.labels
            assert task_dto.progress == original_task.progress
    
    def test_execute_logging_coverage(self, use_case, mock_task_repository, caplog):
        """Test that proper logging is performed"""
        import logging
        
        # Set log level to DEBUG
        caplog.set_level(logging.DEBUG)
        
        # Mock repository
        mock_task_repository.find_by_criteria.return_value = [Mock(), Mock()]
        
        # Create request
        request = ListTasksRequest(
            git_branch_id="branch-log-test",
            status="todo",
            priority="high",
            limit=10
        )
        
        # Execute use case
        use_case.execute(request)
        
        # Verify debug logs
        assert "[USE_CASE] ListTasksUseCase.execute called" in caplog.text
        assert "[USE_CASE] Request git_branch_id: branch-log-test" in caplog.text
        assert "[USE_CASE] Request status: todo" in caplog.text
        assert "[USE_CASE] Request priority: high" in caplog.text
        assert "[USE_CASE] Request limit: 10" in caplog.text
        assert "[USE_CASE] Added git_branch_id to filters: branch-log-test" in caplog.text
        assert "[USE_CASE] Final filters being passed to repository:" in caplog.text
        assert "[USE_CASE] Repository returned 2 tasks" in caplog.text