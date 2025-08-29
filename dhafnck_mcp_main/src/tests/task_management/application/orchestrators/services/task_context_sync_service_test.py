"""Test for Task Context Sync Service"""

import pytest
import logging
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timezone

from fastmcp.task_management.application.orchestrators.services.task_context_sync_service import TaskContextSyncService
from fastmcp.task_management.domain.value_objects.task_id import TaskId
from fastmcp.task_management.domain.value_objects.task_status import TaskStatus
from fastmcp.task_management.domain.value_objects.task_priority import TaskPriority
from fastmcp.task_management.domain.entities.task import Task
from fastmcp.task_management.domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError


class TestTaskContextSyncService:
    """Test suite for TaskContextSyncService"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        return Mock()
    
    @pytest.fixture
    def mock_context_service(self):
        """Create a mock context service"""
        return Mock()
    
    @pytest.fixture
    def mock_unified_context_service(self):
        """Create a mock unified context service"""
        mock = Mock()
        # Mock the common methods
        mock.get_context = Mock()
        mock.create_context = Mock()
        mock.update_context = Mock()
        return mock
    
    @pytest.fixture
    def service(self, mock_task_repository, mock_context_service):
        """Create a task context sync service instance"""
        with patch('fastmcp.task_management.application.orchestrators.services.task_context_sync_service.UnifiedContextFacadeFactory'):
            service = TaskContextSyncService(mock_task_repository, mock_context_service)
            return service
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task"""
        task = Mock(spec=Task)
        task.id = TaskId.from_string("123")
        task.title = "Test Task"
        task.description = "Test Description"
        task.status = TaskStatus.todo()
        task.priority = TaskPriority.medium()
        task.assignees = []
        task.labels = []
        task.estimated_effort = None
        task.due_date = None
        task.git_branch_id = "branch-123"
        return task
    
    def test_init(self, mock_task_repository, mock_context_service):
        """Test service initialization"""
        with patch('fastmcp.task_management.application.orchestrators.services.task_context_sync_service.UnifiedContextFacadeFactory') as mock_factory:
            mock_factory.return_value.create_unified_service.return_value = Mock()
            
            service = TaskContextSyncService(mock_task_repository, mock_context_service)
            assert service._task_repository == mock_task_repository
            assert service._user_id is None
            assert hasattr(service, '_hierarchical_context_service')
            assert hasattr(service, '_get_task_use_case')
            mock_factory.assert_called_once()
    
    def test_init_with_user_id(self, mock_task_repository, mock_context_service):
        """Test service initialization with user_id"""
        user_id = "test-user-123"
        with patch('fastmcp.task_management.application.orchestrators.services.task_context_sync_service.UnifiedContextFacadeFactory'):
            service = TaskContextSyncService(mock_task_repository, mock_context_service, user_id=user_id)
            assert service._user_id == user_id
    
    def test_with_user(self, service):
        """Test creating user-scoped service"""
        user_id = "test-user-456"
        user_scoped_service = service.with_user(user_id)
        assert isinstance(user_scoped_service, TaskContextSyncService)
        assert user_scoped_service._user_id == user_id
        assert user_scoped_service._task_repository == service._task_repository
    
    def test_get_user_scoped_repository_no_user(self, service):
        """Test getting user-scoped repository without user_id"""
        mock_repo = Mock()
        result = service._get_user_scoped_repository(mock_repo)
        assert result == mock_repo
    
    def test_get_user_scoped_repository_with_user(self, service):
        """Test getting user-scoped repository with user_id"""
        service._user_id = "test-user"
        mock_repo = Mock()
        mock_scoped_repo = Mock()
        mock_repo.with_user.return_value = mock_scoped_repo
        
        result = service._get_user_scoped_repository(mock_repo)
        
        mock_repo.with_user.assert_called_once_with("test-user")
        assert result == mock_scoped_repo
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_no_user_id(self, service):
        """Test sync context without user_id raises error"""
        task_id = "123"
        
        with pytest.raises(UserAuthenticationRequiredError) as exc_info:
            await service.sync_context_and_get_task(task_id)
        
        assert "Task context sync" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_invalid_user_id(self, service):
        """Test sync context with invalid user_id"""
        task_id = "123"
        
        # Test with empty string
        with pytest.raises(ValueError) as exc_info:
            await service.sync_context_and_get_task(task_id, user_id="")
        assert "cannot be empty" in str(exc_info.value)
        
        # Test with whitespace
        with pytest.raises(ValueError) as exc_info:
            await service.sync_context_and_get_task(task_id, user_id="   ")
        assert "cannot be empty" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_task_not_found(self, service, mock_task_repository):
        """Test sync context when task is not found"""
        task_id = "123"
        user_id = "test-user"
        
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = None
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        result = await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        assert result is None
        mock_repo.find_by_id.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_create_new_context(self, service, sample_task, mock_unified_context_service):
        """Test sync context when creating new context"""
        task_id = "123"
        user_id = "test-user"
        project_id = "project-123"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        service._hierarchical_context_service = mock_unified_context_service
        mock_unified_context_service.get_context.return_value = None  # No existing context
        mock_unified_context_service.create_context.return_value = {"success": True}
        
        # Mock get task use case
        expected_response = {"success": True, "task": {"id": task_id}, "context": {}}
        service._get_task_use_case.execute = AsyncMock(return_value=expected_response)
        
        result = await service.sync_context_and_get_task(
            task_id,
            user_id=user_id,
            project_id=project_id,
            git_branch_name="main"
        )
        
        assert result == expected_response
        
        # Verify context was checked
        mock_unified_context_service.get_context.assert_called_once_with(
            level="task",
            context_id=task_id
        )
        
        # Verify context was created
        mock_unified_context_service.create_context.assert_called_once()
        call_args = mock_unified_context_service.create_context.call_args
        assert call_args[1]["level"] == "task"
        assert call_args[1]["context_id"] == task_id
        assert call_args[1]["data"]["task_data"]["title"] == sample_task.title
        assert call_args[1]["data"]["parent_branch_id"] == sample_task.git_branch_id
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_update_existing_context(self, service, sample_task, mock_unified_context_service):
        """Test sync context when updating existing context"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        service._hierarchical_context_service = mock_unified_context_service
        mock_unified_context_service.get_context.return_value = {"id": task_id, "data": {}}  # Existing context
        mock_unified_context_service.update_context.return_value = {"success": True}
        
        # Mock get task use case
        expected_response = {"success": True, "task": {"id": task_id}}
        service._get_task_use_case.execute = AsyncMock(return_value=expected_response)
        
        result = await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        assert result == expected_response
        
        # Verify context was updated instead of created
        mock_unified_context_service.update_context.assert_called_once()
        mock_unified_context_service.create_context.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_with_project_id_lookup(self, service, sample_task):
        """Test sync context with project_id lookup from git branch"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock task without project_id
        sample_task.project_id = None
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock git branch repository
        mock_git_branch = Mock()
        mock_git_branch.project_id = "discovered-project-id"
        
        with patch('fastmcp.task_management.application.orchestrators.services.task_context_sync_service.RepositoryFactory') as mock_factory:
            mock_git_branch_repo = Mock()
            mock_git_branch_repo.find_by_id.return_value = mock_git_branch
            mock_factory.get_git_branch_repository.return_value = mock_git_branch_repo
            
            # Mock unified context service
            mock_unified_context_service = Mock()
            mock_unified_context_service.get_context.return_value = None
            mock_unified_context_service.create_context.return_value = {"success": True}
            service._hierarchical_context_service = mock_unified_context_service
            
            # Mock get task use case
            service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
            
            result = await service.sync_context_and_get_task(task_id, user_id=user_id)
            
            # Verify git branch was queried
            mock_git_branch_repo.find_by_id.assert_called_once_with(sample_task.git_branch_id)
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_default_project_id(self, service, sample_task):
        """Test sync context with default project_id when not found"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock task without git_branch_id
        sample_task.git_branch_id = None
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.return_value = None
        mock_unified_context_service.create_context.return_value = {"success": True}
        service._hierarchical_context_service = mock_unified_context_service
        
        # Mock get task use case
        service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
        
        result = await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        # Verify default project_id was used
        create_call = mock_unified_context_service.create_context.call_args
        assert create_call is not None
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_exception_handling(self, service, sample_task):
        """Test sync context exception handling"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service to raise exception
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.side_effect = Exception("Context error")
        service._hierarchical_context_service = mock_unified_context_service
        
        result = await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        assert result is None
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_task_data_serialization(self, service, sample_task):
        """Test task data serialization in context"""
        task_id = "123"
        user_id = "test-user"
        
        # Set task with various data types
        sample_task.due_date = datetime(2025, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
        sample_task.estimated_effort = 5.5
        sample_task.labels = ["bug", "urgent"]
        sample_task.assignees = ["user1", "user2"]
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.return_value = None
        mock_unified_context_service.create_context.return_value = {"success": True}
        service._hierarchical_context_service = mock_unified_context_service
        
        # Mock get task use case
        service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
        
        await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        # Verify task data was properly serialized
        create_call = mock_unified_context_service.create_context.call_args
        task_data = create_call[1]["data"]["task_data"]
        assert task_data["title"] == sample_task.title
        assert task_data["description"] == sample_task.description
        assert task_data["status"] == "todo"
        assert task_data["priority"] == "medium"
        assert task_data["assignees"] == sample_task.assignees
        assert task_data["labels"] == sample_task.labels
        assert task_data["estimated_effort"] == sample_task.estimated_effort
        assert task_data["due_date"] == sample_task.due_date
    
    @pytest.mark.asyncio  
    async def test_sync_context_and_get_task_get_task_options(self, service, sample_task):
        """Test get task options are properly passed"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.return_value = None
        mock_unified_context_service.create_context.return_value = {"success": True}
        service._hierarchical_context_service = mock_unified_context_service
        
        # Mock get task use case
        service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
        
        await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        # Verify get task was called with correct options
        service._get_task_use_case.execute.assert_called_once_with(
            task_id,
            generate_rules=False,
            force_full_generation=False,
            include_context=True
        )
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_logging(self, service, sample_task, caplog):
        """Test logging during sync context"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.return_value = None
        mock_unified_context_service.create_context.return_value = {"success": True}
        service._hierarchical_context_service = mock_unified_context_service
        
        # Mock get task use case
        service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
        
        with caplog.at_level(logging.INFO):
            await service.sync_context_and_get_task(task_id, user_id=user_id, project_id="test-project")
        
        # Check that appropriate log messages were created
        assert any("Creating new context for task" in record.message for record in caplog.records)
    
    @pytest.mark.asyncio
    async def test_sync_context_and_get_task_branch_id_mapping(self, service, sample_task):
        """Test branch_id mapping in task context"""
        task_id = "123"
        user_id = "test-user"
        
        # Mock repository
        mock_repo = Mock()
        mock_repo.find_by_id.return_value = sample_task
        service._get_user_scoped_repository = Mock(return_value=mock_repo)
        
        # Mock unified context service
        mock_unified_context_service = Mock()
        mock_unified_context_service.get_context.return_value = None
        mock_unified_context_service.create_context.return_value = {"success": True}
        service._hierarchical_context_service = mock_unified_context_service
        
        # Mock get task use case
        service._get_task_use_case.execute = AsyncMock(return_value={"success": True})
        
        await service.sync_context_and_get_task(task_id, user_id=user_id)
        
        # Verify branch_id was properly mapped
        create_call = mock_unified_context_service.create_context.call_args
        context_data = create_call[1]["data"]
        assert context_data["parent_branch_id"] == sample_task.git_branch_id
        assert context_data["parent_branch_context_id"] == sample_task.git_branch_id