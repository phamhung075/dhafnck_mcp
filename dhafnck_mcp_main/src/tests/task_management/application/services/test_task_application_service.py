"""Unit tests for TaskApplicationService."""

import pytest
import pytest_asyncio
from unittest.mock import Mock, AsyncMock, MagicMock, patch
from datetime import datetime, timezone

from src.fastmcp.task_management.application.services.task_application_service import TaskApplicationService
from src.fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from src.fastmcp.task_management.application.dtos.task.create_task_response import CreateTaskResponse
from src.fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from src.fastmcp.task_management.application.dtos.task.task_response import TaskResponse
from src.fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from src.fastmcp.task_management.application.dtos.task.task_list_response import TaskListResponse
from src.fastmcp.task_management.application.dtos.task.search_tasks_request import SearchTasksRequest
from src.fastmcp.task_management.application.dtos.task.task_info import TaskInfo
from src.fastmcp.task_management.domain.entities.task import Task
from src.fastmcp.task_management.domain.value_objects.task_id import TaskId
from src.fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from src.fastmcp.task_management.domain.value_objects.priority import Priority
from src.fastmcp.task_management.domain.exceptions.task_exceptions import TaskNotFoundError


class TestTaskApplicationServiceInit:
    """Test TaskApplicationService initialization."""
    
    def test_service_initialization(self):
        """Test service initializes with required dependencies."""
        # Arrange
        mock_repo = Mock()
        mock_context_service = Mock()
        
        # Act
        service = TaskApplicationService(
            task_repository=mock_repo,
            context_service=mock_context_service
        )
        
        # Assert
        assert service._task_repository == mock_repo
        assert service._context_service == mock_context_service
        assert service._create_task_use_case is not None
        assert service._get_task_use_case is not None
        assert service._update_task_use_case is not None
        assert service._list_tasks_use_case is not None
        assert service._search_tasks_use_case is not None
        assert service._delete_task_use_case is not None
        assert service._complete_task_use_case is not None
    
    def test_service_initialization_without_context_service(self):
        """Test service can initialize without context service."""
        # Arrange
        mock_repo = Mock()
        
        # Act
        service = TaskApplicationService(task_repository=mock_repo)
        
        # Assert
        assert service._task_repository == mock_repo
        assert service._context_service is None


