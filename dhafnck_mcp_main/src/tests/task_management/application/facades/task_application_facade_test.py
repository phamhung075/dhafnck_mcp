"""
Tests for Task Application Facade

This module tests the TaskApplicationFacade functionality including:
- Task CRUD operations (create, read, update, delete, complete)
- Task listing and searching with filtering
- Context integration and synchronization
- Dependency management
- Error handling and validation
- Performance optimizations and repository selection
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from fastmcp.task_management.application.facades.task_application_facade import TaskApplicationFacade
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest
from fastmcp.task_management.application.dtos.task.search_tasks_request import SearchTasksRequest
from fastmcp.task_management.domain.exceptions import TaskNotFoundError


class TestTaskApplicationFacade:
    """Test suite for TaskApplicationFacade"""
    
    @pytest.fixture
    def mock_task_repository(self):
        """Create a mock task repository"""
        repo = Mock()
        repo.find_by_id = Mock()
        repo.save = Mock()
        return repo
    
    @pytest.fixture
    def mock_subtask_repository(self):
        """Create a mock subtask repository"""
        repo = Mock()
        repo.find_by_parent_task_id = Mock()
        return repo
    
    @pytest.fixture
    def mock_context_service(self):
        """Create a mock context service"""
        return Mock()
    
    @pytest.fixture
    def mock_git_branch_repository(self):
        """Create a mock git branch repository"""
        repo = Mock()
        repo.find_all = AsyncMock()
        return repo
    
    @pytest.fixture
    def facade(self, mock_task_repository, mock_subtask_repository, mock_context_service, mock_git_branch_repository):
        """Create facade instance with mocked dependencies"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(
                        task_repository=mock_task_repository,
                        subtask_repository=mock_subtask_repository,
                        context_service=mock_context_service,
                        git_branch_repository=mock_git_branch_repository
                    )
                    return facade
    
    @pytest.fixture
    def mock_task_entity(self):
        """Create a mock task entity"""
        task = Mock()
        task.id = "task-123"
        task.title = "Test Task"
        task.description = "Test Description"
        task.status = "todo"
        task.priority = "medium"
        task.assignees = ["user-1"]
        task.labels = ["bug"]
        task.estimated_effort = "2 hours"
        task.due_date = datetime.now()
        task.created_at = datetime.now()
        task.updated_at = datetime.now()
        task.to_dict.return_value = {
            "id": "task-123",
            "title": "Test Task",
            "description": "Test Description",
            "status": "todo",
            "priority": "medium"
        }
        task.add_dependency = Mock()
        task.remove_dependency = Mock()
        task.dependencies = []
        return task


