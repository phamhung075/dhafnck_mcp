"""
Tests for User-Scoped Task Routes with Authentication
Updated to include new subtask summaries endpoint
"""

import pytest
import json
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from fastapi import HTTPException, status, Request
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from fastmcp.auth.domain.entities.user import User, UserStatus, UserRole
from fastmcp.server.routes.user_scoped_task_routes import (
    router,
    UserScopedRepositoryFactory,
    create_task,
    list_tasks,
    get_task,
    update_task,
    delete_task,
    complete_task,
    get_user_task_stats,
    get_subtask_summaries
)
from fastmcp.task_management.application.dtos.task.create_task_request import CreateTaskRequest
from fastmcp.task_management.application.dtos.task.update_task_request import UpdateTaskRequest
from fastmcp.task_management.application.dtos.task.list_tasks_request import ListTasksRequest


class TestUserScopedRepositoryFactory:
    """Test the UserScopedRepositoryFactory"""
    
    def test_create_task_repository(self):
        """Test creating a user-scoped task repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        # Mock the repository and its with_user method
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepository') as MockTaskRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockTaskRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_task_repository(mock_session, user_id)
            
            MockTaskRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance
    
    def test_create_project_repository(self):
        """Test creating a user-scoped project repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.ProjectRepository') as MockProjectRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockProjectRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_project_repository(mock_session, user_id)
            
            MockProjectRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance
    
    def test_create_agent_repository(self):
        """Test creating a user-scoped agent repository"""
        mock_session = Mock(spec=Session)
        user_id = "user-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.AgentRepository') as MockAgentRepo:
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockAgentRepo.return_value = mock_repo_instance
            
            repo = UserScopedRepositoryFactory.create_agent_repository(mock_session, user_id)
            
            MockAgentRepo.assert_called_once_with(mock_session)
            mock_repo_instance.with_user.assert_called_once_with(user_id)
            assert repo == mock_repo_instance