class TestCreateTask:
    """Test create task functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        mock_context_service = Mock()
        service = TaskApplicationService(mock_repo, mock_context_service)
        
        # Mock the use case
        mock_use_case = Mock()
        service._create_task_use_case = mock_use_case
        
        # Mock hierarchical context service
        mock_hierarchical_context_service = Mock()
        service._hierarchical_context_service = mock_hierarchical_context_service
        
        return {
            "service": service,
            "mock_repo": mock_repo,
            "mock_use_case": mock_use_case,
            "mock_hierarchical_context_service": mock_hierarchical_context_service
        }
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, setup):
        """Test successful task creation with context creation."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="test-git-branch-id"
        )
        
        # Create a mock task
        mock_task = Mock()
        mock_task.id = TaskId.from_string("550e8400-e29b-41d4-a716-446655440001")
        mock_task.title = "Test Task"
        mock_task.description = "Test Description"
        mock_task.status = Mock(value="todo")
        mock_task.priority = Mock(value="medium")
        mock_task.assignees = []
        mock_task.labels = []
        mock_task.estimated_effort = None
        mock_task.due_date = None
        
        # Mock successful response
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = mock_task
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.create_task(request)
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(request)
        mock_hierarchical_context_service.create_context.assert_called_once_with(
            level="task",
            context_id=str(mock_task.id.value),
            data={
                "task_data": {
                    "title": mock_task.title,
                    "description": mock_task.description,
                    "status": mock_task.status.value,
                    "priority": mock_task.priority.value,
                    "assignees": mock_task.assignees,
                    "labels": mock_task.labels,
                    "estimated_effort": mock_task.estimated_effort,
                    "due_date": None
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_create_task_without_optional_fields(self, setup):
        """Test task creation with default values for optional fields."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="test-git-branch-id"
        )
        
        # Mock response without task
        mock_response = Mock()
        mock_response.success = False
        mock_response.task = None
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.create_task(request)
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(request)
        # Context should not be created if response has no task
        mock_hierarchical_context_service.create_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_create_task_failure(self, setup):
        """Test task creation failure handling."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="test-git-branch-id"
        )
        
        # Mock failure response
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "Creation failed"
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.create_task(request)
        
        # Assert
        assert response == mock_response
        mock_hierarchical_context_service.create_context.assert_not_called()


class TestGetTask:
    """Test get task functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        mock_context_service = Mock()
        service = TaskApplicationService(mock_repo, mock_context_service)
        
        # Mock the use case
        mock_use_case = AsyncMock()
        service._get_task_use_case = mock_use_case
        
        return {
            "service": service,
            "mock_use_case": mock_use_case
        }
    
    @pytest.mark.asyncio
    async def test_get_task_success(self, setup):
        """Test successful task retrieval."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # Mock response
        mock_response = TaskResponse(
            id=task_id,
            title="Test Task",
            description="Test Description",
            status="todo",
            priority="medium",
            details="",
            estimated_effort="",
            assignees=[],
            labels=[],
            dependencies=[],
            subtasks=[],
            due_date=None,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc)
        )
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.get_task(
            task_id=task_id,
            generate_rules=True,
            force_full_generation=False,
            include_context=True,
            user_id="test-user",
            project_id="test-project",
            git_branch_name="main"
        )
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(
            task_id,
            generate_rules=True,
            force_full_generation=False,
            include_context=True
        )
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, setup):
        """Test task not found returns None."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        task_id = "non-existent-id"
        mock_use_case.execute.side_effect = TaskNotFoundError(f"Task {task_id} not found")
        
        # Act
        response = await service.get_task(task_id)
        
        # Assert
        assert response is None
    
    @pytest.mark.asyncio
    async def test_get_task_with_defaults(self, setup):
        """Test get task with default parameters."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        mock_response = Mock()
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.get_task(task_id)
        
        # Assert
        mock_use_case.execute.assert_called_once_with(
            task_id,
            generate_rules=True,
            force_full_generation=False,
            include_context=False
        )