class TestTaskApplicationFacadeCreateTask:
    """Test suite for task creation"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextSyncService'):
                        facade = TaskApplicationFacade(task_repository=mock_task_repository)
                        return facade
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.get_current_user_id')
    @patch('fastmcp.task_management.application.facades.task_application_facade.AuthConfig')
    def test_create_task_success(self, mock_auth_config, mock_get_user_id, facade):
        """Test successful task creation"""
        # Mock authentication
        mock_get_user_id.return_value = "test-user-123"
        mock_auth_config.is_default_user_allowed.return_value = False
        
        # Mock use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = Mock()
        mock_response.task.id = "task-123"
        mock_response.message = "Task created successfully"
        
        facade._create_task_use_case.execute.return_value = mock_response
        
        # Mock context sync service
        mock_sync_response = Mock()
        facade._task_context_sync_service.sync_context_and_get_task = AsyncMock(return_value=mock_sync_response)
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        result = facade.create_task(request)
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert "task" in result
        assert result["message"] == "Task created successfully"
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.get_current_user_id')
    def test_create_task_validation_error(self, mock_get_user_id, facade):
        """Test task creation with validation error"""
        mock_get_user_id.return_value = "test-user-123"
        
        request = CreateTaskRequest(
            title="",  # Empty title should fail validation
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        result = facade.create_task(request)
        
        assert result["success"] is False
        assert result["action"] == "create"
        assert "title is required" in result["error"]
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.get_current_user_id')
    def test_create_task_title_too_long(self, mock_get_user_id, facade):
        """Test task creation with title too long"""
        mock_get_user_id.return_value = "test-user-123"
        
        request = CreateTaskRequest(
            title="x" * 201,  # Title too long
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        result = facade.create_task(request)
        
        assert result["success"] is False
        assert result["action"] == "create"
        assert "cannot exceed 200 characters" in result["error"]
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.get_current_user_id')
    @patch('fastmcp.task_management.application.facades.task_application_facade.AuthConfig')
    def test_create_task_compatibility_mode(self, mock_auth_config, mock_get_user_id, facade):
        """Test task creation in compatibility mode"""
        # Mock authentication failure with compatibility mode fallback
        from fastmcp.task_management.domain.exceptions.authentication_exceptions import UserAuthenticationRequiredError
        mock_get_user_id.side_effect = UserAuthenticationRequiredError("Authentication required")
        mock_auth_config.is_default_user_allowed.return_value = True
        mock_auth_config.get_fallback_user_id.return_value = "compatibility-default-user"
        
        # Mock use case response
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = Mock()
        mock_response.task.id = "task-123"
        mock_response.message = "Task created successfully"
        
        facade._create_task_use_case.execute.return_value = mock_response
        
        # Mock context sync service
        mock_sync_response = Mock()
        facade._task_context_sync_service.sync_context_and_get_task = AsyncMock(return_value=mock_sync_response)
        
        request = CreateTaskRequest(
            title="Test Task",
            description="Test Description",
            git_branch_id="branch-123"
        )
        
        result = facade.create_task(request)
        
        assert result["success"] is True
        assert result["action"] == "create"
        assert "task" in result
        assert result["message"] == "Task created successfully"


class TestTaskApplicationFacadeUpdateTask:
    """Test suite for task updates"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_update_task_success(self, facade):
        """Test successful task update"""
        mock_response = Mock()
        mock_response.success = True
        mock_response.task = Mock()
        mock_response.task.id = "task-123"
        
        facade._update_task_use_case.execute.return_value = mock_response
        
        request = UpdateTaskRequest(
            task_id="task-123",
            title="Updated Task",
            status="in_progress"
        )
        
        result = facade.update_task("task-123", request)
        
        assert result["success"] is True
        assert result["action"] == "update"
        assert "task" in result
    
    def test_update_task_not_found(self, facade):
        """Test task update when task not found"""
        facade._update_task_use_case.execute.side_effect = TaskNotFoundError("Task not found")
        
        request = UpdateTaskRequest(
            task_id="nonexistent-task",
            title="Updated Task"
        )
        
        result = facade.update_task("nonexistent-task", request)
        
        assert result["success"] is False
        assert result["action"] == "update"
        assert "Task not found" in result["error"]
    
    def test_update_task_empty_id(self, facade):
        """Test task update with empty task ID"""
        request = UpdateTaskRequest(title="Updated Task")
        
        result = facade.update_task("", request)
        
        assert result["success"] is False
        assert result["action"] == "update"
        assert "Task ID is required" in result["error"]