class TestTaskRoutes:
    """Test the user-scoped task route endpoints"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="user-123",
            email="test@example.com",
            username="testuser",
            full_name="Test User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.fixture
    def mock_task(self):
        """Create a mock task"""
        task = Mock()
        task.id = "task-123"
        task.title = "Test Task"
        task.status = "todo"
        task.priority = "high"
        task.user_id = "user-123"
        return task
    
    @pytest.mark.asyncio
    async def test_create_task_success(self, mock_user, mock_db_session):
        """Test successful task creation"""
        request = CreateTaskRequest(
            title="New Task",
            description="Task description",
            status="todo",
            priority="high"
        )
        
        mock_task = Mock()
        mock_task.id = "task-456"
        mock_task.title = request.title
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.create_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await create_task(request, mock_user, mock_db_session)
            
            # Verify
            MockFactory.create_task_repository.assert_called_once_with(mock_db_session, mock_user.id)
            MockFacade.assert_called_once()
            mock_facade.create_task.assert_called_once_with(request)
            
            assert result["success"] is True
            assert result["task"] == mock_task
            assert f"user {mock_user.email}" in result["message"]
    
    @pytest.mark.asyncio
    async def test_create_task_failure(self, mock_user, mock_db_session):
        """Test task creation failure"""
        request = CreateTaskRequest(title="New Task")
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            MockFactory.create_task_repository.side_effect = Exception("Database error")
            
            with pytest.raises(HTTPException) as exc_info:
                await create_task(request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to create task" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_list_tasks_success(self, mock_user, mock_db_session):
        """Test successful task listing"""
        mock_tasks = [
            Mock(id="1", title="Task 1", status="todo"),
            Mock(id="2", title="Task 2", status="done")
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            # Return facade result that matches the expected structure from the route
            mock_facade.list_tasks.return_value = {"success": True, "tasks": mock_tasks}
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                task_status="todo",
                priority="high",
                limit=10,
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify
            assert result["success"] is True
            assert result["tasks"] == mock_tasks
            assert result["count"] == 2
            assert result["user"] == mock_user.email
    
    @pytest.mark.asyncio
    async def test_get_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task retrieval"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await get_task(task_id, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            assert result["success"] is True
            assert result["task"] == mock_task
    
    @pytest.mark.asyncio
    async def test_get_task_not_found(self, mock_user, mock_db_session):
        """Test task not found scenario"""
        task_id = "nonexistent-task"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Call the function
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_update_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task update"""
        task_id = "task-123"
        request = UpdateTaskRequest(
            title="Updated Task",
            status="in_progress"
        )
        
        updated_task = Mock()
        updated_task.id = task_id
        updated_task.title = request.title
        updated_task.status = request.status
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            mock_facade.update_task.return_value = updated_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await update_task(task_id, request, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            mock_facade.update_task.assert_called_once_with(task_id, request)
            assert result["success"] is True
            assert result["task"] == updated_task
            assert "Task updated successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_update_task_not_found(self, mock_user, mock_db_session):
        """Test updating non-existent task"""
        task_id = "nonexistent-task"
        request = UpdateTaskRequest(title="Updated")
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Call the function
            with pytest.raises(HTTPException) as exc_info:
                await update_task(task_id, request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_delete_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task deletion"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await delete_task(task_id, mock_user, mock_db_session)
            
            # Verify
            mock_facade.get_task.assert_called_once_with(task_id)
            mock_facade.delete_task.assert_called_once_with(task_id)
            assert result["success"] is True
            assert "Task deleted successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_complete_task_success(self, mock_user, mock_db_session, mock_task):
        """Test successful task completion"""
        task_id = "task-123"
        completion_summary = "Task completed successfully"
        testing_notes = "All tests passed"
        
        completed_task = Mock()
        completed_task.id = task_id
        completed_task.status = "done"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = mock_task
            mock_facade.complete_task.return_value = completed_task
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await complete_task(
                task_id,
                completion_summary,
                testing_notes,
                mock_user,
                mock_db_session
            )
            
            # Verify
            mock_facade.complete_task.assert_called_once_with(
                task_id=task_id,
                completion_summary=completion_summary,
                testing_notes=testing_notes
            )
            assert result["success"] is True
            assert result["task"] == completed_task
            assert "Task completed successfully" in result["message"]
    
    @pytest.mark.asyncio
    async def test_get_user_task_stats(self, mock_user, mock_db_session):
        """Test getting user task statistics"""
        mock_tasks = [
            Mock(status="done", priority="high"),
            Mock(status="done", priority="low"),
            Mock(status="in_progress", priority="high"),
            Mock(status="todo", priority="medium"),
            Mock(status="todo", priority="high")
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            # Setup mocks
            mock_task_repo = Mock()
            mock_task_repo.find_all.return_value = mock_tasks
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Call the function
            result = await get_user_task_stats(mock_user, mock_db_session)
            
            # Verify
            assert result["success"] is True
            stats = result["stats"]
            assert stats["total_tasks"] == 5
            assert stats["completed_tasks"] == 2
            assert stats["in_progress_tasks"] == 1
            assert stats["pending_tasks"] == 2
            assert stats["high_priority_tasks"] == 3
            assert stats["user"] == mock_user.email


class TestRouterIntegration:
    """Test router integration with FastAPI"""
    
    def test_router_prefix(self):
        """Test that router has correct prefix"""
        assert router.prefix == "/api/v2/tasks"
    
    def test_router_tags(self):
        """Test that router has correct tags"""
        assert "User-Scoped Tasks" in router.tags
    
    def test_router_endpoints(self):
        """Test that all expected endpoints are registered"""
        route_paths = [route.path for route in router.routes]
        
        # Check main CRUD endpoints
        assert "/" in route_paths  # POST and GET
        assert "/{task_id}" in route_paths  # GET, PUT, DELETE
        assert "/{task_id}/complete" in route_paths  # POST
        assert "/stats/summary" in route_paths  # GET
        assert "/{task_id}/subtasks/summaries" in route_paths  # POST
    
    def test_endpoint_methods(self):
        """Test that endpoints have correct HTTP methods"""
        method_paths = {}
        for route in router.routes:
            if hasattr(route, 'methods'):
                for method in route.methods:
                    if route.path not in method_paths:
                        method_paths[route.path] = []
                    method_paths[route.path].append(method)
        
        # Verify methods for each path
        assert "POST" in method_paths.get("/", [])
        assert "GET" in method_paths.get("/", [])
        assert "GET" in method_paths.get("/{task_id}", [])
        assert "PUT" in method_paths.get("/{task_id}", [])
        assert "DELETE" in method_paths.get("/{task_id}", [])
        assert "POST" in method_paths.get("/{task_id}/complete", [])
        assert "GET" in method_paths.get("/stats/summary", [])
        assert "POST" in method_paths.get("/{task_id}/subtasks/summaries", [])


class TestErrorHandling:
    """Test error handling in routes"""
    
    @pytest.mark.asyncio
    async def test_http_exception_passthrough(self, mock_user, mock_db_session):
        """Test that HTTPExceptions are passed through correctly"""
        task_id = "task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            mock_facade = Mock()
            # Simulate an HTTPException being raised
            mock_facade.get_task.side_effect = HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied"
            )
            MockFacade.return_value = mock_facade
            
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            # Verify the original exception is preserved
            assert exc_info.value.status_code == status.HTTP_403_FORBIDDEN
            assert exc_info.value.detail == "Access denied"
    
    @pytest.mark.asyncio
    async def test_unexpected_error_handling(self, mock_user, mock_db_session):
        """Test handling of unexpected errors"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            # Simulate unexpected error
            MockFactory.create_task_repository.side_effect = RuntimeError("Unexpected error")
            
            with pytest.raises(HTTPException) as exc_info:
                await list_tasks(current_user=mock_user, db=mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to list tasks" in str(exc_info.value.detail)


class TestAuthenticationIntegration:
    """Test authentication integration in routes."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="auth-user-456", 
            email="auth@example.com",
            username="authuser",
            full_name="Auth User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )

    @pytest.mark.asyncio
    async def test_supabase_auth_fallback_handling(self, mock_user):
        """Test that routes handle Supabase auth fallback correctly."""
        mock_db_session = Mock(spec=Session)
        
        # Mock the try/except import logic from the routes module
        with patch('fastmcp.server.routes.user_scoped_task_routes.get_current_user') as mock_get_current_user:
            mock_get_current_user.return_value = mock_user
            
            with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
                 patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
                
                MockFactory.create_task_repository.return_value = Mock()
                mock_facade = Mock()
                mock_facade.list_tasks.return_value = []
                MockFacade.return_value = mock_facade
                
                # Call the list_tasks function
                result = await list_tasks(current_user=mock_user, db=mock_db_session)
                
                # Verify user was used correctly
                MockFactory.create_task_repository.assert_called_once_with(mock_db_session, mock_user.id)
                assert result["user"] == mock_user.email

    @pytest.mark.asyncio
    async def test_user_id_passed_correctly_to_repositories(self, mock_user):
        """Test that user ID is correctly passed to all repository factories."""
        mock_db_session = Mock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            mock_task_repo = Mock()
            mock_project_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            MockFactory.create_project_repository.return_value = mock_project_repo
            
            with patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
                mock_facade = Mock()
                mock_task = Mock(id="task-456", title="Test Task")
                mock_facade.create_task.return_value = mock_task
                MockFacade.return_value = mock_facade
                
                request = CreateTaskRequest(
                    title="New Task",
                    description="Task description"
                )
                
                result = await create_task(request, mock_user, mock_db_session)
                
                # Verify user ID passed correctly
                MockFactory.create_task_repository.assert_called_with(mock_db_session, "auth-user-456")
                MockFactory.create_project_repository.assert_called_with(mock_db_session, "auth-user-456")
                
                assert result["success"] is True

    @pytest.mark.asyncio
    async def test_user_scoped_access_control(self, mock_user):
        """Test that user scoped access control works correctly."""
        mock_db_session = Mock(spec=Session)
        task_id = "restricted-task-123"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup user-scoped repository
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Setup facade to return None (task not found for this user)
            mock_facade = Mock()
            mock_facade.get_task.return_value = None
            MockFacade.return_value = mock_facade
            
            # Attempt to access task should fail with 404
            with pytest.raises(HTTPException) as exc_info:
                await get_task(task_id, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
            assert "Task not found" in str(exc_info.value.detail)
            
            # Verify user-scoped repository was used
            MockFactory.create_task_repository.assert_called_with(mock_db_session, mock_user.id)

    @pytest.mark.asyncio 
    async def test_audit_logging_with_user_context(self, mock_user):
        """Test that audit logging includes proper user context."""
        mock_db_session = Mock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_task = Mock(id="logged-task-789", title="Logged Task")
            mock_facade.create_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            request = CreateTaskRequest(title="Logged Task", description="For audit testing")
            
            await create_task(request, mock_user, mock_db_session)
            
            # Verify audit log contains user information
            mock_logger.info.assert_called_with(f"User {mock_user.email} creating task: {request.title}")

    @pytest.mark.asyncio
    async def test_user_stats_calculation_scoped_correctly(self, mock_user):
        """Test that user statistics are calculated only for the user's tasks."""
        mock_db_session = Mock(spec=Session)
        
        # Create mock tasks with different statuses for the user
        mock_user_tasks = [
            Mock(status="done", priority="high"),       # completed, high priority
            Mock(status="done", priority="medium"),     # completed, medium priority  
            Mock(status="in_progress", priority="high"), # in progress, high priority
            Mock(status="todo", priority="low"),        # pending, low priority
            Mock(status="todo", priority="high"),       # pending, high priority
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory:
            mock_task_repo = Mock()
            mock_task_repo.find_all.return_value = mock_user_tasks
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            result = await get_user_task_stats(mock_user, mock_db_session)
            
            # Verify user-scoped repository was used
            MockFactory.create_task_repository.assert_called_with(mock_db_session, mock_user.id)
            
            # Verify statistics are calculated correctly
            stats = result["stats"]
            assert stats["total_tasks"] == 5
            assert stats["completed_tasks"] == 2       # 2 "done" tasks
            assert stats["in_progress_tasks"] == 1     # 1 "in_progress" task
            assert stats["pending_tasks"] == 2        # 2 "todo" tasks  
            assert stats["high_priority_tasks"] == 3  # 3 "high" priority tasks
            assert stats["user"] == mock_user.email


class TestEnhancedLogging:
    """Test suite for enhanced logging in user_scoped_task_routes"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="log-user-123",
            email="logging@example.com",
            username="loguser",
            full_name="Logging User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_list_tasks_debug_logging(self, mock_user, mock_db_session):
        """Test enhanced debug logging for task listing"""
        mock_tasks = [
            {"id": "task-1", "title": "Task 1", "status": "todo"},
            {"id": "task-2", "title": "Task 2", "status": "done"}
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.list_tasks.return_value = {"success": True, "tasks": mock_tasks}
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                task_status="todo",
                priority="high",
                limit=50,
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify debug logging calls
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            # Check that essential debug messages are present
            assert any("=" * 80 in call for call in debug_calls)
            assert any("🔍 TASK LISTING REQUEST" in call for call in debug_calls)
            assert any(f"📧 User: {mock_user.email} (ID: {mock_user.id})" in call for call in debug_calls)
            assert any("🎯 Filters: status=todo, priority=high, limit=50" in call for call in debug_calls)
            assert any("💾 Database session:" in call for call in debug_calls)
            assert any("🏭 Creating user-scoped task repository..." in call for call in debug_calls)
            assert any("✅ Task repository created:" in call for call in debug_calls)
            assert any("🏗️ Creating task application facade..." in call for call in debug_calls)
            assert any("✅ Facade created:" in call for call in debug_calls)
            assert any("📋 Building list request..." in call for call in debug_calls)
            assert any("✅ List request built:" in call for call in debug_calls)
            assert any("🔍 Fetching tasks from facade..." in call for call in debug_calls)
            assert any("✅ Facade result type:" in call for call in debug_calls)
            assert any("✅ Tasks extracted: 2 tasks found" in call for call in debug_calls)
            assert any("📝 Task details:" in call for call in debug_calls)
            assert any("✅ TASK LISTING COMPLETED - Returning 2 tasks" in call for call in debug_calls)
            
            # Verify final info log
            mock_logger.info.assert_called_with(f"User {mock_user.email} retrieved 2 tasks")
    
    @pytest.mark.asyncio
    async def test_list_tasks_error_logging(self, mock_user, mock_db_session):
        """Test enhanced error logging for task listing failures"""
        test_error = RuntimeError("Database connection failed")
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup to raise an error
            MockFactory.create_task_repository.side_effect = test_error
            
            # Call the function and expect an exception
            with pytest.raises(HTTPException):
                await list_tasks(
                    task_status="todo",
                    current_user=mock_user,
                    db=mock_db_session
                )
            
            # Verify error logging calls
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            
            # Check that essential error messages are present
            assert any("=" * 80 in call for call in error_calls)
            assert any(f"❌ ERROR in task listing for user {mock_user.id}" in call for call in error_calls)
            assert any(f"❌ User: {mock_user.email}" in call for call in error_calls)
            assert any("❌ Error type: RuntimeError" in call for call in error_calls)
            assert any("❌ Error message: Database connection failed" in call for call in error_calls)
            assert any("❌ Stack trace:" in call for call in error_calls)
    
    @pytest.mark.asyncio
    async def test_list_tasks_empty_result_logging(self, mock_user, mock_db_session):
        """Test logging when no tasks are found"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup mocks for empty result
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.list_tasks.return_value = {"success": True, "tasks": []}
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify empty result logging
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("📝 No tasks found for user" in call for call in debug_calls)
            
            # Verify info log for empty result
            mock_logger.info.assert_called_with(f"User {mock_user.email} retrieved 0 tasks")
            
            assert result["count"] == 0
            assert result["tasks"] == []
    
    @pytest.mark.asyncio
    async def test_list_tasks_large_result_logging(self, mock_user, mock_db_session):
        """Test logging behavior with large task lists"""
        # Create mock tasks - more than 5 to test truncated logging
        mock_tasks = [
            {"id": f"task-{i}", "title": f"Task {i}", "status": "todo"} 
            for i in range(10)
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            mock_facade.list_tasks.return_value = {"success": True, "tasks": mock_tasks}
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify truncated task logging
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            
            # Should log first 5 tasks
            for i in range(5):
                assert any(f"Task {i+1}: ID=task-{i}" in call for call in debug_calls)
            
            # Should indicate more tasks exist
            assert any("... and 5 more tasks" in call for call in debug_calls)
            
            assert result["count"] == 10
    
    @pytest.mark.asyncio
    async def test_list_tasks_malformed_facade_response_logging(self, mock_user, mock_db_session):
        """Test logging when facade returns unexpected structure"""
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup mocks
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            mock_facade = Mock()
            # Return unexpected structure
            mock_facade.list_tasks.return_value = "unexpected string response"
            MockFacade.return_value = mock_facade
            
            # Call the function
            result = await list_tasks(
                current_user=mock_user,
                db=mock_db_session
            )
            
            # Verify error handling for malformed response
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("❌ Unexpected facade result structure:" in call for call in error_calls)
            
            # Should still return valid response structure
            assert result["success"] is True
            assert result["tasks"] == []
            assert result["count"] == 0


class TestORMTaskRepositoryIntegration:
    """Test integration with ORMTaskRepository"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="orm-user-789",
            email="orm@example.com",
            username="ormuser",
            full_name="ORM User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )
    
    @pytest.mark.asyncio
    async def test_orm_task_repository_usage(self, mock_user):
        """Test that routes correctly use ORMTaskRepository"""
        mock_db_session = Mock(spec=Session)
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepository') as MockTaskRepo, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Verify TaskRepository is imported as ORMTaskRepository
            mock_repo_instance = Mock()
            mock_repo_instance.with_user.return_value = mock_repo_instance
            MockTaskRepo.return_value = mock_repo_instance
            
            # Create repository through factory
            repo = UserScopedRepositoryFactory.create_task_repository(mock_db_session, mock_user.id)
            
            # Verify ORMTaskRepository usage
            MockTaskRepo.assert_called_once_with(mock_db_session)
            mock_repo_instance.with_user.assert_called_once_with(mock_user.id)
            assert repo == mock_repo_instance
    
    @pytest.mark.asyncio
    async def test_facade_with_orm_repository(self, mock_user):
        """Test TaskApplicationFacade works correctly with ORMTaskRepository"""
        mock_db_session = Mock(spec=Session)
        request = CreateTaskRequest(
            title="ORM Task",
            description="Testing ORM integration"
        )
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade:
            
            # Setup ORM repository mock
            mock_orm_repo = Mock()
            mock_orm_repo.__class__.__name__ = "ORMTaskRepository"
            MockFactory.create_task_repository.return_value = mock_orm_repo
            MockFactory.create_project_repository.return_value = Mock()
            
            # Setup facade
            mock_facade = Mock()
            mock_task = Mock(id="orm-task-123", title="ORM Task")
            mock_facade.create_task.return_value = mock_task
            MockFacade.return_value = mock_facade
            
            # Call create_task
            result = await create_task(request, mock_user, mock_db_session)
            
            # Verify facade was created with ORM repository
            MockFacade.assert_called_once()
            call_kwargs = MockFacade.call_args[1]
            assert call_kwargs['task_repository'] == mock_orm_repo
            
            assert result["success"] is True
            assert result["task"] == mock_task

    @pytest.mark.asyncio
    async def test_task_completion_with_user_context(self, mock_user):
        """Test task completion includes proper user context and validation."""
        mock_db_session = Mock(spec=Session)
        task_id = "completion-task-123"
        completion_summary = "Task completed with full context"
        testing_notes = "All tests passed for user scope"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.UserScopedRepositoryFactory') as MockFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskApplicationFacade') as MockFacade, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            mock_task_repo = Mock()
            MockFactory.create_task_repository.return_value = mock_task_repo
            
            # Mock existing task for user
            existing_task = Mock(id=task_id, user_id=mock_user.id)
            completed_task = Mock(id=task_id, status="done", user_id=mock_user.id)
            
            mock_facade = Mock()
            mock_facade.get_task.return_value = existing_task
            mock_facade.complete_task.return_value = completed_task
            MockFacade.return_value = mock_facade
            
            result = await complete_task(
                task_id, completion_summary, testing_notes, mock_user, mock_db_session
            )
            
            # Verify user-scoped validation occurred
            mock_facade.get_task.assert_called_once_with(task_id)
            
            # Verify completion with proper parameters
            mock_facade.complete_task.assert_called_once_with(
                task_id=task_id,
                completion_summary=completion_summary, 
                testing_notes=testing_notes
            )
            
            # Verify audit logging
            mock_logger.info.assert_called_with(f"User {mock_user.email} completed task {task_id}")
            
            assert result["success"] is True
            assert result["task"] == completed_task


class TestSubtaskSummariesEndpoint:
    """Test the new subtask summaries endpoint"""
    
    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user"""
        return User(
            id="subtask-user-123",
            email="subtask@example.com",
            username="subtaskuser",
            full_name="Subtask User",
            password_hash="",
            status=UserStatus.ACTIVE,
            roles=[UserRole.USER],
            email_verified=True
        )
    
    @pytest.fixture
    def mock_request(self):
        """Create a mock request object"""
        request = Mock(spec=Request)
        request.body = AsyncMock()
        return request
    
    @pytest.fixture
    def mock_db_session(self):
        """Create a mock database session"""
        return Mock(spec=Session)
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_success(self, mock_user, mock_request, mock_db_session):
        """Test successful subtask summaries retrieval"""
        task_id = "parent-task-123"
        request_body = {"include_counts": True}
        mock_request.body.return_value = json.dumps(request_body).encode()
        
        mock_subtasks_data = [
            {
                "id": "sub-1",
                "title": "Subtask 1",
                "status": "done",
                "priority": "high",
                "assignees": ["user-1"],
                "progress_percentage": 100
            },
            {
                "id": "sub-2",
                "title": "Subtask 2",
                "status": "in_progress",
                "priority": "medium",
                "assignees": [],
                "progress_percentage": 50
            },
            {
                "id": "sub-3",
                "title": "Subtask 3",
                "status": "todo",
                "priority": "low",
                "assignees": ["user-2"],
                "progress_percentage": 0
            }
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory') as MockTaskRepoFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory') as MockSubtaskRepoFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory:
            
            # Setup factories
            MockTaskRepoFactory.return_value = Mock()
            MockSubtaskRepoFactory.return_value = Mock()
            
            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": mock_subtasks_data
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function
            result = await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            # Verify facade was called correctly
            mock_task_facade.list_subtasks_summary.assert_called_once_with(
                parent_task_id=task_id,
                include_counts=True
            )
            
            # Verify response structure
            assert result["parent_task_id"] == task_id
            assert result["total_count"] == 3
            assert len(result["subtasks"]) == 3
            
            # Verify first subtask summary
            first_subtask = result["subtasks"][0]
            assert first_subtask["id"] == "sub-1"
            assert first_subtask["title"] == "Subtask 1"
            assert first_subtask["status"] == "done"
            assert first_subtask["priority"] == "high"
            assert first_subtask["assignees_count"] == 1
            assert first_subtask["progress_percentage"] == 100
            
            # Verify progress summary
            progress = result["progress_summary"]
            assert progress["total"] == 3
            assert progress["completed"] == 1
            assert progress["in_progress"] == 1
            assert progress["todo"] == 1
            assert progress["blocked"] == 0
            assert progress["completion_percentage"] == 33  # 1/3 * 100
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_empty_body(self, mock_user, mock_request, mock_db_session):
        """Test subtask summaries with empty request body"""
        task_id = "parent-task-456"
        mock_request.body.return_value = b""
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory:
            
            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": []
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function
            result = await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            # Verify include_counts defaults to True
            mock_task_facade.list_subtasks_summary.assert_called_once_with(
                parent_task_id=task_id,
                include_counts=True
            )
            
            # Verify empty response
            assert result["parent_task_id"] == task_id
            assert result["total_count"] == 0
            assert result["subtasks"] == []
            assert result["progress_summary"]["total"] == 0
            assert result["progress_summary"]["completion_percentage"] == 0
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_facade_error(self, mock_user, mock_request, mock_db_session):
        """Test subtask summaries when facade returns error"""
        task_id = "error-task-789"
        mock_request.body.return_value = json.dumps({"include_counts": False}).encode()
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory:
            
            # Setup task facade to return error
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": False,
                "error": "Failed to fetch subtasks"
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function and expect exception
            with pytest.raises(HTTPException) as exc_info:
                await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Failed to fetch subtasks" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_exception_handling(self, mock_user, mock_request, mock_db_session):
        """Test subtask summaries exception handling"""
        task_id = "exception-task-000"
        mock_request.body.return_value = json.dumps({"include_counts": True}).encode()
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory') as MockTaskRepoFactory:
            # Simulate exception
            MockTaskRepoFactory.side_effect = Exception("Database connection failed")
            
            with pytest.raises(HTTPException) as exc_info:
                await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            assert exc_info.value.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
            assert "Database connection failed" in str(exc_info.value.detail)
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_progress_calculation(self, mock_user, mock_request, mock_db_session):
        """Test correct progress calculation in subtask summaries"""
        task_id = "progress-task-111"
        mock_request.body.return_value = json.dumps({"include_counts": True}).encode()
        
        # Create subtasks with various statuses
        mock_subtasks_data = [
            {"id": "s1", "title": "Done 1", "status": "done", "priority": "high", "assignees": []},
            {"id": "s2", "title": "Done 2", "status": "done", "priority": "medium", "assignees": []},
            {"id": "s3", "title": "Done 3", "status": "done", "priority": "low", "assignees": []},
            {"id": "s4", "title": "In Progress", "status": "in_progress", "priority": "high", "assignees": []},
            {"id": "s5", "title": "Todo", "status": "todo", "priority": "medium", "assignees": []},
            {"id": "s6", "title": "Blocked", "status": "blocked", "priority": "high", "assignees": []}
        ]
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory:
            
            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": mock_subtasks_data
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function
            result = await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            # Verify progress summary calculations
            progress = result["progress_summary"]
            assert progress["total"] == 6
            assert progress["completed"] == 3  # 3 done tasks
            assert progress["in_progress"] == 1
            assert progress["todo"] == 1
            assert progress["blocked"] == 1
            assert progress["completion_percentage"] == 50  # 3/6 * 100
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_logging(self, mock_user, mock_request, mock_db_session):
        """Test logging in subtask summaries endpoint"""
        task_id = "log-task-222"
        mock_request.body.return_value = json.dumps({"include_counts": True}).encode()
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory, \
             patch('fastmcp.server.routes.user_scoped_task_routes.logger') as mock_logger:
            
            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": [{"id": "s1", "title": "Test", "status": "done", "priority": "high", "assignees": []}]
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function
            result = await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            # Verify logging
            mock_logger.info.assert_any_call(f"Loading subtask summaries for task {task_id} by user {mock_user.email}")
            mock_logger.info.assert_any_call(f"Returned 1 subtask summaries for task {task_id}")
    
    @pytest.mark.asyncio
    async def test_get_subtask_summaries_malformed_json(self, mock_user, mock_request, mock_db_session):
        """Test subtask summaries with malformed JSON in request body"""
        task_id = "malformed-task-333"
        mock_request.body.return_value = b"invalid json {"
        
        with patch('fastmcp.server.routes.user_scoped_task_routes.TaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.SubtaskRepositoryFactory'), \
             patch('fastmcp.server.routes.user_scoped_task_routes.TaskFacadeFactory') as MockTaskFacadeFactory:
            
            # Setup task facade
            mock_task_facade = Mock()
            mock_task_facade.list_subtasks_summary.return_value = {
                "success": True,
                "subtasks": []
            }
            
            mock_task_facade_factory = Mock()
            mock_task_facade_factory.create_task_facade.return_value = mock_task_facade
            MockTaskFacadeFactory.return_value = mock_task_facade_factory
            
            # Call the function - should handle malformed JSON gracefully
            result = await get_subtask_summaries(task_id, mock_request, mock_user, mock_db_session)
            
            # Should default to include_counts=True
            mock_task_facade.list_subtasks_summary.assert_called_once_with(
                parent_task_id=task_id,
                include_counts=True
            )
            
            assert result["parent_task_id"] == task_id