class TestUpdateTask:
    """Test update task functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        mock_context_service = Mock()
        service = TaskApplicationService(mock_repo, mock_context_service)
        
        # Mock the use case
        mock_use_case = Mock()
        service._update_task_use_case = mock_use_case
        
        # Mock hierarchical context service
        mock_hierarchical_context_service = Mock()
        service._hierarchical_context_service = mock_hierarchical_context_service
        
        return {
            "service": service,
            "mock_use_case": mock_use_case,
            "mock_hierarchical_context_service": mock_hierarchical_context_service
        }
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, setup):
        """Test successful task update with context update."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        request = UpdateTaskRequest(
            task_id="550e8400-e29b-41d4-a716-446655440001",
            title="Updated Task",
            status="in_progress"
        )
        
        # Mock task
        mock_task = Mock()
        mock_task.id = TaskId.from_string("550e8400-e29b-41d4-a716-446655440001")
        mock_task.title = "Updated Task"
        mock_task.description = "Test Description"
        mock_task.status = Mock(value="in_progress")
        mock_task.priority = Mock(value="medium")
        mock_task.assignees = []
        mock_task.labels = []
        mock_task.estimated_effort = None
        mock_task.due_date = None
        
        # Mock response
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = mock_task
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.update_task(request)
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(request)
        mock_hierarchical_context_service.update_context.assert_called_once_with(
            level="task",
            context_id=str(mock_task.id.value),
            changes={
                "task_data": {
                    "title": mock_task.title,
                    "description": mock_task.description,
                    "status": mock_task.status.value,
                    "priority": mock_task.priority.value,
                    "assignees": mock_task.assignees,
                    "labels": mock_task.labels,
                    "estimated_effort": mock_task.estimated_effort,
                    "due_date": None
                }
            }
        )
    
    @pytest.mark.asyncio
    async def test_update_task_failure(self, setup):
        """Test task update failure handling."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        request = UpdateTaskRequest(
            task_id="550e8400-e29b-41d4-a716-446655440001",
            title="Updated Task"
        )
        
        # Mock failure response
        mock_response = Mock()
        mock_response.success = False
        mock_response.error = "Update failed"
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.update_task(request)
        
        # Assert
        assert response == mock_response
        mock_hierarchical_context_service.update_context.assert_not_called()


class TestListTasks:
    """Test list tasks functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        service = TaskApplicationService(mock_repo)
        
        # Mock the use case
        mock_use_case = AsyncMock()
        service._list_tasks_use_case = mock_use_case
        
        return {
            "service": service,
            "mock_use_case": mock_use_case
        }
    
    @pytest.mark.asyncio
    async def test_list_tasks_with_filters(self, setup):
        """Test listing tasks with filters."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        request = ListTasksRequest(
            status="in_progress",
            priority="high",
            assignees=["@coding_agent"],
            labels=["bug", "critical"]
        )
        
        # Mock response
        mock_response = TaskListResponse(
            tasks=[
                TaskResponse(
                    id="task-1",
                    title="Task 1",
                    description="Task description",
                    status="in_progress",
                    priority="high",
                    details="",
                    estimated_effort="",
                    assignees=[],
                    labels=[],
                    dependencies=[],
                    subtasks=[],
                    due_date=None,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ],
            count=1
        )
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.list_tasks(request)
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(request)
    
    @pytest.mark.asyncio
    async def test_get_all_tasks(self, setup):
        """Test getting all tasks."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        # Mock response
        mock_response = TaskListResponse(tasks=[], count=0)
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.get_all_tasks()
        
        # Assert
        assert response == mock_response
        # Should create empty request
        args = mock_use_case.execute.call_args[0]
        assert isinstance(args[0], ListTasksRequest)
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_status(self, setup):
        """Test getting tasks by status."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        # Mock response
        mock_response = TaskListResponse(tasks=[], count=0)
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.get_tasks_by_status("done")
        
        # Assert
        assert response == mock_response
        args = mock_use_case.execute.call_args[0]
        assert isinstance(args[0], ListTasksRequest)
        assert args[0].status == "done"
    
    @pytest.mark.asyncio
    async def test_get_tasks_by_assignee(self, setup):
        """Test getting tasks by assignee."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        # Mock response
        mock_response = TaskListResponse(tasks=[], count=0)
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.get_tasks_by_assignee("@coding_agent")
        
        # Assert
        assert response == mock_response
        args = mock_use_case.execute.call_args[0]
        assert isinstance(args[0], ListTasksRequest)
        assert args[0].assignees == ["@coding_agent"]


class TestSearchTasks:
    """Test search tasks functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        service = TaskApplicationService(mock_repo)
        
        # Mock the use case
        mock_use_case = AsyncMock()
        service._search_tasks_use_case = mock_use_case
        
        return {
            "service": service,
            "mock_use_case": mock_use_case
        }
    
    @pytest.mark.asyncio
    async def test_search_tasks(self, setup):
        """Test searching tasks."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        request = SearchTasksRequest(
            query="authentication bug",
            limit=10
        )
        
        # Mock response
        mock_response = TaskListResponse(
            tasks=[
                TaskResponse(
                    id="task-1",
                    title="Fix authentication bug",
                    description="Fix authentication bug description",
                    status="todo",
                    priority="high",
                    details="",
                    estimated_effort="",
                    assignees=[],
                    labels=[],
                    dependencies=[],
                    subtasks=[],
                    due_date=None,
                    created_at=datetime.now(timezone.utc),
                    updated_at=datetime.now(timezone.utc)
                )
            ],
            count=1
        )
        mock_use_case.execute.return_value = mock_response
        
        # Act
        response = await service.search_tasks(request)
        
        # Assert
        assert response == mock_response
        mock_use_case.execute.assert_called_once_with(request)