class TestTaskApplicationFacadeGetTask:
    """Test suite for task retrieval"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_get_task_success(self, facade, mock_task_repository, mock_task_entity):
        """Test successful task retrieval"""
        mock_task_repository.find_by_id.return_value = mock_task_entity
        
        mock_response = Mock()
        mock_response.to_dict.return_value = {
            "id": "task-123",
            "title": "Test Task",
            "context_data": {"key": "value"}
        }
        
        facade._get_task_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = facade.get_task("task-123")
        
        assert result["success"] is True
        assert result["action"] == "get"
        assert result["task"]["id"] == "task-123"
    
    def test_get_task_not_found(self, facade, mock_task_repository):
        """Test task retrieval when task not found"""
        mock_task_repository.find_by_id.return_value = None
        
        result = facade.get_task("nonexistent-task")
        
        assert result["success"] is False
        assert result["action"] == "get"
        assert "not found" in result["error"]
    
    def test_get_task_empty_id(self, facade):
        """Test task retrieval with empty task ID"""
        result = facade.get_task("")
        
        assert result["success"] is False
        assert result["action"] == "get"
        assert "Task ID is required" in result["error"]


class TestTaskApplicationFacadeDeleteTask:
    """Test suite for task deletion"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_delete_task_success(self, facade):
        """Test successful task deletion"""
        facade._delete_task_use_case.execute.return_value = True
        
        result = facade.delete_task("task-123")
        
        assert result["success"] is True
        assert result["action"] == "delete"
        assert "deleted successfully" in result["message"]
    
    def test_delete_task_not_found(self, facade):
        """Test task deletion when task not found"""
        facade._delete_task_use_case.execute.side_effect = TaskNotFoundError("Task not found")
        
        result = facade.delete_task("nonexistent-task")
        
        assert result["success"] is False
        assert result["action"] == "delete"
        assert "Task not found" in result["error"]
    
    def test_delete_task_empty_id(self, facade):
        """Test task deletion with empty task ID"""
        result = facade.delete_task("")
        
        assert result["success"] is False
        assert result["action"] == "delete"
        assert "Task ID is required" in result["error"]


class TestTaskApplicationFacadeCompleteTask:
    """Test suite for task completion"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_complete_task_success(self, facade):
        """Test successful task completion"""
        mock_result = {
            "success": True,
            "message": "Task completed successfully",
            "context": {"completion_data": "test"}
        }
        facade._complete_task_use_case.execute.return_value = mock_result
        
        result = facade.complete_task("task-123", "Task completed", "Tests passed")
        
        assert result["success"] is True
        assert result["action"] == "complete"
        assert result["task_id"] == "task-123"
        assert result["message"] == "Task completed successfully"
    
    def test_complete_task_not_found(self, facade):
        """Test task completion when task not found"""
        facade._complete_task_use_case.execute.side_effect = TaskNotFoundError("Task not found")
        
        result = facade.complete_task("nonexistent-task")
        
        assert result["success"] is False
        assert result["action"] == "complete"
        assert "Task not found" in result["error"]
    
    def test_complete_task_empty_id(self, facade):
        """Test task completion with empty task ID"""
        result = facade.complete_task("")
        
        assert result["success"] is False
        assert result["action"] == "complete"
        assert "Task ID is required" in result["error"]


class TestTaskApplicationFacadeListTasks:
    """Test suite for task listing"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.PerformanceConfig')
    def test_list_tasks_success(self, mock_perf_config, facade):
        """Test successful task listing"""
        mock_perf_config.is_performance_mode.return_value = False
        
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        mock_task.priority = "medium"
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task.to_dict.return_value = {
            "id": "task-123",
            "title": "Test Task",
            "status": "todo"
        }
        mock_task.dependencies = []
        
        mock_response = Mock()
        mock_response.tasks = [mock_task]
        mock_response.count = 1
        mock_response.filters_applied = {"status": "todo"}
        
        facade._list_tasks_use_case.execute.return_value = mock_response
        
        request = ListTasksRequest(status="todo", limit=10)
        result = facade.list_tasks(request)
        
        assert result["success"] is True
        assert result["action"] == "list"
        assert len(result["tasks"]) == 1
        assert result["count"] == 1
    
    @patch('fastmcp.task_management.application.facades.task_application_facade.PerformanceConfig')
    @patch('fastmcp.task_management.application.facades.task_application_facade.os')
    def test_list_tasks_performance_mode_supabase(self, mock_os, mock_perf_config, facade):
        """Test task listing in performance mode with Supabase"""
        mock_perf_config.is_performance_mode.return_value = True
        mock_os.getenv.return_value = "supabase"
        
        with patch('fastmcp.task_management.application.facades.task_application_facade.SupabaseOptimizedRepository') as mock_supabase_repo:
            mock_repo_instance = Mock()
            mock_repo_instance.list_tasks_minimal.return_value = [
                {"id": "task-123", "title": "Test Task", "status": "todo"}
            ]
            mock_supabase_repo.return_value = mock_repo_instance
            
            request = ListTasksRequest(status="todo", limit=10)
            result = facade.list_tasks(request, minimal=True)
            
            assert result["success"] is True
            assert result["performance_mode"] is True
            assert len(result["tasks"]) == 1