class TestDeleteTask:
    """Test delete task functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        service = TaskApplicationService(mock_repo)
        
        # Mock the use case
        mock_use_case = Mock()
        service._delete_task_use_case = mock_use_case
        
        # Mock hierarchical context service
        mock_hierarchical_context_service = Mock()
        service._hierarchical_context_service = mock_hierarchical_context_service
        
        return {
            "service": service,
            "mock_use_case": mock_use_case,
            "mock_hierarchical_context_service": mock_hierarchical_context_service
        }
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, setup):
        """Test successful task deletion."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        mock_use_case.execute.return_value = True
        
        # Act
        result = await service.delete_task(
            task_id=task_id,
            user_id="test-user",
            project_id="test-project",
            git_branch_name="feature"
        )
        
        # Assert
        assert result is True
        mock_use_case.execute.assert_called_once_with(task_id)
        mock_hierarchical_context_service.delete_context.assert_called_once_with(
            "task", task_id
        )
    
    @pytest.mark.asyncio
    async def test_delete_task_failure(self, setup):
        """Test failed task deletion."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        mock_use_case.execute.return_value = False
        
        # Act
        result = await service.delete_task(task_id)
        
        # Assert
        assert result is False
        mock_hierarchical_context_service.delete_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_delete_task_with_defaults(self, setup):
        """Test delete task with default parameters."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        mock_hierarchical_context_service = setup["mock_hierarchical_context_service"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        mock_use_case.execute.return_value = True
        
        # Act
        result = await service.delete_task(task_id)
        
        # Assert
        assert result is True
        mock_hierarchical_context_service.delete_context.assert_called_once_with(
            "task", task_id
        )


class TestCompleteTask:
    """Test complete task functionality."""
    
    @pytest_asyncio.fixture
    async def setup(self):
        """Set up test dependencies."""
        mock_repo = Mock()
        service = TaskApplicationService(mock_repo)
        
        # Mock the use case
        mock_use_case = AsyncMock()
        service._complete_task_use_case = mock_use_case
        
        return {
            "service": service,
            "mock_use_case": mock_use_case
        }
    
    @pytest.mark.asyncio
    async def test_complete_task_success(self, setup):
        """Test successful task completion."""
        # Arrange
        service = setup["service"]
        mock_use_case = setup["mock_use_case"]
        
        task_id = "550e8400-e29b-41d4-a716-446655440001"
        
        # Mock response
        mock_response = {
            "status": "success",
            "task_id": task_id,
            "message": "Task completed successfully"
        }
        mock_use_case.execute.return_value = mock_response
        
        # Act
        result = await service.complete_task(task_id)
        
        # Assert
        assert result == mock_response
        mock_use_case.execute.assert_called_once_with(task_id)


class TestTaskApplicationServiceIntegration:
    """Test integration scenarios for TaskApplicationService."""
    
    @pytest.mark.asyncio
    async def test_create_update_delete_workflow(self):
        """Test complete task lifecycle."""
        # This would be an integration test with real implementations
        # For now, we'll use mocks to simulate the workflow
        
        mock_repo = Mock()
        mock_repo.get_next_id.return_value = TaskId.from_string("550e8400-e29b-41d4-a716-446655440001")
        
        service = TaskApplicationService(mock_repo)
        
        # Mock all use cases
        service._create_task_use_case = Mock()
        service._update_task_use_case = Mock()
        service._delete_task_use_case = Mock()
        service._hierarchical_context_service = AsyncMock()
        
        # Create task
        create_request = CreateTaskRequest(
            title="Integration Test Task",
            description="Test Description",
            git_branch_id="test-git-branch-id"
        )
        
        mock_task = Mock()
        mock_task.id = TaskId.from_string("550e8400-e29b-41d4-a716-446655440001")
        
        create_response = Mock()
        create_response.success = True
        create_response.task = mock_task
        service._create_task_use_case.execute.return_value = create_response
        
        result = await service.create_task(create_request)
        assert result.success is True
        
        # Update task
        update_request = UpdateTaskRequest(
            task_id="550e8400-e29b-41d4-a716-446655440001",
            status="in_progress"
        )
        
        update_response = Mock()
        update_response.success = True
        update_response.task = mock_task
        service._update_task_use_case.execute.return_value = update_response
        
        result = await service.update_task(update_request)
        assert result.success is True
        
        # Delete task
        service._delete_task_use_case.execute.return_value = True
        
        result = await service.delete_task("550e8400-e29b-41d4-a716-446655440001")
        assert result is True