class TestTaskApplicationFacadeSearchTasks:
    """Test suite for task searching"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_search_tasks_success(self, facade):
        """Test successful task search"""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.title = "Authentication Task"
        mock_task.to_dict.return_value = {
            "id": "task-123",
            "title": "Authentication Task"
        }
        
        mock_response = Mock()
        mock_response.tasks = [mock_task]
        mock_response.count = 1
        mock_response.query = "authentication"
        
        facade._search_tasks_use_case.execute.return_value = mock_response
        
        request = SearchTasksRequest(query="authentication", limit=10)
        result = facade.search_tasks(request)
        
        assert result["success"] is True
        assert result["action"] == "search"
        assert len(result["tasks"]) == 1
        assert result["query"] == "authentication"
    
    def test_search_tasks_empty_query(self, facade):
        """Test task search with empty query"""
        request = SearchTasksRequest(query="", limit=10)
        result = facade.search_tasks(request)
        
        assert result["success"] is False
        assert result["action"] == "search"
        assert "Search query is required" in result["error"]


class TestTaskApplicationFacadeGetNextTask:
    """Test suite for next task retrieval"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    @pytest.mark.asyncio
    @patch('fastmcp.task_management.application.facades.task_application_facade.get_current_user_id')
    @patch('fastmcp.task_management.application.facades.task_application_facade.AuthConfig')
    async def test_get_next_task_success(self, mock_auth_config, mock_get_user_id, facade):
        """Test successful next task retrieval"""
        # Mock authentication
        mock_get_user_id.return_value = "test-user-123"
        mock_auth_config.is_default_user_allowed.return_value = False
        
        mock_response = Mock()
        mock_response.has_next = True
        mock_response.next_item = {"id": "task-123", "title": "Next Task"}
        mock_response.context = {"project": "test"}
        mock_response.context_info = {"branch": "main"}
        mock_response.message = "Next task found"
        
        facade._do_next_use_case.execute = AsyncMock(return_value=mock_response)
        
        result = await facade.get_next_task(
            include_context=True,
            user_id="user-123",
            project_id="project-123",
            git_branch_id="branch-123"
        )
        
        assert result["success"] is True
        assert result["action"] == "next"
        assert result["task"]["has_next"] is True
    
    @pytest.mark.asyncio
    async def test_get_next_task_no_tasks(self, facade):
        """Test next task retrieval when no tasks available"""
        facade._do_next_use_case.execute = AsyncMock(return_value=None)
        
        result = await facade.get_next_task()
        
        assert result["success"] is False
        assert result["action"] == "next"
        assert "No tasks found" in result["message"]


class TestTaskApplicationFacadeDependencyManagement:
    """Test suite for dependency management"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_add_dependency_success(self, facade, mock_task_repository, mock_task_entity):
        """Test successful dependency addition"""
        # Mock finding both tasks
        dependency_task = Mock()
        dependency_task.id = "dependency-123"
        
        mock_task_repository.find_by_id.side_effect = [mock_task_entity, dependency_task]
        
        result = facade.add_dependency("task-123", "dependency-123")
        
        assert result["success"] is True
        assert "added to task" in result["message"]
        mock_task_entity.add_dependency.assert_called_once()
        mock_task_repository.save.assert_called_once()
    
    def test_add_dependency_task_not_found(self, facade, mock_task_repository):
        """Test dependency addition when main task not found"""
        mock_task_repository.find_by_id.return_value = None
        
        result = facade.add_dependency("nonexistent-task", "dependency-123")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_add_dependency_empty_task_id(self, facade):
        """Test dependency addition with empty task ID (backward compatibility)"""
        result = facade.add_dependency("", "dependency-123")
        
        assert result["success"] is True
        assert "No-op" in result["message"]
    
    def test_remove_dependency_success(self, facade, mock_task_repository, mock_task_entity):
        """Test successful dependency removal"""
        mock_task_repository.find_by_id.return_value = mock_task_entity
        
        result = facade.remove_dependency("task-123", "dependency-123")
        
        assert result["success"] is True
        assert "removed from task" in result["message"]
        mock_task_entity.remove_dependency.assert_called_once()
        mock_task_repository.save.assert_called_once()
    
    def test_remove_dependency_task_not_found(self, facade, mock_task_repository):
        """Test dependency removal when task not found"""
        mock_task_repository.find_by_id.return_value = None
        
        result = facade.remove_dependency("nonexistent-task", "dependency-123")
        
        assert result["success"] is False
        assert "not found" in result["error"]
    
    def test_remove_dependency_empty_id(self, facade):
        """Test dependency removal with empty IDs"""
        result = facade.remove_dependency("", "dependency-123")
        
        assert result["success"] is False
        assert "Task ID cannot be empty" in result["error"]
        
        result = facade.remove_dependency("task-123", "")
        
        assert result["success"] is False
        assert "Dependency ID cannot be empty" in result["error"]


class TestTaskApplicationFacadeContextDerivation:
    """Test suite for context derivation functionality"""
    
    @pytest.fixture
    def facade(self, mock_task_repository, mock_git_branch_repository):
        """Create facade with git branch repository"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextSyncService'):
                        facade = TaskApplicationFacade(
                            task_repository=mock_task_repository,
                            git_branch_repository=mock_git_branch_repository
                        )
                        return facade
    
    @pytest.mark.asyncio
    async def test_derive_context_from_git_branch_id_success(self, facade, mock_git_branch_repository):
        """Test successful context derivation from git branch ID"""
        mock_branch = Mock()
        mock_branch.id = "branch-123"
        mock_branch.project_id = "project-456"
        mock_branch.name = "feature-branch"
        
        mock_git_branch_repository.find_all.return_value = [mock_branch]
        
        result = await facade._derive_context_from_git_branch_id("branch-123")
        
        assert result["project_id"] == "project-456"
        assert result["git_branch_name"] == "feature-branch"
    
    @pytest.mark.asyncio
    async def test_derive_context_from_git_branch_id_not_found(self, facade, mock_git_branch_repository):
        """Test context derivation when git branch not found"""
        mock_git_branch_repository.find_all.return_value = []
        
        with patch('fastmcp.task_management.application.facades.task_application_facade.ProjectManagementService') as mock_project_service:
            mock_service_instance = Mock()
            mock_service_instance.get_git_branch_by_id.return_value = {"success": False}
            mock_project_service.return_value = mock_service_instance
            
            result = await facade._derive_context_from_git_branch_id("nonexistent-branch")
            
            assert result["project_id"] is None
            assert result["git_branch_name"] is None
    
    @pytest.mark.asyncio
    async def test_derive_context_no_git_repository(self, mock_task_repository):
        """Test context derivation when no git repository available"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    
                    result = await facade._derive_context_from_git_branch_id("branch-123")
                    
                    assert result["project_id"] is None
                    assert result["git_branch_name"] is None


class TestTaskApplicationFacadeUtilityMethods:
    """Test suite for utility methods"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_await_if_coroutine_with_coroutine(self, facade):
        """Test _await_if_coroutine with actual coroutine"""
        async def sample_coroutine():
            return "test_result"
        
        result = facade._await_if_coroutine(sample_coroutine())
        assert result == "test_result"
    
    def test_await_if_coroutine_with_regular_value(self, facade):
        """Test _await_if_coroutine with regular value"""
        result = facade._await_if_coroutine("regular_value")
        assert result == "regular_value"
    
    def test_count_tasks(self, facade):
        """Test count_tasks utility method"""
        mock_response = Mock()
        mock_response.count = 5
        facade._list_tasks_use_case.execute.return_value = mock_response
        
        filters = {"status": "todo", "priority": "high"}
        result = facade.count_tasks(filters)
        
        assert result["success"] is True
        assert result["count"] == 5
    
    def test_list_tasks_summary(self, facade):
        """Test list_tasks_summary utility method"""
        mock_task = Mock()
        mock_task.id = "task-123"
        mock_task.title = "Test Task"
        mock_task.status = "todo"
        mock_task.priority = "medium"
        mock_task.created_at = datetime.now()
        mock_task.updated_at = datetime.now()
        mock_task.subtasks = []
        mock_task.assignees = ["user-1"]
        mock_task.dependencies = []
        
        mock_response = Mock()
        mock_response.tasks = [mock_task]
        mock_response.count = 1
        facade._list_tasks_use_case.execute.return_value = mock_response
        
        filters = {"status": "todo"}
        result = facade.list_tasks_summary(filters, offset=0, limit=10)
        
        assert result["success"] is True
        assert len(result["tasks"]) == 1
        assert result["count"] == 1
    
    def test_list_subtasks_summary(self, facade, mock_subtask_repository):
        """Test list_subtasks_summary utility method"""
        facade._subtask_repository = mock_subtask_repository
        
        mock_subtask = Mock()
        mock_subtask.id = "subtask-123"
        mock_subtask.title = "Test Subtask"
        mock_subtask.status = "todo"
        mock_subtask.priority = "medium"
        mock_subtask.progress_percentage = 50
        mock_subtask.assignees = ["user-1"]
        
        mock_subtask_repository.find_by_parent_task_id.return_value = [mock_subtask]
        
        result = facade.list_subtasks_summary("task-123")
        
        assert result["success"] is True
        assert len(result["subtasks"]) == 1
        assert result["subtasks"][0]["id"] == "subtask-123"
    
    def test_list_subtasks_summary_no_repository(self, facade):
        """Test list_subtasks_summary when no subtask repository available"""
        facade._subtask_repository = None
        
        result = facade.list_subtasks_summary("task-123")
        
        assert result["success"] is False
        assert "not configured" in result["error"]


class TestTaskApplicationFacadeValidation:
    """Test suite for validation methods"""
    
    @pytest.fixture
    def facade(self, mock_task_repository):
        """Create minimal facade for testing"""
        with patch('fastmcp.task_management.application.facades.task_application_facade.UnifiedContextFacadeFactory'):
            with patch('fastmcp.task_management.application.facades.task_application_facade.TaskContextRepository'):
                with patch('fastmcp.task_management.application.facades.task_application_facade.get_db_config'):
                    facade = TaskApplicationFacade(task_repository=mock_task_repository)
                    return facade
    
    def test_validate_create_task_request_success(self, facade):
        """Test successful create task request validation"""
        request = CreateTaskRequest(
            title="Valid Task",
            description="Valid description",
            git_branch_id="branch-123"
        )
        
        # Should not raise any exception
        facade._validate_create_task_request(request)
    
    def test_validate_create_task_request_empty_title(self, facade):
        """Test create task request validation with empty title"""
        request = CreateTaskRequest(
            title="",
            description="Valid description",
            git_branch_id="branch-123"
        )
        
        with pytest.raises(ValueError, match="title is required"):
            facade._validate_create_task_request(request)
    
    def test_validate_create_task_request_title_too_long(self, facade):
        """Test create task request validation with title too long"""
        request = CreateTaskRequest(
            title="x" * 201,
            description="Valid description",
            git_branch_id="branch-123"
        )
        
        with pytest.raises(ValueError, match="cannot exceed 200 characters"):
            facade._validate_create_task_request(request)
    
    def test_validate_update_task_request_success(self, facade):
        """Test successful update task request validation"""
        request = UpdateTaskRequest(
            task_id="task-123",
            title="Updated Task",
            description="Updated description"
        )
        
        # Should not raise any exception
        facade._validate_update_task_request("task-123", request)
    
    def test_validate_update_task_request_empty_task_id(self, facade):
        """Test update task request validation with empty task ID"""
        request = UpdateTaskRequest(title="Updated Task")
        
        with pytest.raises(ValueError, match="Task ID is required"):
            facade._validate_update_task_request("", request)
    
    def test_validate_update_task_request_empty_title(self, facade):
        """Test update task request validation with empty title"""
        request = UpdateTaskRequest(
            task_id="task-123",
            title=""
        )
        
        with pytest.raises(ValueError, match="cannot be empty"):
            facade._validate_update_task_request("task-123", request)